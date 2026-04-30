<!-- markdownlint-disable MD033 -->
<p style="font-size:18px">
  | EN | <a href="./README.jp.md">JP</a> |
</p>

# Easy LLM

Easy LLM is a platform for developing AI agents that can play together with you in Minecraft.
AI agents that use Easy LLM refer to in-game information and use an LLM to perform actions and chat with players.

## What You Can Do with This Repository

Implement an AI agent that can chat and play with you in Minecraft.

- Send in-game actions, states, and observation information to the outside via WebSocket
- Implement an AI agent that uses an LLM to perform actions and chat with players while taking in-game information into account

## Repository Structure

- [minecraft_server_on_docker](./minecraft_server_on_docker/)
  : Source code for building a Minecraft server on docker
- [mineflayer_server_on_docker](./mineflayer_server_on_docker/)
  : Source code for building a Mineflayer server on docker
- [src](./src/)
  : Python sample code for implementing an AI agent

---

# Flow up to AI Agent Implementation

This section explains how to implement an AI agent in Minecraft using mods and Python code.

## 1. Preparation

Please follow the steps below to prepare in advance. Operation has been verified on Windows 11.

### 1.1 Installing Python Libraries

Create a Python 3.11 or later environment and install the libraries.

The following is an example of setting up a Python environment using [Anaconda](https://www.anaconda.com/download).
If you use Anaconda, you can build the Python environment by executing the following commands in PowerShell opened from the root folder of this repository.

```powershell
conda create -n easy_llm python=3.11
conda activate easy_llm
cd src
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1.2 Installing Docker

If you are using Windows, download and run the installer from [Docker Docs](https://docs.docker.com/desktop/setup/install/windows-install/). Docker must be version 20.10 or later.

### 1.3 Installing Minecraft

Install [Minecraft Launcher](https://www.minecraft.net/) and make sure you can play Minecraft: Java Edition (version 1.21). It will be used as the client. A Java Edition license is required.

### 1.4 Obtaining an OpenAI API key

- Issue an OpenAI API key from [here](https://platform.openai.com/api-keys). You need to create an account. Also, confirm from [here](https://platform.openai.com/settings/organization/billing/overview) that there is a balance of at least 0.1 dollars.

The LLM is used to generate the AI agent’s actions, and the key is used for that purpose.

### 1.5 Downloading MOD Files

Download the following MOD files.

- Fabric API: [fabric-api-0.102.0+1.21.jar](https://modrinth.com/mod/fabric-api)
- Easy LLM MOD: [easy-llm-fabric-1.0.0+mc1.21.jar][def]

For Fabric API, select the version and download it as shown below.

<p align="center">
  <img src="./image/fabric_api_download.png" alt="Voice Bridge GUI-sample" width="450">
</p>

## 2. Placing the MOD Files

### 2.1 Installing the MODs on the Minecraft server

Place the two downloaded files in the `data/mods` folder of the Minecraft server you will use.

If you use the Minecraft server included in this project, place them in [./minecraft_server_on_docker/_mods/1.21](./minecraft_server_on_docker/_mods/1.21), and the MODs will be loaded when the Minecraft server starts.
After placing the MOD files, delete [./minecraft_server_on_docker/_mods/1.21/mods_file_here.txt](./minecraft_server_on_docker/_mods/1.21/mods_file_here.txt).

### 2.2 Installing the MODs on the Minecraft client

In this version, there is no need to add MOD files to the Minecraft client.

## 3. Starting Each Server

Start each server in a separate terminal. Open two terminals from the root folder of this repository.

- Minecraft server (Terminal A)
- Mineflayer server (Terminal B)

### 3.1 Starting and Preparing the Minecraft Server

- Starting Docker Desktop
  Start Docker Desktop from the Start menu or similar.

- Starting the server

  In Terminal A, execute the following. Startup takes some time only the first time.
  ```
  conda activate easy_llm
  cd minecraft_server_on_docker
  python launch_mc_server_cli.py
  ```

  After execution, enter the world settings in the terminal as shown below, and the Minecraft server will start.<br>By changing the port number, you can start multiple Minecraft servers.

  ```
  Enter mode name [flat] > flat
  Enter Minecraft port [25565] > 25565
  Enter Minecraft version [1.21] > 1.21
  ```

  When `Done` is output to the terminal as shown below, the server startup is complete.

  ```
  [00:39:28] [Server thread/INFO]: Done (0.465s)! For help, type "help"
  ```

- Joining the world

  Start the Minecraft client and join the world from "Multiplayer". If the world is not displayed, specify a server address such as `localhost:25565` in "Add Server".

- Granting permissions
  After joining the world, execute in Terminal A where the logs are being output.

  ```
  op xxx
  ```
  Here, `xxx` is your Minecraft user name. This grants op permissions to your user, allowing you to use various commands. When using the same server again, you do not need to execute the above command.

** Note **
<br>If you have previously opened a server on Docker with the same port number, confirm that the docker container is stopped, and then perform [3.1 Starting and Preparing the Minecraft Server](#31-starting-and-preparing-the-minecraft-server).

### 3.2 Starting the Mineflayer Server

In Terminal B, execute the following to start the server. Startup takes some time only the first time.
```
conda activate easy_llm
cd mineflayer_server_on_docker
python mineflayer_cli.py
```

After execution, enter the world settings in the terminal as shown below, and the Mineflayer server will start.

```
Enter Minecraft version [1.21] > 1.21
```

When output like the following appears in the terminal, the server startup is complete.

```
Starting container: beliefnestjs
Server started on port 3000
```

## 4. WebSocket Connection Settings

### 4.1 Setup on Minecraft

Set the destination address in order to send observation information on Minecraft to Websocket.
Execute the following command in the text terminal on Minecraft.
<br>However, when executing commands in the text terminal on Minecraft, op permissions are required. Refer to [here](#31-starting-and-preparing-the-minecraft-server) for how to configure op permissions.

```
/obsWs add ws://host.docker.internal:7892
```

To check the destination addresses currently configured in Minecraft, execute the following command.
By default, `ws://host.docker.internal:7891` is opened when the Minecraft server starts.

```
/obsWs list
```

To delete a destination address currently configured in Minecraft, execute the following command.

```
/obsWs remove ws://host.docker.internal:7892
```

### 4.2 Setup on Python
item at src/sally_cfg.yml L11 match the [destination address configured in 4.1 Setup on Minecraft] (if you are running the Minecraft server on Docker, set Minecraft to `ws://host.docker.internal:****` and set src/sally_cfg.yml to L12 `host: 0.0.0.0`, L13 `port: ****`. * can be any value)
- Confirm that a valid API key is entered in L35 `api_key`

If you want to have conversations in Japanese, make the following changes.

- Change L7 `generate_action: ./prompts/coding_llm_human_prompt_template.txt` to `generate_action: ./prompts/coding_llm_human_prompt_template_jp.txt`
- Change L9 `primitive: ./prompts/jp/coding_llm_system_prompt_template.txt` to `primitive: ./prompts/jp/coding_llm_system_prompt_template_jp.txt`

## 5. Running the Sample Code

To run the sample code, open one terminal. It must be different from the terminals used to start each server.

- main program (Terminal C)

In Terminal C, execute the following from the root folder of this repository to start the program.
  ```
  conda activate easy_llm
  cd src
  python main.py --config sally_cfg.yml
  ```

If `Action generation will start when you press Enter.` is displayed in Terminal C, startup is complete.

After that, at any time, if you enter the Enter key once in Terminal C, the agent will generate an action.

## 6. How to Add a Second and Subsequent Agents

By creating a new agent_cfg.yml and running the main program, you can create additional AI agents.
<br>A sample file, anne_cfg.yml, is provided.

### 6.1 Creating agent_cfg.yml

1. Create a copy of sally_cfg.yml
  <br>Create a copy of sally_cfg.yml and give it any name. Here, it will be called agent_cfg.yml.
2. Change the following items in agent_cfg.yml
  <br>Open agent_cfg.yml in a text editor or similar, and change the following items.

- L2 agent_name: "Any name"
- L13 port: "Any four-digit number"
- L22 setup: false
- L35 api_key: Valid API key

note:
<br>make sure agent_name is a name that does not exist as an in-game player. Due to Minecraft specifications, players with the same name cannot exist.
<br>Also, set the port number to a number that is different from the other AI agents.

If you are using anne_cfg.yml, change the following items in anne_cfg.yml.

- L35 api_key: Valid API key

### 6.2 Setup on Minecraft

Execute the following command in the text terminal on Minecraft.
<br>For ****, write the L13 port: "Any four-digit number" configured in [6.1 Creating agent_cfg.yml](#61-creating-agent_cfgyml).
If you use anne_cfg.yml, write 7892.

```
/obsWs add ws://host.docker.internal:****
```

### 6.3 Adding an Agent

Open one new terminal. It must be different from the terminals you have used so far.

- main program (Terminal D)

In Terminal D, execute the following from the root folder of this repository to start the program.
  ```
  conda activate easy_llm
  cd src
  python main.py --config agent_cfg.yml
  ```

If you are using anne_cfg.yml, run the following commands from the root folder of this repository in Terminal D.
  ```
  conda activate easy_llm
  cd src
  python main.py --config anne_cfg.yml
  ```

If `Action generation will start when you press Enter.` is displayed in Terminal D, startup is complete.

After that, at any time, if you enter the Enter key once in Terminal D, the agent will generate an action.

[def]: https://legacy.curseforge.com/minecraft/mc-mods/easy-llm/files

<!-- markdownlint-enable MD033 -->
