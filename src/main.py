import argparse
import traceback
import json
import time
import queue
import threading
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from websockets.sync.server import serve

from modules.js_client import MineflayerJsClient
from modules.websocketconnecter import WebsocketConnecter
from modules.belief import StandaloneWorldObservationRuntime, build_world_config_from_first_blocks_data
from modules.llm import Opneai_LLM, Ollama_LLM
from modules.utils import make_file_logger, load_config, load_primitives, read_files

__VERSION__ = "20260427_0658"

OFFSET = [0,0,0]
DISALLOWED_EXPRESSIONS = [
      {"expression":"bot.on(", "message":"Do not wait for other players' action. Do not use `bot.on` or `Promise`."},
      {"expression":"Promise(", "message":"Do not wait for other players' action. Do not use `bot.on` or `Promise`."},
      {"expression":"findBlock(", "message":"Do not use `findBlock()` or `findBlocks()`. Use specific coordinates instead to specify the goal."},
      {"expression":"findBlocks(", "message":"Do not use `findBlock()` or `findBlocks()`. Use specific coordinates instead to specify the goal."},
      {"expression":"while (", "message":"Do not write infinite loops."},
      {"expression":"bot.players[", "message":"Do not use bot.players[playername]`"},
      {"expression":"bot.nearestEntity(", "message":"Do not use bot.nearestEntity()"},
      {"expression":"offset(", "message": "Do not use `position.offset()`. Use ..... instead."}
    ]

###############################################################
@dataclass(frozen=True)
class WebSocketConfig:
    host: str
    port: int

@dataclass(frozen=True)
class MinecraftServerConfig:
    host: str
    port: int
    server_id: str

@dataclass(frozen=True)
class MineflayerServerConfig:
    port: int
    setup: bool

@dataclass(frozen=True)
class MinecraftConfig:
    offset: list[int]
    env_box: list[list[int]]
    can_dig_when_move: bool
    move_timeout_sec: int
    stuck_check_interval_sec: int
    stuck_offset_range: int

@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model_name: str
    temperature: float
    request_timeout: int
    max_trial: int

###############################################################

###############################################################
def build_mineflayer_variables(agent_name, offset, env_box):
    return {
        "offsetVec3": json.dumps({"__Vec3__": offset}),
        "agentInfo": json.dumps({agent_name:{"mcName":agent_name}}),
        "envBox": json.dumps([
                {"__Vec3__": env_box[0]},
                {"__Vec3__": env_box[1]}])
        }

def build_easy_llm_variables(env_box):
    return {
        "type": "first_access",
        "min": {"x": env_box[0][0], "y": env_box[0][1], "z": env_box[0][2]},
        "max": {"x": env_box[1][0], "y": env_box[1][1], "z": env_box[1][2]},
    }

def build_agent_dataclasses(config):
    easy_llm = WebSocketConfig(
        host=config["easy_llm"]["host"],
        port=config["easy_llm"]["port"],
    )
    minecraft_server = MinecraftServerConfig(
        host=config["minecraft_server"]["host"],
        port=config["minecraft_server"]["port"],
        server_id=config["minecraft_server"]["server_id"],
    )
    mineflayer_server = MineflayerServerConfig(
        port=config["mineflayer_server"]["port"],
        setup=config["mineflayer_server"]["setup"],
    )
    minecraft = MinecraftConfig(
        offset=config["minecraft"]["offset"],
        env_box=[
            config["minecraft"]["env_box"]["min"],
            config["minecraft"]["env_box"]["max"],
        ],
        can_dig_when_move=config["minecraft"]["can_dig_when_move"],
        move_timeout_sec=config["minecraft"]["move_timeout_sec"],
        stuck_check_interval_sec=config["minecraft"]["stuck_check_interval_sec"],
        stuck_offset_range=config["minecraft"]["stuck_offset_range"],
    )
    llm = LLMConfig(
        api_key=config["openai"]["api_key"],
        model_name=config["openai"]["model_name"],
        temperature=config["openai"]["temperature"],
        request_timeout=config["openai"]["request_timeout"],
        max_trial=config["openai"]["max_trial"],
    )
    return easy_llm, minecraft_server, mineflayer_server, minecraft, llm
