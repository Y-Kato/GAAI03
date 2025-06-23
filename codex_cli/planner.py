import os
import json

import openai


def get_planner_prompt(task_summary):
    """Planner AI に渡すプロンプトリストを返す"""
    project_root = os.environ.get('PROJECT_PATH', os.getcwd())
    prompt_path = os.path.join(project_root, 'prompts', 'planner.md')
    with open(prompt_path, encoding='utf-8') as f:
        system_prompt = f.read()
    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': (
            'タスク情報:\n'
            f"{json.dumps(task_summary, ensure_ascii=False, indent=2)}"
            '\n\n上記タスクを実行可能なフェーズに分解し、JSON形式で計画書を作成してください。'
        )}
    ]


def plan_task(task_summary):
    """タスクを AI に計画させ、JSON 計画書を返す"""
    messages = get_planner_prompt(task_summary)
    response = openai.ChatCompletion.create(
        model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
        messages=messages,
        temperature=float(os.environ.get('OPENAI_TEMPERATURE', '0.3')),
        max_tokens=int(os.environ.get('OPENAI_MAX_TOKENS', '4000'))
    )
    content = response.choices[0].message.get('content')
    return json.loads(content)