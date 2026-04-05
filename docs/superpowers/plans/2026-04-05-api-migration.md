# API 功能迁移 + Brain 论坛帖子 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Gemini CLI SDK v1.2.0 的 OpenAI 兼容 API 模块迁移到 git 仓库，推送远程，并输出 WorldQuant Brain 论坛分享帖。

**Architecture:** 将源目录 `/Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk` 的新增/修改文件复制到目标仓库 `/Users/xujingjie/Work/WQ/gemini-cli-sdk`，提交并推送。博客帖子以 Markdown 形式输出，内容面向量化研究员，结合量化场景展示 SDK 价值。

**Tech Stack:** Python, FastAPI, uvicorn, slowapi, pydantic v2, git

---

## File Map

| 操作 | 文件 |
|------|------|
| 新建目录+文件 | `gemini_cli_sdk/api/__init__.py` |
| 新建 | `gemini_cli_sdk/api/server.py` |
| 新建 | `gemini_cli_sdk/api/config.py` |
| 新建 | `gemini_cli_sdk/api/models.py` |
| 新建 | `gemini_cli_sdk/api/openai_adapter.py` |
| 新建 | `gemini_cli_sdk/api/cli.py` |
| 新建 | `examples/api_usage_example.py` |
| 新建 | `API_QUICKSTART.md` |
| 修改 | `gemini_cli_sdk/__init__.py` (version bump) |
| 修改 | `requirements.txt` (新增依赖) |
| 修改 | `setup.py` (新增 extras + entry_point) |
| 修改 | `README.md` (全面扩充) |

---

### Task 1: 迁移 api/ 模块

**Files:**
- Create: `gemini_cli_sdk/api/__init__.py`
- Create: `gemini_cli_sdk/api/server.py`
- Create: `gemini_cli_sdk/api/config.py`
- Create: `gemini_cli_sdk/api/models.py`
- Create: `gemini_cli_sdk/api/openai_adapter.py`
- Create: `gemini_cli_sdk/api/cli.py`

- [ ] **Step 1: 复制 api/ 目录**

```bash
cp -r /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/gemini_cli_sdk/api \
      /Users/xujingjie/Work/WQ/gemini-cli-sdk/gemini_cli_sdk/api
```

- [ ] **Step 2: 验证文件已复制**

```bash
ls /Users/xujingjie/Work/WQ/gemini-cli-sdk/gemini_cli_sdk/api/
```

Expected output:
```
__init__.py  cli.py  config.py  models.py  openai_adapter.py  server.py
```

- [ ] **Step 3: 验证无 __pycache__ 污染**

```bash
ls /Users/xujingjie/Work/WQ/gemini-cli-sdk/gemini_cli_sdk/api/__pycache__ 2>/dev/null && echo "FOUND - need cleanup" || echo "OK - no pycache"
```

If FOUND, run:
```bash
rm -rf /Users/xujingjie/Work/WQ/gemini-cli-sdk/gemini_cli_sdk/api/__pycache__
```

- [ ] **Step 4: 提交**

```bash
cd /Users/xujingjie/Work/WQ/gemini-cli-sdk
git add gemini_cli_sdk/api/
git commit -m "feat: add OpenAI-compatible REST API module (v1.2.0)"
```

---

### Task 2: 更新 requirements.txt 和 setup.py

**Files:**
- Modify: `requirements.txt`
- Modify: `setup.py`

- [ ] **Step 1: 覆盖 requirements.txt**

```bash
cp /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/requirements.txt \
   /Users/xujingjie/Work/WQ/gemini-cli-sdk/requirements.txt
```

- [ ] **Step 2: 覆盖 setup.py**

```bash
cp /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/setup.py \
   /Users/xujingjie/Work/WQ/gemini-cli-sdk/setup.py
```

- [ ] **Step 3: 验证 setup.py 包含 entry point 和 extras**

```bash
grep -n "gemini-api-server\|fastapi\|extras_require" /Users/xujingjie/Work/WQ/gemini-cli-sdk/setup.py
```

Expected: 看到 `gemini-api-server=gemini_cli_sdk.api.cli:main` 和 `fastapi>=0.104.0`

- [ ] **Step 4: 提交**

```bash
cd /Users/xujingjie/Work/WQ/gemini-cli-sdk
git add requirements.txt setup.py
git commit -m "chore: update dependencies for API server (pydantic v2, fastapi, uvicorn)"
```

---

### Task 3: 更新 __init__.py 和 README.md，新增示例文件

**Files:**
- Modify: `gemini_cli_sdk/__init__.py`
- Modify: `README.md`
- Create: `examples/api_usage_example.py`
- Create: `API_QUICKSTART.md`

