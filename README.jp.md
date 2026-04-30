<!-- markdownlint-disable MD033 -->
<p style="font-size:18px">
  | <a href="./README.md">EN</a> | JP |
</p>

# Easy LLM

Easy LLM は、Minecraft 内で一緒に遊ぶことができる AI エージェント を開発するためのプラットフォームです。
Easy LLM を用いた AIエージェント はゲーム内の情報を参照し、LLM を用いて行動や発言を行います。

## このリポジトリでできること

Minecraft の世界に話しながら一緒に遊べる AIエージェント を実装する

- ゲーム内の行動・状態・観測情報を WebSocket で外部へ送る
- LLM を用いたゲーム内の情報を考慮して行動・発言を行う AIエージェント を実装する

## リポジトリ構成

- [minecraft_server_on_docker](./minecraft_server_on_docker/)
  : Minecraft server を docker 上に構築するためのソースコード
- [mineflayer_server_on_docker](./mineflayer_server_on_docker/)
  : Mineflayer server を docker 上に構築するためのソースコード
- [src](./src/)
  : AIエージェント を実装する Python サンプルコード

---

# AIエージェント 実装までの流れ

MOD と pythonプログラムを用いて、Minecraft 内に AIエージェント を実装する手順を示します。

## 1. 事前準備

以下の手順に従って事前準備を行ってください。動作確認は Windows 11 上で行っています。

### 1.1 Python ライブラリのインストール

python 3.11以上の環境を作成し、ライブラリのインストールを行ってください。

