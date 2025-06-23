# AI API通信仕様書

## 1. API エンドポイント構成

### 1.1 使用するAI API
- **OpenAI API**: GPT-4/GPT-4o
- **Anthropic API**: Claude 3/3.5

### 1.2 統一API インターフェース
```python
class UnifiedAIClient:
    def __init__(self):
        self.provider = os.getenv('AI_PROVIDER', 'openai')  # 'openai' or 'anthropic'
        self.openai_client = openai.OpenAI() if self.provider == 'openai' else None
        self.anthropic_client = anthropic.Anthropic() if self.provider == 'anthropic' else None
    
    def call_ai_api(self, messages, model=None, temperature=0.3, max_tokens=4000):
        """統一されたAI API呼び出しインターフェース"""
        if self.provider == 'openai':
            return self._call_openai(messages, model or "gpt-4o", temperature, max_tokens)
        elif self.provider == 'anthropic':
            return self._call_anthropic(messages, model or "claude-3-5-sonnet-20241022", temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    def _call_openai(self, messages, model, temperature, max_tokens):
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    def _call_anthropic(self, messages, model, temperature, max_tokens):
        # システムプロンプトを分離
        system_prompt = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append(msg)
        
        response = self.anthropic_client.messages.create(
            model=model,
            system=system_prompt,
            messages=user_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return json.loads(response.content[0].text)
```

## 2. プロンプトテンプレート管理

### 2.1 Planner用プロンプト構造
```python
def get_planner_prompt(task_summary):
    return [
        {
            "role": "system",
            "content": open("prompts/planner.md", encoding='utf-8').read()
        },
        {
            "role": "user", 
            "content": f"""
タスク情報:
{json.dumps(task_summary, ensure_ascii=False, indent=2)}

上記タスクを実行可能なフェーズに分解し、JSON形式で計画書を作成してください。
"""
        }
    ]
```

### 2.2 Manager用プロンプト構造
```python
def get_manager_prompt(current_state):
    return [
        {
            "role": "system",
            "content": open("prompts/manager.md", encoding='utf-8').read()
        },
        {
            "role": "user",
            "content": f"""
現在のタスク状態:
{json.dumps(current_state, ensure_ascii=False, indent=2)}

実行結果を評価し、必要に応じて計画を更新してください。
"""
        }
    ]
```

## 3. Function Calling 活用

### 3.1 統一されたFunction Calling実装
```python
class UnifiedFunctionCaller:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        
    def execute_with_functions(self, messages, functions):
        """プロバイダーに関係なくFunction Callingを実行"""
        if self.ai_client.provider == 'openai':
            return self._openai_function_calling(messages, functions)
        elif self.ai_client.provider == 'anthropic':
            return self._anthropic_function_calling(messages, functions)
    
    def _openai_function_calling(self, messages, functions):
        response = self.ai_client.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=functions,
            function_call="auto"
        )
        return self._process_openai_response(response)
    
    def _anthropic_function_calling(self, messages, functions):
        # Claude用のtool形式に変換
        tools = self._convert_functions_to_tools(functions)
        response = self.ai_client.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        return self._process_anthropic_response(response)

functions = [{
    "name": "execute_command",
    "description": "Linuxコマンドを実行",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "実行するコマンド"
            },
            "working_dir": {
                "type": "string",
                "description": "実行ディレクトリ"
            }
        },
        "required": ["command"]
    }
}]
```

## 4. レート制限とエラー処理

### 4.1 統一レート制限対策
```python
class UnifiedRateLimiter:
    def __init__(self):
        self.openai_limiter = APIRateLimiter(max_calls_per_minute=20)
        self.anthropic_limiter = APIRateLimiter(max_calls_per_minute=15)
    
    def wait_if_needed(self, provider):
        if provider == 'openai':
            self.openai_limiter.wait_if_needed()
        elif provider == 'anthropic':
            self.anthropic_limiter.wait_if_needed()

class APIRateLimiter:
    def __init__(self, max_calls_per_minute=20):
        self.max_calls = max_calls_per_minute
        self.calls = deque()
    
    def wait_if_needed(self):
        now = time.time()
        self.calls = deque(t for t in self.calls if now - t < 60)
        if len(self.calls) >= self.max_calls:
            sleep_time = 60 - (now - self.calls[0])
            time.sleep(sleep_time)
        self.calls.append(now)
```

### 4.2 統一エラーハンドリング
```python
def unified_api_call_with_retry(ai_client, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return ai_client.call_ai_api(messages)
        except (openai.APITimeoutError, anthropic.APITimeoutError):
            if attempt < max_retries - 1:
                time.sleep(300)  # 5分待機
                continue
            raise
        except (openai.APIError, anthropic.APIError) as e:
            log_error(f"API Error ({ai_client.provider}): {e}")
            raise
```

## 5. コスト管理

### 5.1 統一トークン計算
```python
def estimate_tokens(text, provider='openai'):
    if provider == 'openai':
        # GPT-4系: 1トークン ≈ 4文字（英語）、2文字（日本語）
        return len(text) / 2
    elif provider == 'anthropic':
        # Claude系: 1トークン ≈ 3.5文字（英語）、1.8文字（日本語）
        return len(text) / 1.8
```

### 5.2 統一コスト追跡
```python
COST_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015}
}

class CostTracker:
    def calculate_cost(self, provider, model, input_tokens, output_tokens):
        costs = COST_PER_1K_TOKENS.get(model, {"input": 0, "output": 0})
        return (input_tokens / 1000 * costs["input"] + 
                output_tokens / 1000 * costs["output"])
```

## 6. セキュリティ考慮

### 6.1 統一APIキー管理
```python
class SecureAPIKeyManager:
    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.openai_key and os.getenv('AI_PROVIDER') == 'openai':
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        if not self.anthropic_key and os.getenv('AI_PROVIDER') == 'anthropic':
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
```

### 6.2 統一プロンプトインジェクション対策
```python
class UnifiedPromptValidator:
    def validate_response(self, response, expected_schema):
        # JSONスキーマ検証による応答検証
        jsonschema.validate(response, expected_schema)
        return True
```

## 7. 統一使用例

```python
# 初期化
ai_client = UnifiedAIClient()
function_caller = UnifiedFunctionCaller(ai_client)
rate_limiter = UnifiedRateLimiter()

# API呼び出し
rate_limiter.wait_if_needed(ai_client.provider)
messages = get_planner_prompt(task_summary)
response = unified_api_call_with_retry(ai_client, messages)
```