- [ ] **Step 1: 覆盖 __init__.py（版本升级）**

```bash
cp /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/gemini_cli_sdk/__init__.py \
   /Users/xujingjie/Work/WQ/gemini-cli-sdk/gemini_cli_sdk/__init__.py
```

- [ ] **Step 2: 验证版本号**

```bash
grep "__version__" /Users/xujingjie/Work/WQ/gemini-cli-sdk/gemini_cli_sdk/__init__.py
```

Expected: `__version__ = "1.2.0"`

- [ ] **Step 3: 覆盖 README.md**

```bash
cp /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/README.md \
   /Users/xujingjie/Work/WQ/gemini-cli-sdk/README.md
```

- [ ] **Step 4: 复制新示例文件和快速上手指南**

```bash
cp /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/examples/api_usage_example.py \
   /Users/xujingjie/Work/WQ/gemini-cli-sdk/examples/api_usage_example.py

cp /Users/xujingjie/Downloads/AI_consultant/code/gemini-cli-sdk/API_QUICKSTART.md \
   /Users/xujingjie/Work/WQ/gemini-cli-sdk/API_QUICKSTART.md
```

- [ ] **Step 5: 验证文件数量**

```bash
ls /Users/xujingjie/Work/WQ/gemini-cli-sdk/examples/ | wc -l
```

Expected: 5（比之前多 1 个）

- [ ] **Step 6: 提交**

```bash
cd /Users/xujingjie/Work/WQ/gemini-cli-sdk
git add gemini_cli_sdk/__init__.py README.md examples/api_usage_example.py API_QUICKSTART.md
git commit -m "docs: update README and add API quickstart guide (v1.2.0)"
```

---

### Task 4: 提交设计文档并 push 到远程

**Files:**
- Already created: `docs/superpowers/specs/2026-04-05-api-migration-design.md`
- Already created: `docs/superpowers/plans/2026-04-05-api-migration.md`

- [ ] **Step 1: 提交设计和计划文档**

```bash
cd /Users/xujingjie/Work/WQ/gemini-cli-sdk
git add docs/
git commit -m "docs: add migration design spec and implementation plan"
```

- [ ] **Step 2: 检查远程**

```bash
git remote -v
```

- [ ] **Step 3: push 所有提交**

```bash
git push origin main
```

Expected: 看到 3-4 个提交被推送，无错误

- [ ] **Step 4: 验证 push 成功**

```bash
git log --oneline -5
```

---

### Task 5: 撰写 WorldQuant Brain 论坛帖子

**Output:** 直接输出到对话，供用户复制发帖

- [ ] **Step 1: 撰写帖子**

帖子内容（中文，Markdown 格式，约 1200 字）：

---

**帖子标题：** 用本地 Gemini CLI 搭建免费 AI 助手——量化研究员的 Alpha 开发提效实践

**帖子正文：**

```markdown
## 背景：量化研究中的 AI 调用痛点

做量化研究，AI 工具几乎已经成了标配。但实际使用中有几个让人头疼的问题：

- **API 费用高**：高频调用 GPT-4/Claude，月账单很快破百美元
- **速率限制**：免费额度不够用，付费额度也有并发上限
- **数据隐私**：把内部因子逻辑、策略描述发给第三方 API，总觉得不安心
- **网络依赖**：某些环境下访问海外 API 不稳定

有没有一种方式，能在本地免费跑一个强大的 AI，还能无缝兼容现有工具链？

## 方案：Gemini CLI SDK + 本地 OpenAI 兼容 API

Google 推出了 Gemini CLI，可以在终端里直接和 Gemini 对话，而且**个人用户免费**。

我写了一个 Python SDK，把 Gemini CLI 封装成易用的异步 API，最新版（v1.2.0）还新增了 **OpenAI 兼容的本地 REST API Server**——这意味着你可以把任何使用 OpenAI SDK 的代码，几乎零成本切换到本地 Gemini。

项目地址：https://github.com/xiscoxu/gemini-cli-sdk

### 核心能力

**1. 异步调用 + 流式响应**

```python
import asyncio
from gemini_cli_sdk import GeminiClient

async def analyze_factor(factor_desc: str):
    async with GeminiClient() as client:
        # 流式获取分析结果，实时看到思考过程
        print("AI 分析中: ", end="")
        async for chunk in await client.chat(
            f"分析这个 Alpha 因子的逻辑和潜在问题：{factor_desc}",
            stream=True
        ):
            print(chunk, end="", flush=True)

