import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


class SlackListener:
    """Slack イベントを受信し、codex CLI をトリガーするリスナ"""

    def __init__(self):
        slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
        slack_app_token = os.environ.get('SLACK_APP_TOKEN')
        if not slack_bot_token or not slack_app_token:
            raise ValueError('SLACK_BOT_TOKEN/SLACK_APP_TOKEN が設定されていません')
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
        """Socket Mode で Slack イベント受信を開始"""
        self.handler.start()