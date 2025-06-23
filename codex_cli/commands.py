import os
import sys
import json
import click

from .slack_plugin import SlackListener
from .executor_plugin import Executor
from .planner import plan_task

@click.group()
def codex():
    """Codex CLI プラグイン"""
    pass

@codex.command('health-check')
def health_check():
    """システムヘルスチェック (Slack, Docker)"""
    ok = True
    if os.getenv('SLACK_BOT_TOKEN') and os.getenv('SLACK_APP_TOKEN'):
        click.echo('Slack configuration: OK')
    else:
        click.echo('Slack configuration: NG', err=True)
        ok = False
    try:
        import docker

        client = docker.from_env()
        client.ping()
        click.echo('Docker connectivity: OK')
    except Exception as e:
        click.echo(f'Docker connectivity: NG ({e})', err=True)
        ok = False
    if not ok:
        sys.exit(1)

@codex.command('test-components')
def test_components():
    """コンポーネントテスト (SlackListener, Executor)"""
    try:
        SlackListener()
        click.echo('SlackListener: OK')
    except Exception as e:
        click.echo(f'SlackListener: ERROR ({e})', err=True)
    try:
        Executor()
        click.echo('Executor: OK')
    except Exception as e:
        click.echo(f'Executor: ERROR ({e})', err=True)

@codex.command('plan')
@click.option('--task-summary', 'summary_path', required=True,
              type=click.Path(exists=True), help='タスクサマリJSONファイル')
@click.option('--output', 'output_path', required=True,
              type=click.Path(), help='出力プランJSONファイル')
def plan(summary_path, output_path):
    """タスクをフェーズに分解し計画書を作成"""
    with open(summary_path, encoding='utf-8') as f:
        summary = json.load(f)
    plan = plan_task(summary)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    click.echo(f'Plan saved to {output_path}')

@codex.command('execute')
@click.option('--plan', 'plan_path', required=True,
              type=click.Path(exists=True), help='プランJSONファイル')
@click.option('--output', 'output_path', required=True,
              type=click.Path(), help='実行結果JSONファイル')
def execute(plan_path, output_path):
    """計画書に従いコマンドを実行し結果を保存"""
    with open(plan_path, encoding='utf-8') as f:
        plan = json.load(f)
    results = Executor().execute_plan(plan)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    click.echo(f'Results saved to {output_path}')