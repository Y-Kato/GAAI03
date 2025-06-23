# openai-codex-cli

AIコマンドエージェントをローカル CLI から操作するための Python プラグインです。タスク分解 → コマンド実行 → フェーズ管理の一連ワークフローを自動化し、
Slack や Docker の環境チェックもサポートします。

## 主な特徴

- **health-check** : Slack トークンおよび Docker 接続のヘルスチェック
- **test-components** : SlackListener／Executor のセルフテスト
- **plan** : GPT-4 を使いタスクサマリを実行フェーズに分解し、計画 JSON を生成
- **execute** : 生成されたプラン JSON に従いシェルコマンドを順次実行して結果を保存

## インストール

### PyPI からインストール
```bash
pip install openai-codex-cli
```

### ソースからインストール
```bash
git clone https://github.com/your-org/openai-codex-cli.git
cd openai-codex-cli
pip install .
```

## 環境変数設定

動作に必要な環境変数を設定してください（または `.env` ファイルに記載して読み込む）。

| 変数             | 説明                             |
|------------------|----------------------------------|
| OPENAI_API_KEY   | OpenAI API キー                  |
| SLACK_BOT_TOKEN  | Slack Bot トークン (`xoxb-…`)    |
| SLACK_APP_TOKEN  | Slack App トークン (`xapp-…`)    |
| PROJECT_PATH     | プロジェクトルート（prompts 配置先）|

```bash
export OPENAI_API_KEY="your_openai_api_key"
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."
export PROJECT_PATH="/path/to/your/project"
```

## 使い方

```bash
codex health-check                                         # システムヘルスチェック
codex test-components                                      # コンポーネントテスト
codex plan --task-summary @task_summary.json --output @plan.json   # プラン生成
codex execute --plan @plan.json --output @results.json             # プラン実行
```

## 詳細ドキュメント

各種設定やセキュリティ設計、API 仕様などの詳細は `docs/` 配下のドキュメントをご覧ください。

- docs/API-specification.md
- docs/slack-settings.md
- docs/security-design.md
- docs/task-execution-flow-design.md
- docs/future-improvements.md

## ライセンス

MIT