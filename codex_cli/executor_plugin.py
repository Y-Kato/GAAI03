import os
import subprocess


class Executor:
    """AI 生成コマンドを安全に実行し、結果を返却"""

    def __init__(self, working_dir=None):
        self.working_dir = working_dir or os.environ.get('PROJECT_PATH', os.getcwd())

    def execute_plan(self, plan):
        """計画書の各フェーズを実行し、結果リストを返す"""
        results = []
        for phase in plan.get('domain_phases', []):
            cmd = phase.get('exec')
            if not cmd:
                continue
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            results.append({
                'no': phase.get('no'),
                'exec': cmd,
                'stdout': proc.stdout,
                'stderr': proc.stderr,
                'returncode': proc.returncode,
            })
        return results