###############################################################

###############################################################
class Agent:
    def __init__(
        self,
        *,
        log_dir: str,
        agent_name: str,
        agent_id: str,
        prompt_path: str,
        minecraft_server_cfg: MinecraftServerConfig,
        mineflayer_server_cfg: MineflayerServerConfig,
        easy_llm_cfg: WebSocketConfig,
        minecraft_cfg: MinecraftConfig,
        llm_cfg: LLMConfig
    ):
        self.log_dir = log_dir
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.minecraft_server_cfg = minecraft_server_cfg
        self.mineflayer_server_cfg = mineflayer_server_cfg
        self.easy_llm_cfg = easy_llm_cfg
        self.minecraft_cfg = minecraft_cfg
        self.llm_cfg = llm_cfg
        self.agent_logger = make_file_logger(self.agent_name, f"{self.log_dir}/{self.agent_name}.log")
        self.primitives = load_primitives()
        self.prompts = read_files(prompt_path)
        self.obs_audio_q = queue.Queue()
        self.for_belief_update_q = queue.Queue()

        self.belief = None
        self.world_config = None

        self.llm = Opneai_LLM(self.log_dir, self.llm_cfg.api_key, self.llm_cfg.model_name, self.llm_cfg.temperature, self.llm_cfg.request_timeout, self.llm_cfg.max_trial)

        self.MineflayerJsClient_logger = make_file_logger("MineflayerJsClient", f"{self.log_dir}/MineflayerJsClient.log")
        self.js_client = MineflayerJsClient(port=self.mineflayer_server_cfg.port, logger=self.MineflayerJsClient_logger)
        self.mineflayer_variables = build_mineflayer_variables(self.agent_name, self.minecraft_cfg.offset, self.minecraft_cfg.env_box)

        self.easy_llm_ws = WebsocketConnecter("easy_llm", self.easy_llm_cfg.host, self.easy_llm_cfg.port, True)
        self.easy_llm_variables = build_easy_llm_variables(self.minecraft_cfg.env_box)

    ########################### action methods from mod ############################
    def add_avatar(self):
        self.agent_logger.info(f"mf_server_setup:{self.mineflayer_server_cfg.setup}")
        self.js_client.connect()
        if self.mineflayer_server_cfg.setup:
            self.js_client.setup(
                can_dig_when_move=self.minecraft_cfg.can_dig_when_move,
                move_timeout_sec=self.minecraft_cfg.move_timeout_sec,
                stuck_check_interval_sec=self.minecraft_cfg.stuck_check_interval_sec,
                stuck_offset_range=self.minecraft_cfg.stuck_offset_range,
                sync=True,
            )
        self.js_client.join(server_id=self.minecraft_server_cfg.server_id, mc_name=self.agent_name, mc_port=self.minecraft_server_cfg.port, mc_host=self.minecraft_server_cfg.host)
        self.js_client.update_agent_variables(server_id=self.minecraft_server_cfg.server_id, mc_name=self.agent_name, variables=self.mineflayer_variables)
    
    def exec_js(self, js):
        self.js_client.exec_js(server_id=self.minecraft_server_cfg.server_id, mc_name=self.agent_name, code=js, primitives=self.primitives, sync=True, timeout=180)
    ##################################################################################

    #################################### LLM ######################################
    def create_prompt(self, human_prompt_type, system_prompt_type):
        human_base_prompt, system_prompt = self.prompts["human"][human_prompt_type], self.prompts["system"][system_prompt_type]
        #--- BeliefNest依存　情報の取得 + プロンプトへの入力 ---# # BeliefNest
        human_variables = {"self_name":self.agent_name}
        try:
            loader = self.belief.create_current_observation_loader()
            human_prompt = self.belief.load_from_template(loader, human_base_prompt, variables=human_variables, extra_filters=[], allow_filter_override=True)
        except Exception as e:
            self.agent_logger.critical(f"agent.py L171 エラー発生:{e}")
            error_msg = traceback.format_exc()
            self.agent_logger.critical("例外が発生しました:")
            self.agent_logger.critical(error_msg)
        #----------------------------------------------------#
        self.agent_logger.info(f"----------------------------------------------")
        self.agent_logger.info(f"human_prompt:{human_prompt}")
        self.agent_logger.info(f"----------------------------------------------")
        return human_prompt, system_prompt

    def execute_llm(self, format_prompts, validate_js=True):
        code, time_str = self.llm.request_llm(prompts=format_prompts, disallowed_expressions=DISALLOWED_EXPRESSIONS, javascript_check=validate_js)
        self.agent_logger.info(f"-----------------------------------")
        self.agent_logger.info(f"code:{code}")
        self.agent_logger.info(f"time_str:{time_str}")
        self.agent_logger.info(f"-----------------------------------")
        return code
    
    def generate_action_js(self):
        human_prompt, system_prompt = self.create_prompt(human_prompt_type="generate_action", system_prompt_type="primitive")
        format_prompts = self.llm.format_prompts_for_llm([("system", system_prompt), ("user", human_prompt)])
        javascript = self.execute_llm(format_prompts, validate_js=True)
        return javascript
    ##################################################################################

    ################################# belief ####################################
    def update_belief_loop(self, input_q):
        while True:
            try:
                obs = input_q.get(timeout=0.1)
            except queue.Empty:
                continue
            if any(item.get("type") == "block_snapshot" for item in obs.get("items", [])):
                self.world_config = build_world_config_from_first_blocks_data(obs, player_names=["sally", "obs7"])
                self.belief = StandaloneWorldObservationRuntime.from_world_config(self.world_config, offset=[0,0,0])
                continue
            if self.belief != None:
                self.belief.add_raw_observation(obs)
    ###########################################################################################

    ################################# OBS from mod ####################################
    def get_mc_obs(self, input_q, output1_q):
        self.agent_logger.info("start get_mc_obs")
        while True:
            try:
                obs = input_q.get(timeout=0.1)
            except queue.Empty:
                continue

            if isinstance(obs, str):
                obs = json.loads(obs)
            output1_q.put(obs)
    ###########################################################################################

    def main(self):
        self.agent_logger.info("Action generation will start when you press Enter.")
        while True:
            try:
                line = input("[enter]:")
            except EOFError:
                try:
                    self.easy_llm_ws.websocket.close()
                except Exception:
                    pass
                return

            action_js = self.generate_action_js()
            self.exec_js(action_js)

    def run(self):
        self.add_avatar()

        easy_llm_ws_thread = threading.Thread(target=self.easy_llm_ws.run, daemon=True)
        easy_llm_ws_thread.start()
        time.sleep(0.5)
        self.easy_llm_ws.send(self.easy_llm_variables)

        get_mc_obs_thread = threading.Thread(target=self.get_mc_obs, args=(self.easy_llm_ws.queue, self.for_belief_update_q), daemon=True)
        get_mc_obs_thread.start()
        update_belief_loop_thread = threading.Thread(target=self.update_belief_loop, args=(self.for_belief_update_q,), daemon=True)
        update_belief_loop_thread.start()

        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    config = load_config(args.config)
    easy_llm_cfg, minecraft_server_cfg, mineflayer_server_cfg, minecraft_cfg, llm_cfg = build_agent_dataclasses(config)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    agent = Agent(
        log_dir=f'{config["agent"]["logs_dir"]}/{timestamp}',
        agent_name=config["agent"]["agent_name"],
        agent_id=config["agent"]["agent_id"],
        prompt_path=config["agent"]["prompts"],
        minecraft_server_cfg=minecraft_server_cfg,
        mineflayer_server_cfg=mineflayer_server_cfg,
        easy_llm_cfg=easy_llm_cfg,
        minecraft_cfg=minecraft_cfg,
        llm_cfg=llm_cfg
    )
    agent.run()
    agent.main_thread.join()

if __name__ == "__main__":
    main()