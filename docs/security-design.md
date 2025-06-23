# セキュリティ設計書

## 1. セキュリティ要件概要

本システムは、AIが自律的にコマンドを生成・実行するため、以下のセキュリティ要件を満たす必要があります：

1. **実行環境の隔離**: ホストシステムへの影響を最小化
2. **アクセス制御**: プロジェクトディレクトリ内での権限最大化、外部への影響最小化
3. **監査証跡**: 全実行履歴の記録
4. **認証・認可**: 正当なユーザーのみのアクセス

## 2. 脅威モデルと対策

### 2.1 主要な脅威

| 脅威                     | リスクレベル | 対策                                       |
| ------------------------ | ------------ | ------------------------------------------ |
| コマンドインジェクション | 高           | コマンド検証、プロジェクトディレクトリ制限 |
| ディレクトリトラバーサル | 高           | chroot/コンテナ隔離 + パス制限             |
| Windowsマウント領域操作  | 高           | Windowsマウント検出と禁止                  |
| リソース枯渇             | 中           | リソース制限、タイムアウト                 |
| 情報漏洩                 | 中           | ログマスキング、暗号化                     |

### 2.2 AIプロンプトインジェクション対策

```python
class CommandValidator:
    def __init__(self, project_root="/workspace"):
        self.project_root = os.path.realpath(project_root)
        self.windows_mount_patterns = [
            r'/mnt/c/',     # WSL2 Cドライブマウント
            r'/mnt/d/',     # WSL2 Dドライブマウント  
            r'/mnt/[a-zA-Z]/',  # その他ドライブマウント
            r'/media/',     # 一般的なメディアマウント
        ]
    
    # 危険なコマンドパターン
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',      # ルートからの削除
        r':(){ :|:& };:',     # Fork bomb
        r'>\s*/dev/sda',      # ディスク直接書き込み
        r'dd\s+if=.+of=/dev/', # ディスク操作
        r'sudo\s+.*',         # sudo実行（許可制）
        r'su\s+.*',           # ユーザー切り替え
    ]
    
    # 許可コマンドリスト（ホワイトリスト方式）
    ALLOWED_COMMANDS = [
        # 基本コマンド
        'ls', 'pwd', 'cat', 'grep', 'find', 'echo', 'head', 'tail', 'wc',
        'mkdir', 'touch', 'cp', 'mv', 'rm', 'chmod', 'chown',
        # 開発ツール
        'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'npx', 
        'git', 'curl', 'wget', 'unzip', 'tar',
        # データベース・AI関連
        'sqlite3', 'psql', 'mysql', 'redis-cli',
        'docker', 'docker-compose',
        # 必要に応じて管理者権限が必要なツール
        'apt', 'apt-get', 'apt-cache', 'dpkg',
        'systemctl', 'service',
    ]
    
    def validate(self, command):
        """コマンドの安全性を検証"""
        # 危険パターンチェック
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                # sudoは特別扱い：DB構築等で必要な場合がある
                if pattern.startswith(r'sudo') and self._is_safe_sudo_command(command):
                    continue
                raise SecurityError(f"Dangerous command pattern: {pattern}")
        
        # プロジェクトディレクトリ外への操作をチェック
        if self._accesses_outside_project(command):
            raise SecurityError("Access outside project directory denied")
        
        # Windowsマウント領域へのアクセスをチェック
        if self._accesses_windows_mount(command):
            raise SecurityError("Windows mount access denied")
        
        # コマンド抽出と検証
        base_command = command.split()[0]
        if base_command not in self.ALLOWED_COMMANDS:
            if not self._is_safe_absolute_path(base_command):
                raise SecurityError(f"Command not in whitelist: {base_command}")
    
    def _is_safe_sudo_command(self, command):
        """sudo コマンドが安全かどうかをチェック"""
        # パッケージ管理系のsudoは許可
        safe_sudo_patterns = [
            r'sudo\s+(apt|apt-get|dpkg)',
            r'sudo\s+(systemctl|service)',
            r'sudo\s+pip3?\s+install',
            # 必要に応じて追加
        ]
        
        for pattern in safe_sudo_patterns:
            if re.search(pattern, command):
                return True
        return False
    
    def _accesses_outside_project(self, command):
        """プロジェクトディレクトリ外へのアクセスをチェック"""
        # 絶対パスや相対パスでの外部アクセスを検出
        dangerous_path_patterns = [
            r'\.\./',           # 上位ディレクトリへの移動
            r'/home/[^/]+',     # 他ユーザーのホームディレクトリ
            r'/etc/',           # システム設定ディレクトリ
            r'/var/',           # システム変数ディレクトリ
            r'/usr/',           # システムプログラム（読み取りは除く）
            r'/bin/',           # システムバイナリ
            r'/sbin/',          # システム管理バイナリ
        ]
        
        # 読み取り専用操作は一部許可
        readonly_commands = ['cat', 'ls', 'head', 'tail', 'grep', 'find', 'which']
        command_parts = command.split()
        if command_parts and command_parts[0] in readonly_commands:
            return False  # 読み取り専用コマンドは外部アクセス許可
        
        for pattern in dangerous_path_patterns:
            if re.search(pattern, command):
                return True
        return False
    
    def _accesses_windows_mount(self, command):
        """Windowsマウント領域へのアクセスをチェック"""
        for pattern in self.windows_mount_patterns:
            if re.search(pattern, command):
                return True
        return False
    
    def _is_safe_absolute_path(self, command_path):
        """絶対パスのコマンドが安全かどうかをチェック"""
        if not command_path.startswith('/'):
            return True  # 相対パスは安全と仮定
        
        # プロジェクトディレクトリ内の実行ファイルは許可
        real_path = os.path.realpath(command_path)
        if real_path.startswith(self.project_root):
            return True
        
        # 一般的なシステムコマンドパスは許可
        safe_system_paths = [
            '/usr/bin/', '/bin/', '/usr/local/bin/',
            '/usr/sbin/', '/sbin/'  # 必要な場合のみ
        ]
        
        for safe_path in safe_system_paths:
            if real_path.startswith(safe_path):
                return True
        
        return False
```

