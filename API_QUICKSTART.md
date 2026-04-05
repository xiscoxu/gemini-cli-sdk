# Gemini CLI SDK API 快速开始

## 5 分钟快速上手

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/xiscoxu/gemini-cli-sdk.git
cd gemini-cli-sdk

# 安装 API 服务器
pip install -e ".[api]"

# 确保 Gemini CLI 已安装
npm install -g @google/gemini-cli
gemini -p "Hello"  # 首次运行配置
```

### 2. 启动 API 服务器

```bash
gemini-api-server --port 8765
```

### 3. 使用 API

#### 方式 A: 使用 OpenAI Python SDK

```bash
# 安装 OpenAI SDK
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:8765/v1',
    api_key='dummy-key'
)

response = client.chat.completions.create(
    model='gemini-2.5-pro',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)

print(response.choices[0].message.content)
```

#### 方式 B: 使用 cURL

```bash
curl http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-pro",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 常见使用场景

### 流式响应

```python
stream = client.chat.completions.create(
    model='gemini-2.5-flash',
    messages=[{'role': 'user', 'content': 'Write a poem'}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### 多轮对话

```python
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': 'What is Python?'}
]

response = client.chat.completions.create(
    model='gemini-2.5-pro',
    messages=messages
)

# 添加助手回复到历史
messages.append({
    'role': 'assistant',
    'content': response.choices[0].message.content
})

# 继续对话
messages.append({'role': 'user', 'content': 'Can you give an example?'})
response = client.chat.completions.create(
    model='gemini-2.5-pro',
    messages=messages
)
```

### 并发请求

```python
from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI(
    base_url='http://localhost:8765/v1',
    api_key='dummy-key'
)

async def main():
    tasks = [
        client.chat.completions.create(
            model='gemini-2.5-flash',
            messages=[{'role': 'user', 'content': f'Question {i}'}]
        )
        for i in range(5)
    ]
    responses = await asyncio.gather(*tasks)
    for resp in responses:
        print(resp.choices[0].message.content)

asyncio.run(main())
```

## 配置服务器

```bash
# 高性能配置
gemini-api-server \
  --host 0.0.0.0 \
  --port 8765 \
  --rate-limit 200 \
  --max-concurrency 16 \
  --max-processes 10 \
  --timeout 60

# 调试模式
gemini-api-server \
  --debug \
  --log-level DEBUG \
  --reload
```

## 查看文档

启动服务器后访问：
- Swagger UI: http://localhost:8765/docs
- 健康检查: http://localhost:8765/health
- 统计信息: http://localhost:8765/stats

## 与现有工具集成

### LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8765/v1",
    api_key="dummy-key",
    model="gemini-2.5-pro"
)

response = llm.invoke("What is machine learning?")
print(response.content)
```

### Cherry Studio

在 Cherry Studio 设置中添加自定义模型提供商：
- Provider Type: OpenAI
- API Host: `http://localhost:8765`
- API Key: 任意字符串
- Model: `gemini-2.5-pro` 或 `gemini-2.5-flash`

## 常见问题

**Q: API 密钥是必需的吗？**
A: 不是。虽然 OpenAI SDK 要求提供密钥，但你可以使用任意字符串。

**Q: 支持哪些模型？**
A: 所有 Gemini CLI 支持的模型：
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-2.0-flash
- gemini-1.5-pro
- gemini-1.5-flash

**Q: 如何处理速率限制？**
A: API 默认限制 60 请求/分钟，可通过 `--rate-limit` 参数调整。

**Q: 生产环境如何部署？**
A: 参考 README.md 中的 systemd 或 Docker 部署方案。

## 下一步

- 查看完整示例：`examples/api_usage_example.py`
- 阅读完整文档：README.md 中的"API 服务器"章节
- 参考 API 文档：http://localhost:8765/docs
