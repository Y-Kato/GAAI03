# openai-codex-cli

OpenAI Codex向けのCLIプラグインです。タスクをAI（GPT-4）で分解し、シェルコマンドを自動実行・管理する一連のワークフローを提供します。

## Features

- **health-check**     : SlackトークンとDocker接続のヘルスチェック
- **test-components**  : SlackListener／Executorのセルフテスト
- **plan**             : タスクサマリを実行フェーズに分解し計画JSONを生成
- **execute**          : 計画JSONをもとにコマンド実行し結果を収集

## Installation

### PyPI から
```bash
pip install openai-codex-cli
```

### ソースから
```bash
git clone https://github.com/Y-Kato/GAAI03.git
cd GAAI03
pip install .
```

## Environment Variables

| Name              | Description                                      |
|-------------------|--------------------------------------------------|
| OPENAI_API_KEY    | OpenAI APIキー                                   |
| SLACK_BOT_TOKEN   | Slack Bot OAuthトークン (`xoxb-…`)               |
| SLACK_APP_TOKEN   | Slack App-levelトークン (Socket Mode, `xapp-…`) |
| PROJECT_PATH      | プロジェクトルートパス（prompts配置先）          |

```bash
export OPENAI_API_KEY="sk-…"
export SLACK_BOT_TOKEN="xoxb-…"
export SLACK_APP_TOKEN="xapp-…"
export PROJECT_PATH="/path/to/project"
```

## Usage

### ローカルCLI
```bash
codex health-check
codex test-components
codex plan --task-summary @task_summary.json --output @plan.json
codex execute --plan @plan.json --output @results.json
```

### Slack連携（詳細）

Slack App作成〜OAuth/イベント購読〜Socket Mode設定〜動作テストなど、具体手順は以下を参照してください。
- docs/slack-settings.md

## Further Documentation

- docs/API-specification.md
- docs/task-execution-flow-design.md
- docs/security-design.md
- docs/future-improvements.md

## License

MIT