## 3. Docker実行環境のセキュリティ

### 3.1 Dockerコンテナ設定
```yaml
services:
  executor:
    image: executor:latest
    user: "1000:1000"  # 非rootユーザー
    cap_drop:
      - ALL  # 全capabilities削除
    cap_add:
      - CHOWN       # ファイル所有者変更（プロジェクト内）
      - DAC_OVERRIDE # ファイル権限オーバーライド（必要時）
      - SETUID      # DB構築等で必要な場合
      - SETGID      # グループ権限変更
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined  # AI開発ツール使用のため
    read_only: false  # AI開発でシステム変更が必要
    tmpfs:
      - /tmp
      - /var/tmp
    volumes:
      - type: bind
        source: ${PROJECT_PATH}
        target: /workspace
        read_only: false  # プロジェクトディレクトリは読み書き可
      # Windowsマウントは明示的に除外
    environment:
      - EXECUTOR_TIMEOUT=300  # 5分タイムアウト
      - PROJECT_ROOT=/workspace
    deploy:
      resources:
        limits:
          cpus: '4'      # AI開発のため増量
          memory: 8G     # LLaMA等のため増量
        reservations:
          cpus: '2'
          memory: 4G
```

### 3.2 ファイルアクセス制御
```python
class FileAccessController:
    def __init__(self, allowed_base_path="/workspace"):
        self.allowed_base = os.path.realpath(allowed_base_path)
        self.windows_mount_patterns = [
            r'/mnt/c',
            r'/mnt/d', 
            r'/mnt/[a-zA-Z]',
            r'/media',
        ]
    
    def check_path(self, path):
        """パスアクセスの安全性をチェック"""
        real_path = os.path.realpath(path)
        
        # プロジェクトディレクトリ外のアクセスチェック
        if not real_path.startswith(self.allowed_base):
            # システムディレクトリの読み取り専用アクセスは許可
            if self._is_readonly_system_access(real_path):
                return True
            raise SecurityError(f"Access denied: {path}")
        
        # Windowsマウント領域チェック
        if self._is_windows_mount(real_path):
            raise SecurityError("Windows mount access denied")
        
        return True
    
    def _is_readonly_system_access(self, path):
        """システムディレクトリの読み取り専用アクセスかチェック"""
        readonly_system_paths = [
            '/usr/bin/', '/bin/', '/usr/local/bin/',
            '/etc/', '/usr/share/', '/var/log/'
        ]
        
        for sys_path in readonly_system_paths:
            if path.startswith(sys_path):
                return True
        return False
    
    def _is_windows_mount(self, real_path):
        """Windowsマウント領域かチェック"""
        for pattern in self.windows_mount_patterns:
            if re.search(pattern, real_path):
                return True
        return False
```

