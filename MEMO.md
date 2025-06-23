## 追加したファイル・ディレクトリ構成

    .
    ├── .gitignore
    ├── README.md
    ├── setup.cfg
    ├── setup.py
    └── codex_cli
        ├── __init__.py
        ├── commands.py
        ├── planner.py
        ├── executor_plugin.py
        └── slack_plugin.py

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 主な実装概要

#### 1. パッケージ設定（setup.cfg / setup.py）

    [metadata]
    name = openai-codex-cli
    version = 0.1.0
    description = OpenAI CLI Codex plugin
    long_description = file: README.md
    long_description_content_type = text/markdown
    license = MIT

    [options]
    packages = find:
    install_requires =
        openai>=0.27.0
        slack-bolt>=1.0.0
        docker>=5.0.0
        click>=8.0.0
    python_requires = >=3.7

    [options.entry_points]
    openai.cli.commands =
        codex=codex_cli.commands:codex

[setup.cfg】

    #!/usr/bin/env python3
    from setuptools import setup

    if __name__ == "__main__":
        setup()

【F:setup.py】

#### 2. CLI コマンド群（codex_cli/commands.py）

openai codex 以下にサブコマンドを追加しています。

    * `health-check` … Slack トークン／App Token と Docker 接続の簡易チェック
    * `test-components` … `SlackListener`／`Executor` のインスタンス化テスト
    * `plan` … `--task-summary` で与えたタスク JSON を GPT-4（デフォルト）にプロンプトして計画 JSON を生成
    * `execute` … `--plan` で与えた計画 JSON の `domain_phases[*].exec` コマンドを順次実行し、結果を JSON に保存

    @click.group()
    def codex():
        """Codex CLI プラグイン"""

    @codex.command('health-check')
    def health_check():
        """システムヘルスチェック (Slack, Docker)"""
        …

    @codex.command('test-components')
    def test_components():
        """コンポーネントテスト (SlackListener, Executor)"""
        …

    @codex.command('plan')
    @click.option('--task-summary', 'summary_path', …)
    @click.option('--output', 'output_path', …)
    def plan(summary_path, output_path):
        """タスクをフェーズに分解し計画書を作成"""
        …

    @codex.command('execute')
    @click.option('--plan', 'plan_path', …)
    @click.option('--output', 'output_path', …)
    def execute(plan_path, output_path):
        """計画書に従いコマンドを実行し結果を保存"""
        …

【F:codex_cli/commands.py](/home/kato/docker/GAAI03/setup.cfg】

    #!/usr/bin/env python3
    from setuptools import setup

    if __name__ == "__main__":
        setup()

【F:setup.py】

#### 2. CLI コマンド群（codex_cli/commands.py）

openai codex 以下にサブコマンドを追加しています。

    * `health-check` … Slack トークン／App Token と Docker 接続の簡易チェック
    * `test-components` … `SlackListener`／`Executor` のインスタンス化テスト
    * `plan` … `--task-summary` で与えたタスク JSON を GPT-4（デフォルト）にプロンプトして計画 JSON を生成
    * `execute` … `--plan` で与えた計画 JSON の `domain_phases[*].exec` コマンドを順次実行し、結果を JSON に保存

    @click.group()
    def codex():
        """Codex CLI プラグイン"""

    @codex.command('health-check')
    def health_check():
        """システムヘルスチェック (Slack, Docker)"""
        …

    @codex.command('test-components')
    def test_components():
        """コンポーネントテスト (SlackListener, Executor)"""
        …

    @codex.command('plan')
    @click.option('--task-summary', 'summary_path', …)
    @click.option('--output', 'output_path', …)
    def plan(summary_path, output_path):
        """タスクをフェーズに分解し計画書を作成"""
        …

    @codex.command('execute')
    @click.option('--plan', 'plan_path', …)
    @click.option('--output', 'output_path', …)
    def execute(plan_path, output_path):
        """計画書に従いコマンドを実行し結果を保存"""
        …

【F:codex_cli/commands.py)

