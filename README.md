# OpenAI Codex CLI Plugin

This package provides a `codex` subcommand for the OpenAI CLI, implementing the following commands:

- `openai codex health-check`: System health check (Slack, Docker connectivity).
- `openai codex test-components`: Component self-test (Slack listener, Executor).
- `openai codex plan`: Decompose a task into execution phases (generate plan JSON).
- `openai codex execute`: Execute a plan JSON and collect results.

## Installation

```bash
# (Optional) 仮想環境作成・有効化（プロジェクトごとに環境を分離）
# Debian/Ubuntu 系でエラーが出る場合:
#   sudo apt update && sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate

# pip, setuptools, wheel を最新化
pip install --upgrade pip setuptools wheel

# 本パッケージをインストール
pip install .

# 環境変数を設定（または .env に記述して source してください）
export OPENAI_API_KEY="your_openai_api_key"
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."
export PROJECT_PATH="/path/to/your/project"
```

## Usage

```bash
# Health check
codex health-check

# Component test
codex test-components

# Plan generation
codex plan --task-summary @task_summary.json --output @plan.json

# Plan execution
codex execute --plan @plan.json --output @results.json
```