### 3.3 AI開発環境の権限管理
```python
class AIDevEnvironmentManager:
    """AI開発に必要な環境構築の権限管理"""
    
    def __init__(self):
        self.allowed_install_commands = [
            # Python関連
            'pip install', 'pip3 install', 'conda install',
            # Node.js関連  
            'npm install', 'yarn install',
            # システムパッケージ（sudo必要）
            'sudo apt install', 'sudo apt-get install',
            'sudo dpkg -i',
            # Docker関連
            'docker pull', 'docker build', 'docker run',
            # データベース
            'sudo systemctl start postgresql',
            'sudo systemctl start mysql',
            'sudo systemctl start redis',
        ]
    
    def validate_ai_dev_command(self, command):
        """AI開発用コマンドの妥当性をチェック"""
        # LLaMA, データベース, AI開発ツールの構築は許可
        ai_dev_patterns = [
            r'.*llama.*',
            r'.*pytorch.*', 
            r'.*tensorflow.*',
            r'.*huggingface.*',
            r'.*transformers.*',
            r'.*postgresql.*',
            r'.*mysql.*',
            r'.*redis.*',
            r'.*neo4j.*',
            r'.*py2neo.*',
        ]
        
        for pattern in ai_dev_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return command in self.allowed_install_commands
```

## 4. 認証・認可

### 4.1 Slack認証フロー
```python
class SlackAuthenticator:
    def verify_request(self, request):
        # 署名検証
        timestamp = request.headers.get('X-Slack-Request-Timestamp')
        signature = request.headers.get('X-Slack-Signature')
        
        # タイムスタンプ検証（5分以内）
        if abs(time.time() - float(timestamp)) > 300:
            raise AuthError("Request too old")
        
        # HMAC署名検証
        base_string = f"v0:{timestamp}:{request.body}"
        expected_sig = f"v0={hmac.new(
            SLACK_SIGNING_SECRET.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()}"
        
        if not hmac.compare_digest(signature, expected_sig):
            raise AuthError("Invalid signature")
```

### 4.2 プロジェクトディレクトリ権限管理
```python
class ProjectPermissionManager:
    """プロジェクトディレクトリ内での権限管理"""
    
    def __init__(self, project_root="/workspace"):
        self.project_root = project_root
        self.setup_project_permissions()
    
    def setup_project_permissions(self):
        """プロジェクト用の権限設定"""
        try:
            # プロジェクトディレクトリの所有権確保
            os.chown(self.project_root, 1000, 1000)
            
            # 必要なサブディレクトリ作成
            subdirs = ['data', 'logs', 'temp', 'models', 'db']
            for subdir in subdirs:
                subdir_path = os.path.join(self.project_root, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                os.chmod(subdir_path, 0o755)
                
        except PermissionError:
            # 権限がない場合は警告のみ
            logging.warning("Could not set up project permissions")
```

## 5. 監査とログ

### 5.1 実行ログ記録
```python
class AuditLogger:
    def __init__(self):
        self.log_file = "/workspace/logs/audit.log"
        self.setup_logging()
    
    def log_command_execution(self, context):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": context.user_id,
            "channel_id": context.channel_id,
            "task_id": context.task_id,
            "phase_id": context.phase_id,
            "command": context.command,
            "working_dir": context.working_dir,
            "exit_code": context.exit_code,
            "execution_time": context.execution_time,
            "output_size": len(context.output),
            "security_level": self._assess_security_level(context.command)
        }
        
        # センシティブ情報のマスキング
        log_entry["command"] = self._mask_sensitive(log_entry["command"])
        
        # プロジェクトディレクトリ内にログ保存
        self._persist_log(log_entry)
    
    def _assess_security_level(self, command):
        """コマンドのセキュリティレベル評価"""
        if 'sudo' in command:
            return "HIGH"
        elif any(cmd in command for cmd in ['rm', 'mv', 'cp']):
            return "MEDIUM"
        else:
            return "LOW"
    
    def _mask_sensitive(self, command):
        """センシティブ情報のマスキング"""
        # API キー、パスワード等のマスキング
        patterns = [
            (r'password[=\s]+\S+', 'password=***'),
            (r'token[=\s]+\S+', 'token=***'),
            (r'key[=\s]+\S+', 'key=***'),
        ]
        
        masked_command = command
        for pattern, replacement in patterns:
            masked_command = re.sub(pattern, replacement, masked_command, flags=re.IGNORECASE)
        
        return masked_command
```