[Anaconda](https://www.anaconda.com/download) を用いた python 環境構築例を示します。
Anaconda を使用する場合、本リポジトリフォルダを開いた PowerShell で以下のコマンドを実行すると、pythonの環境が構築されます。

```powershell
conda create -n easy_llm python=3.11
conda activate easy_llm
cd src
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1.2 Docker のインストール

Windows を使用している場合は、[Docker Docs](https://docs.docker.com/desktop/setup/install/windows-install/) からインストーラをダウンロードして実行してください。Dockerはバージョン20.10以降である必要があります。

### 1.3 Minecraft のインストール

[Minecraft Launcher](https://www.minecraft.net/)をインストールし、Minecraft: Java Edition（バージョン1.21）をプレイできるようにしてください。クライアントとして使用します。Java Edition のライセンスが必要です。

### 1.4 Opneai API key の取得

- [こちら](https://platform.openai.com/api-keys)からOpenAI API キーを発行してください。アカウントの作成が必要です。なお、[こちら](https://platform.openai.com/settings/organization/billing/overview)から残高が0.1ドル以上存在することを確認してください。

AI エージェントの行動生成に LLM を活用しており、そこに使用します。

### 1.5 MOD ファイルのダウンロード

以下の MOD ファイルをダウンロードして下さい。

- Fabric API: [fabric-api-0.102.0+1.21.jar](https://modrinth.com/mod/fabric-api)
- Easy LLM MOD: [easy-llm-fabric-1.0.0+mc1.21.jar][def]

Fabric API は、以下のようにバージョンを選択してダウンロードを行ってください。

<p align="center">
  <img src="./image/fabric_api_download.png" alt="Voice Bridge GUI-sample" width="450">
</p>

## 2. MOD ファイルの配置

### 2.1 Minecraft server への MOD 導入

使用する Minecraft server の `data/mods` フォルダに、ダウンロードした２つのファイルを配置してください。

本プロジェクトに含まれる Minecraft server を使用する場合は、[./minecraft_server_on_docker/_mods/1.21](./minecraft_server_on_docker/_mods/1.21)に配置すると、Minecraft server 起動時に MOD が読み込まれます。
MOD ファイル配置後に、[./minecraft_server_on_docker/_mods/1.21/mods_file_here.txt](./minecraft_server_on_docker/_mods/1.21/mods_file_here.txt) を削除してください。

### 2.2 Minecraft client への MOD 導入

本バージョンでは、Minecraft client へ MOD ファイルを追加する必要はありません。

## 3. 各サーバーの起動

2つの異なるターミナルで、各サーバーを起動します。そのため、2つのターミナルを起動して下さい。
2つのターミナルは、本リポジトリフォルダを開いておいてください。

- Minecraft サーバ（ターミナルA）
- Mineflayer サーバ（ターミナルB）

### 3.1 Minecraft サーバの起動と準備

- Docker Desktopの起動
  スタートメニューなどからDocker Desktopを起動してください。

- サーバの起動

  ターミナルAにおいて、以下を実行してください。初回のみ起動に時間がかかります。
  ```
  conda activate easy_llm
  cd minecraft_server_on_docker
  python launch_mc_server_cli.py
  ```

  実行後は、ターミナルに対して、以下のようにワールドの設定を入力すると、Minecraft サーバが起動します。<br>port 番号を変更することで、複数のMinecraft サーバを起動できます。

  ```
  Enter mode name [flat] > flat
  Enter Minecraft port [25565] > 25565
  Enter Minecraft version [1.21] > 1.21
  ```

  以下のようにターミナルに `Done` が出力されると、サーバの起動が完了しています。

  ```
  [00:39:28] [Server thread/INFO]: Done (0.465s)! For help, type "help"
  ```

- ワールドへの参加

  Minecraft クライアントを起動し、「マルチプレイ」からワールドに参加してください。ワールドが表示されない場合は、「サーバーを追加」で `localhost:25565` のようなサーバアドレスを指定してください。

- 権限の付与

  ワールドに参加したら、ログが出力されているターミナルAで以下を実行してください。
  ```
  op xxx
  ```
  ただし`xxx`はあなたの Minecraft ユーザ名です。これによりあなたのユーザにop権限が与えられ、様々なコマンドを使用可能になります。同一サーバを再度使用する際には、上記のコマンド実行は不要です。

** 注意 **
<br>過去に Docker 上で、同様の port 番号でサーバーを開いていた場合は、docker コンテナが停止しているかを確認したうえで、[3.1 Minecraft サーバの起動と準備](#31-minecraft-サーバの起動と準備)を行ってください

### 3.2 Mineflayer サーバの起動

ターミナルBにおいて、以下を実行してサーバを起動してください。初回のみ起動に時間がかかります。
```
conda activate easy_llm
cd mineflayer_server_on_docker
python mineflayer_cli.py
```

実行後は、ターミナルに対して、以下のようにワールドの設定を入力すると、Mineflayer サーバが起動します。

```
Enter Minecraft version [1.21] > 1.21
```

以下のような出力がターミナルに出ると、サーバの起動が完了しています。

```
Starting container: beliefnestjs
Server started on port 3000
```

## 4. websocketの接続設定

### 4.1 Minecraft 上のセットアップ

Minecraft 上の観測情報を Websocket に送信するために、接続先アドレスを設定します。
Minecraft 上のテキストターミナルにおいて、以下のコマンドを実行してください。
<br>ただし、Minecraft 上のテキストターミナルでコマンドを実行する場合には、op権限が必要となります。op権限の設定方法は[こちら](#31-minecraft-サーバの起動と準備)を参照してください。

```
/obsWs add ws://host.docker.internal:7892
```

現在 Minecraft に設定されている接続先アドレスを確認する場合は、以下のコマンドを実行してください。
Default として、Minecraft サーバ起動時に `ws://host.docker.internal:7891` が開くようになっています。

```
/obsWs list
```

現在 Minecraft に設定されている接続先アドレスを削除する場合は、以下のコマンドを実行してください。

```
/obsWs remove ws://host.docker.internal:7892
```

### 4.2 python 上のセットアップ

`src/sally_cfg.yml`に、取得した Opneai API key を入力してください。

その後、`src/sally_cfg.yml` ファイルにおいて、以下の項目をチェックしてください。

- src/sally_cfg.yml L11 `easy_llm` の項目にある `host: port:` の二つの値と [4.1 Minecraft 上のセットアップ で設定した接続先アドレス] のが一致しているか（Docker 上でMinecraft サーバを立てている場合は、Minecraftでは `ws://host.docker.internal:****`, src/sally_cfg.yml では L12 `host: 0.0.0.0`, L13 `port: ****` と設定してください。* は任意）
- L35 `api_key` に有効な API キーが入っていることを確認する

日本語での会話を行いたい場合は、以下の変更を行ってください。

- L7 `generate_action: ./prompts/coding_llm_human_prompt_template.txt` を `generate_action: ./prompts/coding_llm_human_prompt_template_jp.txt`に変更
- L9 `primitive: ./prompts/jp/coding_llm_system_prompt_template.txt` を `primitive: ./prompts/jp/coding_llm_system_prompt_template_jp.txt`に変更

## 5. サンプルコードの実行

サンプルコードを実行するために、1つターミナルを開いてください。各サーバーの起動に使用したターミナルとは異なるものが必要となります。

- mainプログラム（ターミナルC）

ターミナルCにおいて、本リポジトリフォルダで以下を実行してプログラムを起動してください。
  ```
  conda activate easy_llm
  cd src
  python main.py --config sally_cfg.yml
  ```

ターミナルC上に、`ction generation will start when you press Enter.`と表示されれば起動完了です。

以降は任意のタイミングで、ターミナルCに対して Enter key を一度入力すると、エージェントが行動を生成します。

## 6. 二人目以降のエージェントの追加方法

新たに agent_cfg.yml を作成し、mainプログラムを実行することで、AIエージェントを追加で作成することができます。
<br>サンプルとして、anne_cfg.yml を用意しています。

### 6.1 agent_cfg.yml の作成

1. sally_cfg.yml のコピーを作成
  <br>sally_cfg.yml のコピーを作成し、任意の名前を付けてください。ここでは、agent_cfg.yml とします。
2. agent_cfg.yml の以下の項目を変更する
  <br>agent_cfg.yml をテキストエディタ等で開き、以下の項目を変更します。

- L2 agent_name: "任意の名前"
- L13 port: "４桁の任意の数字"
- L22 setup: false
- L35 api_key: 有効な API キー

注意点として、agent_name は、ゲーム内のプレイヤーとして存在しない名前にしてください。Minecraft の仕様上、同じ名前のプレイヤーは存在できないようになっています。
<br>また、port 番号は、他の AIエージェントとは違う数字を設定してください

anne_cfg.yml を使用する場合は、以下の項目を変更してください。

- L35 api_key: 有効な API キー

### 6.2 Minecraft 上のセットアップ

Minecraft 上のテキストターミナルにおいて、以下のコマンドを実行してください。
<br>**** には、[6.1 agent_cfg.yml の作成](#61-agent_cfgyml-の作成)で設定した L13 port: "４桁の任意の数字" を記述して下さい。
anne_cfg.yml を使用する場合は、7892 を記述してください。

```
/obsWs add ws://host.docker.internal:****
```

### 6.3 エージェントの追加

新たに、1つターミナルを開いてください。これまで使用していたターミナルとは異なるものが必要となります。

- mainプログラム（ターミナルD）

ターミナルDにおいて、本リポジトリフォルダで以下を実行してプログラムを起動してください。
  ```
  conda activate easy_llm
  cd src
  python main.py --config agent_cfg.yml
  ```

anne_cfg.yml を使用する場合は、ターミナルDにおいて、本リポジトリフォルダで以下を実行してください。
  ```
  conda activate easy_llm
  cd src
  python main.py --config anne_cfg.yml
  ```

ターミナルD上に、`Action generation will start when you press Enter.`と表示されれば起動完了です。

以降は任意のタイミングで、ターミナルDに対して Enter key を一度入力すると、エージェントが行動を生成します。

[def]: https://legacy.curseforge.com/minecraft/mc-mods/easy-llm/files

<!-- markdownlint-enable MD033 -->