asyncio.run(analyze_factor("过去20天的动量因子，用收盘价/20日前收盘价"))
```

**2. 会话管理：保持上下文**

```python
async with GeminiClient() as client:
    session_id = client.create_session()

    # 第一轮：描述任务背景
    await client.chat("我在研究A股市场的反转因子", session_id)

    # 第二轮：AI 记得上下文
    response = await client.chat("帮我把这个因子转化为 Brain Alpha 表达式", session_id)
    print(response.content)
```

**3. 本地 OpenAI 兼容 API Server（v1.2.0 新增）**

```bash
# 安装 API 服务器依赖
pip install gemini-cli-sdk[api]

# 启动本地服务（默认端口 8000）
gemini-api-server
```

启动后，直接用 OpenAI SDK 调用：

```python
from openai import OpenAI

# 只需改一行：把 base_url 指向本地
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # 本地不需要 key
)

response = client.chat.completions.create(
    model="gemini",
    messages=[{"role": "user", "content": "分析这个 Alpha 因子的风险敞口"}]
)
print(response.choices[0].message.content)
```

## 量化场景实战

### 场景一：自然语言 → Alpha 表达式

在 Brain 平台写 Alpha 时，有时候有个模糊的想法但不确定怎么写表达式。可以这样用：

```python
async def idea_to_alpha(idea: str):
    async with GeminiClient() as client:
        session_id = client.create_session()

        # 给 AI 一些 Brain 平台的上下文
        await client.chat(
            "你是 WorldQuant Brain 平台的量化分析专家。"
            "Brain 使用类似 ts_mean(x, d)、rank(x)、zscore(x) 等函数。",
            session_id
        )

        response = await client.chat(
            f"把这个投资想法转化为 Brain Alpha 表达式并解释逻辑：{idea}",
            session_id
        )
        return response.content

idea = "买入近期成交量放大但价格没有上涨的股票"
alpha_expr = asyncio.run(idea_to_alpha(idea))
print(alpha_expr)
```

### 场景二：批量分析回测结果

```python
import asyncio
from gemini_cli_sdk import GeminiClient

backtest_results = [
    {"alpha": "ts_mean(returns, 20)", "sharpe": 0.8, "turnover": 0.45, "drawdown": -0.12},
    {"alpha": "rank(volume / ts_mean(volume, 5))", "sharpe": 1.2, "turnover": 0.78, "drawdown": -0.08},
    {"alpha": "zscore(close / open - 1)", "sharpe": 0.3, "turnover": 0.92, "drawdown": -0.21},
]

async def batch_analyze(results):
    async with GeminiClient() as client:
        tasks = []
        for r in results:
            prompt = (
                f"Alpha: {r['alpha']}\n"
                f"Sharpe: {r['sharpe']}, Turnover: {r['turnover']}, Max Drawdown: {r['drawdown']}\n"
                f"请给出改进建议（50字以内）"
            )
            tasks.append(client.one_shot(prompt))

        # 并发分析所有 Alpha
        responses = await asyncio.gather(*tasks)
        for r, resp in zip(results, responses):
            print(f"\n[{r['alpha']}]\n{resp.content}")

asyncio.run(batch_analyze(backtest_results))
```

## 快速上手（3步）

```bash
# 1. 安装 Gemini CLI（需要 Node.js 18+）
npm install -g @google/gemini-cli
gemini  # 首次运行，完成 Google 账号授权

# 2. 安装 SDK
pip install gemini-cli-sdk
# 如需 API Server：pip install gemini-cli-sdk[api]

# 3. 运行示例
python -c "
import asyncio
from gemini_cli_sdk import GeminiClient

async def main():
    async with GeminiClient() as client:
        r = await client.one_shot('用一句话解释什么是动量因子')
        print(r.content)

asyncio.run(main())
"
```

## 总结

| 特性 | 说明 |
|------|------|
| 费用 | Gemini CLI 个人免费，本地运行零 API 费用 |
| 兼容性 | 完全兼容 OpenAI SDK，LangChain 等工具无缝接入 |
| 隐私 | 数据不经第三方服务器（Gemini CLI 直连 Google） |
| 并发 | 内置进程池，支持高并发批量调用 |
| 流式 | 支持流式响应，实时获取长篇分析 |

项目开源地址：https://github.com/xiscoxu/gemini-cli-sdk
欢迎 Star 和反馈！

有在用 AI 辅助 Alpha 研究的朋友，欢迎在评论区分享你的工作流 👇
```

- [ ] **Step 2: 帖子输出完成**

帖子内容已在 Step 1 完整输出，用户可直接从对话中复制发布到 Brain 论坛。无需额外命令。