### 5.2 ログ保護
```python
class LogProtection:
    def __init__(self):
        self.log_directory = "/workspace/logs"
        self.setup_log_protection()
    
    def setup_log_protection(self):
        """ログファイルの保護設定"""
        # ログディレクトリの権限設定
        os.makedirs(self.log_directory, exist_ok=True)
        os.chmod(self.log_directory, 0o700)  # 所有者のみアクセス可
        
        # ローテーション設定
        self.setup_log_rotation()
    
    def setup_log_rotation(self):
        """ログローテーションの設定"""
        # 日次ローテーション、90日保持
        import logging.handlers
        
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(self.log_directory, "audit.log"),
            when='midnight',
            interval=1,
            backupCount=90
        )
        return handler
```

## 6. シークレット管理

### 6.1 環境変数セキュリティ
```bash
# .env ファイル権限設定
chmod 600 .env
chown 1000:1000 .env

# プロジェクトディレクトリ内でのシークレット管理
mkdir -p /workspace/.secrets
chmod 700 /workspace/.secrets
```

### 6.2 APIキーローテーション
```python
class APIKeyManager:
    def __init__(self):
        self.secrets_dir = "/workspace/.secrets"
        self.rotation_interval = 90  # 90日
    
    def check_key_rotation_needed(self):
        """APIキーローテーションの必要性チェック"""
        key_age_file = os.path.join(self.secrets_dir, "key_created.timestamp")
        
        if not os.path.exists(key_age_file):
            return True
        
        with open(key_age_file, 'r') as f:
            created_timestamp = float(f.read().strip())
        
        age_days = (time.time() - created_timestamp) / (24 * 3600)
        return age_days > self.rotation_interval
```

## 7. インシデント対応

### 7.1 異常検知
```python
class SecurityMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'consecutive_failures': 3,
            'suspicious_commands': 5,
            'resource_usage': 0.9  # 90%
        }
    
    def monitor_security_events(self):
        """セキュリティイベントの監視"""
        # 連続した実行エラー
        if self.check_consecutive_failures():
            self.trigger_security_alert("Consecutive command failures detected")
        
        # 異常なリソース使用
        if self.check_resource_usage():
            self.trigger_security_alert("Abnormal resource usage detected")
        
        # 不審なコマンドパターン
        if self.check_suspicious_patterns():
            self.trigger_security_alert("Suspicious command patterns detected")
    
    def trigger_security_alert(self, message):
        """セキュリティアラートの発報"""
        # 実行停止
        self.emergency_stop()
        
        # Slackアラート
        self.send_slack_alert(message)
        
        # ログ保全
        self.preserve_security_logs()
```

### 7.2 対応手順
```python
class IncidentResponse:
    def emergency_stop(self):
        """緊急停止処理"""
        # 1. 実行中のプロセス停止
        self.stop_all_executions()
        
        # 2. 一時ファイルのクリーンアップ
        self.cleanup_temp_files()
        
        # 3. セキュリティログの保護
        self.protect_security_logs()
    
    def investigate_incident(self, incident_type):
        """インシデント調査"""
        # ログ分析とレポート生成
        investigation_report = self.analyze_security_logs(incident_type)
        
        # 対策提案
        recommendations = self.generate_recommendations(investigation_report)
        
        return investigation_report, recommendations
```

## 8. まとめ

### 8.1 セキュリティ層構成
1. **物理層**: Dockerコンテナによる隔離
2. **ネットワーク層**: プロジェクトディレクトリ内通信のみ
3. **アプリケーション層**: コマンド検証とファイルアクセス制御
4. **監査層**: 全実行履歴の記録と分析

### 8.2 主要な設計思想
- **AI開発の自由度確保**: プロジェクトディレクトリ内での最大権限
- **外部影響の最小化**: Windowsマウント等の保護
- **透明性の確保**: 全操作の監査証跡
- **段階的権限管理**: 必要に応じたsudo権限の許可