#### 3. Planner プラグイン（codex_cli/planner.py）

prompts/planner.md を読み込み、OpenAI Python SDK の ChatCompletion API を呼び出して計画 JSON（domain_phases）を取得します。

    def get_planner_prompt(task_summary):
        project_root = os.environ.get('PROJECT_PATH', os.getcwd())
        prompt_path = os.path.join(project_root, 'prompts', 'planner.md')
        …

    def plan_task(task_summary):
        messages = get_planner_prompt(task_summary)
        response = openai.ChatCompletion.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
            messages=messages,
            temperature=float(os.environ.get('OPENAI_TEMPERATURE', '0.3')),
            max_tokens=int(os.environ.get('OPENAI_MAX_TOKENS', '4000'))
        )
        return json.loads(response.choices[0].message['content'])

codex_cli/planner.py

#### 4. Executor プラグイン（codex_cli/executor_plugin.py）

計画 JSON の各フェーズに書かれたシェルコマンド（exec）を subprocess.run(..., shell=True) で実行し、標準出力・標準エラーを収集します。

    class Executor:
        def __init__(self, working_dir=None):
            self.working_dir = working_dir or os.environ.get('PROJECT_PATH', os.getcwd())

        def execute_plan(self, plan):
            results = []
            for phase in plan.get('domain_phases', []):
                cmd = phase.get('exec')
                if not cmd:
                    continue
                proc = subprocess.run(cmd, shell=True, cwd=self.working_dir,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                results.append({...})
            return results

codex_cli/executor_plugin.py

#### 5. Slack リスナー（codex_cli/slack_plugin.py）

Slack Bolt(SDK) の Socket Mode で app_mention イベントを受信し、将来的に CLI コマンド（plan/execute など）をトリガーできる基盤を用意しています。

    class SlackListener:
        def __init__(self):
            slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
            slack_app_token = os.environ.get('SLACK_APP_TOKEN')
            …
            self.app = App(token=slack_bot_token)
            self.handler = SocketModeHandler(self.app, slack_app_token)
            self._register_events()

        def _register_events(self):
            @self.app.event('app_mention')
            def handle_mention(event, say):
                user = event.get('user')
                text = event.get('text')
                say(f'<@{user}> received: {text}')

        def start(self):
            self.handler.start()

codex_cli/slack_plugin.py

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## インストール＆動作確認手順

    # リポジトリルートで
    pip install .

    # 必須環境変数を設定
    export OPENAI_API_KEY="your_openai_api_key"
    export SLACK_BOT_TOKEN="xoxb-..."
    export SLACK_APP_TOKEN="xapp-..."
    export PROJECT_PATH="/path/to/your/project"   # prompts/ や実行対象プロジェクトのルート

    # 動作確認
    openai codex health-check
    openai codex test-components

    # タスク計画→実行の例
    openai codex plan --task-summary @task_summary.json --output @plan.json
    openai codex execute --plan @plan.json --output @results.json

README に仮想環境（venv）を使ったディレクトリ単位の環境分離手順を追記しました。これでグローバルな Python 環境を汚さずに、本プラグインをプロジェクトごとにインストールできます。

    # (Optional) プロジェクトルートで仮想環境を作成・有効化
    python3 -m venv .venv
    source .venv/bin/activate

    # pip, setuptools, wheel を最新化
    pip install --upgrade pip setuptools wheel

    # パッケージをインストール
    pip install .

    # 環境変数を設定（または .env に書いて source ）
    export OPENAI_API_KEY="your_openai_api_key"
    export SLACK_BOT_TOKEN="xoxb-..."
    export SLACK_APP_TOKEN="xapp-..."
    export PROJECT_PATH="/path/to/your/project"

README.md

これで openai codex … 系のコマンドが、その仮想環境内だけにインストールされ、システム全体の Python ライブラリには影響を与えません。

― 完了した変更のハイライト ―

    * README.md に仮想環境（venv）手順を追加 [README.md](/home/kato/docker/GAAI03/README.md)

ご確認ください！