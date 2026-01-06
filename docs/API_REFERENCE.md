# Gemini CLI SDK API Reference

这是 Gemini CLI SDK 的完整 API 参考文档。

## 目录

- [GeminiClient](#geminiclient) - 主要客户端类
- [GeminiConfig](#geminiconfig) - 配置管理
- [ConfigManager](#configmanager) - 配置文件管理
- [SessionManager](#sessionmanager) - 会话管理
- [数据模型](#数据模型) - 响应和消息模型
- [异常类](#异常类) - 错误处理
- [工具函数](#工具函数) - 实用工具

---

## GeminiClient

主要的客户端类，用于与 Gemini CLI 进行交互。

### 构造函数

```python
GeminiClient(config: Optional[GeminiConfig] = None)
```

**参数:**
- `config` (GeminiConfig, 可选): 客户端配置。如果未提供，将使用默认配置。

**示例:**
```python
from gemini_cli_sdk import GeminiClient, GeminiConfig

# 使用默认配置
client = GeminiClient()

# 使用自定义配置
config = GeminiConfig(max_processes=3, log_level="DEBUG")
client = GeminiClient(config=config)
```

### 异步上下文管理器

```python
async with GeminiClient() as client:
    # 使用客户端
    response = await client.one_shot("Hello")
```

### 核心方法

#### one_shot()

执行单次问答，不保持上下文。

```python
async def one_shot(
    self,
    message: str,
    system_instruction: Optional[str] = None
) -> GeminiResponse
```

**参数:**
- `message` (str): 要发送的消息
- `system_instruction` (str, 可选): 系统指令

**返回:** `GeminiResponse` 对象

**示例:**
```python
# 简单问答
response = await client.one_shot("什么是Python？")

# 带系统指令
response = await client.one_shot(
    "解释递归",
    system_instruction="你是一个编程教师，用简单易懂的方式解释概念"
)
```

#### chat()

在指定会话中发送消息，保持对话上下文。

```python
async def chat(
    self,
    message: str,
    session_id: str,
    system_instruction: Optional[str] = None
) -> GeminiResponse
```

**参数:**
- `message` (str): 要发送的消息
- `session_id` (str): 会话ID
- `system_instruction` (str, 可选): 系统指令

**返回:** `GeminiResponse` 对象

**示例:**
```python
# 创建会话
session_id = client.create_session()

# 发送消息
response1 = await client.chat("你好", session_id)
response2 = await client.chat("我刚才说了什么？", session_id)

# 关闭会话
client.close_session(session_id)
```

#### send_batch()

批量发送消息到指定会话。

```python
async def send_batch(
    self,
    messages: List[str],
    session_id: str,
    system_instruction: Optional[str] = None
) -> List[GeminiResponse]
```

**参数:**
- `messages` (List[str]): 消息列表
- `session_id` (str): 会话ID
- `system_instruction` (str, 可选): 系统指令

**返回:** `GeminiResponse` 对象列表

**示例:**
```python
session_id = client.create_session()
messages = ["第一个问题", "第二个问题", "第三个问题"]
responses = await client.send_batch(messages, session_id)
```

#### send_concurrent()

并发发送多个独立消息。

```python
async def send_concurrent(
    self,
    messages: List[str],
    system_instruction: Optional[str] = None
) -> List[GeminiResponse]
```

**参数:**
- `messages` (List[str]): 消息列表
- `system_instruction` (str, 可选): 系统指令

**返回:** `GeminiResponse` 对象列表

**示例:**
```python
messages = ["问题1", "问题2", "问题3"]
responses = await client.send_concurrent(messages)
```

#### send_message_with_features()

发送带有高级功能的消息。

```python
async def send_message_with_features(
    self,
    message: str,
    session_id: Optional[str] = None,
    system_instruction: Optional[str] = None,
    process_file_refs: bool = False,
    allow_shell_commands: bool = False
) -> GeminiResponse
```

**参数:**
- `message` (str): 消息内容
- `session_id` (str, 可选): 会话ID
- `system_instruction` (str, 可选): 系统指令
- `process_file_refs` (bool): 是否处理文件引用 (@filename)
- `allow_shell_commands` (bool): 是否允许执行Shell命令 (!command)

**示例:**
```python
# 文件引用
response = await client.send_message_with_features(
    "分析这个文件: @data.txt",
    process_file_refs=True
)

# Shell 命令
response = await client.send_message_with_features(
    "!ls -la",
    allow_shell_commands=True
)
```

### 会话管理方法

#### create_session()

创建新的对话会话。

```python
def create_session(
    self,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

**参数:**
- `user_id` (str, 可选): 用户ID
- `metadata` (dict, 可选): 会话元数据

**返回:** 会话ID (str)

#### close_session()

关闭指定会话。

```python
def close_session(self, session_id: str) -> None
```

#### list_sessions()

列出所有活跃会话。

```python
def list_sessions(self) -> List[SessionInfo]
```

### 配置和状态方法

#### get_config()

获取当前配置。

```python
def get_config(self) -> GeminiConfig
```

#### set_config()

设置新配置。

```python
def set_config(self, config: GeminiConfig) -> None
```

#### get_stats()

获取客户端统计信息。

```python
def get_stats(self) -> Dict[str, Any]
```

**返回示例:**
```python
{
    "sessions": {
        "total": 2,
        "active": 1
    },
    "processes": {
        "total": 3,
        "idle": 1
    }
}
```

#### health_check()

执行健康检查。

```python
async def health_check(self) -> Dict[str, Any]
```

---

## GeminiConfig

配置类，用于设置客户端行为。

### 构造函数

```python
GeminiConfig(
    max_processes: int = 5,
    idle_timeout: int = 300,
    max_context_length: int = 50,
    gemini_command: str = "gemini",
    gemini_args: List[str] = None,
    enable_logging: bool = True,
    log_level: str = "INFO",
    response_timeout: float = 30.0,
    cleanup_interval: int = 60
)
```

**参数:**
- `max_processes` (int): 最大进程数，默认 5
- `idle_timeout` (int): 空闲超时时间（秒），默认 300
- `max_context_length` (int): 最大上下文长度，默认 50
- `gemini_command` (str): Gemini CLI 命令，默认 "gemini"
- `gemini_args` (List[str]): Gemini CLI 参数
- `enable_logging` (bool): 是否启用日志，默认 True
- `log_level` (str): 日志级别，默认 "INFO"
- `response_timeout` (float): 响应超时时间（秒），默认 30.0
- `cleanup_interval` (int): 清理间隔（秒），默认 60

**示例:**
```python
config = GeminiConfig(
    max_processes=10,
    idle_timeout=600,
    log_level="DEBUG",
    response_timeout=60.0
)
```

---

## ConfigManager

配置文件管理器。

### 构造函数

```python
ConfigManager(config_file: Optional[str] = None)
```

### 方法

#### load_config()

从文件和环境变量加载配置。

```python
def load_config(self) -> GeminiConfig
```

#### save_config()

保存配置到文件。

```python
def save_config(self, config: GeminiConfig) -> None
```

#### get_config_dict()

获取配置字典。

```python
def get_config_dict(self) -> Dict[str, Any]
```

**示例:**
```python
from gemini_cli_sdk.config import ConfigManager

manager = ConfigManager("my_config.json")
config = manager.load_config()

# 修改配置
config.max_processes = 8
manager.save_config(config)
```

### 环境变量

ConfigManager 支持以下环境变量：

- `GEMINI_MAX_PROCESSES`: 最大进程数
- `GEMINI_IDLE_TIMEOUT`: 空闲超时时间
- `GEMINI_MAX_CONTEXT_LENGTH`: 最大上下文长度
- `GEMINI_COMMAND`: Gemini CLI 命令
- `GEMINI_ARGS`: Gemini CLI 参数（空格分隔）
- `GEMINI_ENABLE_LOGGING`: 是否启用日志 (true/false)
- `GEMINI_LOG_LEVEL`: 日志级别
- `GEMINI_RESPONSE_TIMEOUT`: 响应超时时间
- `GEMINI_CLEANUP_INTERVAL`: 清理间隔

---

## SessionManager

会话管理器，处理对话上下文。

### 构造函数

```python
SessionManager(
    config_manager: Optional[ConfigManager] = None,
    max_context_length: Optional[int] = None
)
```

### 方法

#### create_session()

```python
def create_session(
    self,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

#### close_session()

```python
def close_session(self, session_id: str) -> None
```

#### add_message()

```python
def add_message(
    self,
    session_id: str,
    role: MessageRole,
    content: str
) -> None
```

#### get_context()

```python
def get_context(self, session_id: str) -> List[Message]
```

#### get_session_info()

```python
def get_session_info(self, session_id: str) -> SessionInfo
```

---

## 数据模型

### GeminiResponse

Gemini 响应对象。

```python
@dataclass
class GeminiResponse:
    content: str
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
```

**属性:**
- `content` (str): 响应内容
- `session_id` (str, 可选): 会话ID
- `timestamp` (datetime, 可选): 时间戳
- `metadata` (dict, 可选): 元数据

### Message

消息对象。

```python
@dataclass
class Message:
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
```

### MessageRole

消息角色枚举。

```python
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
```

### SessionInfo

会话信息对象。

```python
@dataclass
class SessionInfo:
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    message_count: int
    metadata: Optional[Dict[str, Any]] = None
```

### ProcessInfo

进程信息对象。

```python
@dataclass
class ProcessInfo:
    pid: int
    status: ProcessStatus
    created_at: datetime
    last_used: datetime
    session_id: Optional[str] = None
```

### ProcessStatus

进程状态枚举。

```python
class ProcessStatus(Enum):
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
```

---

## 异常类

### GeminiSDKError

所有 SDK 异常的基类。

```python
class GeminiSDKError(Exception):
    """Base exception for Gemini CLI SDK."""
    pass
```

### GeminiProcessError

进程相关错误。

```python
class GeminiProcessError(GeminiSDKError):
    """Process management related errors."""
    pass
```

### GeminiSessionError

会话相关错误。

```python
class GeminiSessionError(GeminiSDKError):
    """Session management related errors."""
    pass
```

### GeminiConfigError

配置相关错误。

```python
class GeminiConfigError(GeminiSDKError):
    """Configuration related errors."""
    pass
```

### GeminiTimeoutError

超时错误。

```python
class GeminiTimeoutError(GeminiSDKError):
    """Timeout related errors."""
    pass
```

### GeminiNotFoundError

资源未找到错误。

```python
class GeminiNotFoundError(GeminiSDKError):
    """Resource not found errors."""
    pass
```

### GeminiConnectionError

连接错误。

```python
class GeminiConnectionError(GeminiSDKError):
    """Connection related errors."""
    pass
```

### GeminiValidationError

验证错误。

```python
class GeminiValidationError(GeminiSDKError):
    """Input validation errors."""
    pass
```

---

## 工具函数

### 系统命令处理

```python
from gemini_cli_sdk.system_commands import process_shell_command, process_file_reference

# 处理 Shell 命令
result = await process_shell_command("ls -la")

# 处理文件引用
content = process_file_reference("@data.txt")
```

### 实用工具

```python
from gemini_cli_sdk.utils import (
    validate_session_id,
    format_timestamp,
    sanitize_message,
    format_duration
)

# 验证会话ID
is_valid = validate_session_id("session-123")

# 格式化时间戳
formatted = format_timestamp(datetime.now())

# 清理消息内容
clean_message = sanitize_message("用户输入的消息")

# 格式化持续时间
duration_str = format_duration(timedelta(seconds=120))
```

---

## 使用示例

### 基础使用

```python
import asyncio
from gemini_cli_sdk import GeminiClient, GeminiConfig

async def main():
    config = GeminiConfig(enable_logging=True, log_level="INFO")
    
    async with GeminiClient(config=config) as client:
        # 单次问答
        response = await client.one_shot("什么是Python？")
        print(f"回答: {response.content}")
        
        # 对话会话
        session_id = client.create_session()
        response1 = await client.chat("你好", session_id)
        response2 = await client.chat("我想学编程", session_id)
        client.close_session(session_id)

asyncio.run(main())
```

### 高级功能

```python
async def advanced_example():
    async with GeminiClient() as client:
        # 文件引用
        response = await client.send_message_with_features(
            "分析这个文件: @data.txt",
            process_file_refs=True
        )
        
        # Shell 命令
        response = await client.send_message_with_features(
            "!ls -la",
            allow_shell_commands=True
        )
        
        # 并发处理
        questions = ["问题1", "问题2", "问题3"]
        responses = await client.send_concurrent(questions)
        
        # 批量处理
        session_id = client.create_session()
        messages = ["消息1", "消息2", "消息3"]
        responses = await client.send_batch(messages, session_id)
```

### 错误处理

```python
from gemini_cli_sdk import (
    GeminiClient,
    GeminiTimeoutError,
    GeminiValidationError,
    GeminiNotFoundError
)

async def error_handling_example():
    try:
        async with GeminiClient() as client:
            response = await client.one_shot("测试消息")
    except GeminiTimeoutError:
        print("请求超时")
    except GeminiValidationError as e:
        print(f"输入验证错误: {e}")
    except GeminiNotFoundError:
        print("Gemini CLI 未找到")
    except Exception as e:
        print(f"其他错误: {e}")
```

---

## 配置示例

### 配置文件 (config.json)

```json
{
    "max_processes": 8,
    "idle_timeout": 600,
    "max_context_length": 100,
    "gemini_command": "gemini",
    "gemini_args": ["--interactive", "--json-output"],
    "enable_logging": true,
    "log_level": "INFO",
    "response_timeout": 45.0,
    "cleanup_interval": 120
}
```

### 环境变量配置

```bash
export GEMINI_MAX_PROCESSES=10
export GEMINI_LOG_LEVEL=DEBUG
export GEMINI_RESPONSE_TIMEOUT=60.0
export GEMINI_ARGS="--interactive --json-output --verbose"
```

---

## 性能优化建议

1. **进程池大小**: 根据并发需求调整 `max_processes`
2. **上下文长度**: 合理设置 `max_context_length` 以平衡性能和功能
3. **超时设置**: 根据网络条件调整 `response_timeout`
4. **会话管理**: 及时关闭不需要的会话以释放资源
5. **并发处理**: 对于独立的请求使用 `send_concurrent()`

---

## 最佳实践

1. **使用异步上下文管理器**: 确保资源正确释放
2. **错误处理**: 捕获和处理特定的异常类型
3. **配置管理**: 使用配置文件或环境变量管理设置
4. **日志记录**: 启用适当的日志级别进行调试
5. **会话生命周期**: 明确管理会话的创建和关闭

---

这个 API 参考文档涵盖了 Gemini CLI SDK 的所有主要功能和使用方法。如需更多详细信息，请参考源代码中的文档字符串和示例代码。
