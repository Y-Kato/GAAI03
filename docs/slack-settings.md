# Slack連携設定ガイド（具体的手順）

このガイドでは、AIコマンドエージェントとSlackを連携させるための具体的な手順を説明します。

## 📋 事前準備

- Slackワークスペースの管理者権限
- AIエージェントシステムが起動している環境
- インターネット接続

---

## 🚀 Step 1: Slack Appの作成

### 1.1 Slack API Consoleにアクセス

1. **ブラウザで [https://api.slack.com/apps](https://api.slack.com/apps) を開く**
2. **「Create New App」ボタンをクリック**
3. **「From scratch」を選択**

### 1.2 アプリ基本情報の入力

```
App Name: AI Command Agent
Pick a workspace: [あなたのワークスペースを選択]
```

4. **「Create App」ボタンをクリック**

---

## ⚙️ Step 2: 権限設定（OAuth & Permissions）

### 2.1 左メニューから「OAuth & Permissions」をクリック

### 2.2 Bot Token Scopesに以下のスコープを追加

**必須スコープ（順番にクリックして追加）：**

1. `app_mentions:read` - アプリへのメンション読み取り
2. `chat:write` - メッセージ送信
3. `chat:write.public` - パブリックチャンネルへの投稿
4. `channels:read` - チャンネル情報読み取り
5. `im:read` - DMメッセージ読み取り
6. `im:write` - DMメッセージ送信
7. `im:history` - DM履歴読み取り
8. `users:read` - ユーザー情報読み取り

### 2.3 ワークスペースへのインストール

1. **「Install to Workspace」ボタンをクリック**
2. **権限確認画面で「許可する」をクリック**
3. **表示される Bot User OAuth Token（`xoxb-...`）をコピーして保存**

---

## 🔔 Step 3: イベント購読設定

### 3.1 左メニューから「Event Subscriptions」をクリック

### 3.2 イベント購読を有効化

1. **「Enable Events」をトグルでONにする**
2. **Request URLは一旦空のままにしておく**（Socket Mode使用のため）

### 3.3 Subscribe to bot eventsセクションで以下を追加

**「Add Bot User Event」をクリックして順番に追加：**

1. `app_mention` - @AI-Agent メンション検知
2. `message.im` - ダイレクトメッセージ受信

### 3.4 設定を保存

**「Save Changes」をクリック**

---

## 🔌 Step 4: Socket Mode設定（重要）

### 4.1 左メニューから「Socket Mode」をクリック

### 4.2 Socket Modeを有効化

1. **「Enable Socket Mode」をトグルでONにする**
2. **「Generate an app-level token to enable Socket Mode」セクションで：**
   - Token Name: `socket-mode-token`
   - Scope: `connections:write` を選択
   - **「Generate」ボタンをクリック**
3. **表示される App-Level Token（`xapp-...`）をコピーして保存**

---

## 🔐 Step 5: Signing Secretの取得

### 5.1 左メニューから「Basic Information」をクリック

### 5.2 App Credentialsセクション

**「Signing Secret」の「Show」をクリックしてコピー・保存**

---

## 🔧 Step 6: 環境変数の設定

### 6.1 .envファイルの編集

プロジェクトルートの`.env`ファイルを編集：

```bash
# Slack設定（ここに実際の値を設定）
SLACK_BOT_TOKEN=xoxb-1234567890-1234567890123-abcdefghijklmnopqrstuvwx
SLACK_SIGNING_SECRET=1234567890abcdef1234567890abcdef
SLACK_APP_TOKEN=xapp-1-A1234567890-1234567890123-abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwx

# AI API設定
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-claude-key-here

# プロジェクト設定
PROJECT_PATH=/home/kato/docker/GAAI02
PROJECT_DIR=/workspace
```

**⚠️ 実際のトークン値に置き換えてください**

---

## 🏠 Step 7: Botをワークスペースに追加

### 7.1 チャンネルにBotを招待

任意のSlackチャンネルで：

```
/invite @AI Command Agent
```

または

1. **チャンネル名をクリック**
2. **「インテグレーション」タブ**
3. **「アプリを追加」**
4. **「AI Command Agent」を選択**

---

## 🧪 Step 8: システム起動とテスト

### 8. SlackListener 動作確認

仮想環境をアクティブにした上で、SlackListener と Executor の初期化テストを実行します。

```bash
codex test-components
```

両コンポーネントとも `OK` が出力されれば、Slack からのメンション受信・コマンド実行の準備が整っています。

あとは Slack 上で:

```bash
@AI Command Agent <タスク内容>
```

を投げるだけで、自動的にタスク計画・実行・結果通知のワークフローが実行されます。

**期待する動作：**
1. 受付確認メッセージ
2. タスク分析・計画の実行
3. 結果報告

---

## 🔍 トラブルシューティング

### 問題1: 「アプリが応答しない」

**確認事項：**
- [ ] Socket Mode が有効になっている
- [ ] `SLACK_APP_TOKEN` が正しく設定されている
- [ ] `codex test-components` で SlackListener／Executor のセルフテストが OK になっている

**解決方法：**
```bash
codex test-components
```

### 問題2: 「権限エラー」

**確認事項：**
- [ ] Bot Token Scopesが全て追加されている
- [ ] ワークスペースに正しくインストールされている
- [ ] `SLACK_BOT_TOKEN`が正しい

**解決方法：**
1. OAuth & Permissionsで「Reinstall to Workspace」
2. 新しいBot Tokenをコピーして`.env`を更新

### 問題3: 「タスクが実行されない」

**確認事項：**
- [ ] `OPENAI_API_KEY` が設定されている
- [ ] プランファイル (`plan.json`) の `domain_phases[*].exec` が正しく命令を含んでいる

**デバッグ方法：**
```bash
codex health-check
codex test-components
```

### 問題4: 「Socket Mode接続エラー」

**確認事項：**
- [ ] インターネット接続
- [ ] ファイアウォール設定
- [ ] App-Level Tokenの`connections:write`スコープ

**解決方法：**
```bash
# 新しいApp-Level Tokenの生成
# Slack API Console → Socket Mode → Regenerate Token
```

---

## 📊 連携状況の確認方法

### ログでの確認

```bash
# リアルタイムログ監視
make logs

# 特定のログ確認
docker-compose exec ai-agent cat logs/ai_agent.log
```

### ヘルスチェック

```bash
# システム全体のヘルスチェック
make health

# 詳細ヘルスチェック
curl http://localhost:3000/health
```

### 接続状態の確認

**正常時のログ出力例：**
```
2025-06-23 10:30:00 - ai_agent - INFO - AI Command Agent initialized successfully
2025-06-23 10:30:01 - ai_agent - INFO - Slack App initialized successfully
2025-06-23 10:30:02 - ai_agent - INFO - Socket Mode connection established
2025-06-23 10:30:02 - ai_agent - INFO - AI Command Agent is running and ready to receive tasks!
```

---

## 🎯 使用例

### 基本的なタスク例

```
@AI Command Agent 以下のタスクをお願いします：
- Pythonでシンプルなウェブサーバーを作成
- ポート8000で起動
- "Hello, World!"を表示
```

### より複雑なタスク例

```
@AI Command Agent 
データベースを使ったTodoアプリを作ってください：
- SQLiteデータベース使用
- CRUD操作可能
- 簡単なWebインターフェース付き
```

### ファイル操作タスク例

```
@AI Command Agent 
プロジェクトファイルを整理してください：
- 不要なファイルの削除
- ディレクトリ構造の最適化
- README.mdの更新
```

---

## 🔄 メンテナンス

### 定期的なトークン更新

**推奨頻度：3ヶ月ごと**

1. Slack API Consoleで新しいトークンを生成
2. `.env`ファイルを更新
3. システム再起動

### ログのクリーンアップ

```bash
# 30日以上古いログの削除
docker-compose exec ai-agent python -c "
from src.utils.logger import cleanup_old_logs
cleanup_old_logs(30)
"
```

### バックアップ

```bash
# 重要なデータのバックアップ
cp -r data/ backup/data_$(date +%Y%m%d)/
cp .env backup/env_$(date +%Y%m%d)
```

---

## ✅ チェックリスト

連携設定完了の確認：

- [ ] Slack Appが作成済み
- [ ] 必要なBot Token Scopesが追加済み
- [ ] Socket Modeが有効化済み
- [ ] 3つのトークン/シークレットを取得済み
  - [ ] Bot User OAuth Token (`xoxb-...`)
  - [ ] App-Level Token (`xapp-...`)
  - [ ] Signing Secret
- [ ] `.env`ファイルが正しく設定済み
- [ ] システムが正常起動済み
- [ ] Slackでのメンション応答テスト成功
- [ ] ダイレクトメッセージ応答テスト成功
- [ ] 実際のタスク実行テスト成功

**すべてのチェックが完了すれば、AIコマンドエージェントとSlackの連携は正常に動作しています！**

---

## 📞 サポート

問題が解決しない場合：

1. `make logs`でログを確認
2. `make health`でシステム状態を確認
3. Slack API Consoleで設定を再確認
4. 必要に応じてトークンを再生成
