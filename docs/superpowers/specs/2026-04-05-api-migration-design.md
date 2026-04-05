# Design: Gemini CLI SDK API 功能迁移 + Brain 论坛分享帖

**Date:** 2026-04-05

## 概述

将 `gemini-cli-sdk` v1.2.0 的新功能（OpenAI 兼容 REST API 服务器模块）从本地开发目录迁移至 git 仓库，推送到远程，并在 WorldQuant Brain 论坛发布一篇面向量化研究员的技术分享帖。

---

## 一、迁移设计

### 新增内容

| 路径 | 说明 |
|------|------|
| `gemini_cli_sdk/api/__init__.py` | API 模块入口，暴露 FastAPI app |
| `gemini_cli_sdk/api/server.py` | FastAPI 服务器，OpenAI 兼容端点，速率限制 |
| `gemini_cli_sdk/api/config.py` | API 服务器配置（host/port/rate_limit 等） |
| `gemini_cli_sdk/api/models.py` | OpenAI 格式请求/响应数据模型 |
| `gemini_cli_sdk/api/openai_adapter.py` | Gemini SDK → OpenAI 格式适配层 |
| `gemini_cli_sdk/api/cli.py` | CLI 入口点（`gemini-api` 命令） |
| `examples/api_usage_example.py` | API 使用示例 |
| `API_QUICKSTART.md` | 快速上手指南 |

### 更新内容

| 文件 | 变更 |
|------|------|
| `gemini_cli_sdk/__init__.py` | 版本 1.0.5 → 1.2.0 |
| `requirements.txt` | 新增 fastapi, uvicorn, slowapi, python-multipart；pydantic 升至 v2 |
| `setup.py` | 新增 API 依赖组和 CLI entry point |
| `README.md` | 全面扩充（500→787行），新增 API Server 文档 |

### 跳过内容

- `gemini-cli-proxy-master/` — 参考实现，非 SDK 核心

---

## 二、帖子设计

### 平台
WorldQuant Brain 论坛

### 标题
用本地 Gemini CLI 搭建免费 AI 助手——量化研究员的 Alpha 开发提效实践

### 目标受众
Brain 平台量化研究员，有 Python 基础，关注 AI 辅助研究效率

### 结构

1. **背景痛点** — AI API 成本与速率限制是量化研究高频调用的瓶颈
2. **方案介绍** — Gemini CLI SDK：本地驱动，零 API 费用，OpenAI 兼容
3. **核心能力展示** — 异步调用、流式响应、本地 OpenAI API Server（附代码）
4. **量化场景示例** — 因子描述 → AI 生成 Alpha 表达式；批量回测结果分析
5. **快速上手** — 3 步安装
6. **总结 + 项目链接**

### 语言
中文为主，代码注释英文

---

## 三、执行步骤

1. 复制 `api/` 模块及新增文件到目标仓库
2. 更新差异文件（`__init__.py`, `requirements.txt`, `setup.py`, `README.md`）
3. git add + commit + push
4. 撰写并输出 Brain 论坛帖子内容
