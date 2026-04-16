# LLM API 接入说明

这份文档专门说明两件事：

1. 真实 API key 应该放在哪里
2. 这套代码是从哪里读取 key、从哪里真正调用大模型的

## 先说结论

- 不要把真实 key 写进 Git 仓库
- 不要把真实 key 写进 `.env.example`
- 建议把真实 key 放在项目根目录的 `.env.local`
- 当前项目默认接的是 `DeepSeek`

推荐做法：

```bash
cd /Users/wuzujia/Downloads/整体/course-generation-agent
cp .env.example .env.local
```

然后只在 `.env.local` 里填写真实值：

```env
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

## 代码从哪里读取 API key

### 1. 环境变量入口

项目配置在：

- `apps/api/app/core/settings.py`

这里定义了：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `LLM_CONFIG_FILE`

关键点：

- `SettingsConfigDict` 会自动读取根目录下的 `.env.local` 和 `.env`
- 读取顺序在代码里已经写好，优先使用本地环境配置

对应位置：

- `apps/api/app/core/settings.py`

## 2. 模型配置入口

模型配置文件在：

- `config/llm.yaml`

当前默认配置是：

- provider: `deepseek`
- chat model: `deepseek-chat`
- review model: `deepseek-chat`

如果以后你想改模型名，优先改这里。

## 3. 真正组装模型客户端的地方

模型客户端在：

- `apps/api/app/llm/deepseek_client.py`

这个文件负责：

- 读取 `Settings`
- 从环境变量或 `.env.local` 解析 `DEEPSEEK_API_KEY`
- 组装 `ChatOpenAI(...)`
- 决定当前是否允许使用远程 LLM

关键方法：

- `can_use_remote_llm()`
  作用：判断现在有没有真实可用的远程模型

- `_resolve_api_key(...)`
  作用：真正解析 API key

- `_build_chat_model(...)`
  作用：构造实际的模型请求客户端

如果你想排查“为什么没走大模型”，先看这里。

## 哪些功能会实际调用大模型

### 1. 生成系列课框架

位置：

- `apps/api/app/llm/deepseek_client.py`
- 方法：`stream_series_framework_markdown(...)`

作用：

- 根据用户想法和结构化问答，生成 `series_framework.md`

### 2. 单课 / 其他步骤生成

位置：

- `apps/api/app/llm/deepseek_client.py`
- 方法：`stream_step_markdown(...)`
- 方法：`stream_markdown(...)`

### 3. 自动点评与评分

位置：

- `apps/api/app/llm/deepseek_client.py`
- 方法：`review_markdown(...)`

### 4. 系列课的评分 Agent / 决策 Agent

位置：

- `apps/api/app/series/decision_scoring.py`

这里会做三层事情：

- 本地规则和本地模型评分
- 大模型特征提取
- 大模型决策打分与修改建议

关键函数：

- `score_series_framework_markdown(...)`
- `_extract_features_with_llm(...)`
- `_generate_review_with_llm(...)`
- `_evaluate_decision_agent_with_llm(...)`

## 哪些地方不会调用大模型

这些通常不是 LLM 阶段：

- 前端页面渲染
- 文件上传
- `.md/.docx/.doc` 解析
- 系列课结构化问答的固定题目文案
- 问答流程切题本身

说明：

- 现在系列课 `A/B/C/D` 结构化问答阶段，已经改成优先走本地快速逻辑，不再为每一题等待远程模型
- 真正耗时的大模型阶段主要在“生成框架 / 评分 / 自动改稿”

## 如果你想换成别的 API 提供方，改哪里

### 最小改法

如果新提供方兼容 OpenAI 风格接口，可以只改：

- `.env.local`
  - `DEEPSEEK_API_KEY`
  - `DEEPSEEK_BASE_URL`

以及：

- `config/llm.yaml`
  - `model`

前提是：

- 新服务兼容 `ChatOpenAI` 的调用方式

### 更完整的改法

如果你想正式支持一个新的 provider，建议改这几处：

1. `config/llm.yaml`
   定义新的 provider 配置

2. `apps/api/app/core/schemas.py`
   如果需要，扩展 `LLMProviderConfig`

3. `apps/api/app/llm/deepseek_client.py`
   把当前这个客户端抽象成更通用的 provider client

## 如何确认当前有没有真的接上大模型

最可靠的排查方式是看这三个地方：

### 1. 本地配置是否存在

检查项目根目录：

```bash
ls -la .env.local
```

### 2. 代码判断是否允许远程调用

可以在虚拟环境里执行：

```bash
source .venv/bin/activate
python - <<'PY'
from app.core.settings import get_settings
from app.llm.deepseek_client import DeepSeekClient

s = get_settings()
client = DeepSeekClient(s)
print("deepseek_api_key_present =", bool(s.deepseek_api_key))
print("can_use_remote_llm =", client.can_use_remote_llm())
PY
```

### 3. 看后端日志

如果真的用了远程模型，通常会看到类似：

```text
HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
```

## 安全提醒

- `.env.local` 不要提交到 Git
- 不要把真实 key 写进文档、截图、提交记录
- 如果你怀疑 key 已经泄露，优先去服务商后台重置

## 相关文件速查

- 配置读取：`apps/api/app/core/settings.py`
- 模型配置：`config/llm.yaml`
- 模型客户端：`apps/api/app/llm/deepseek_client.py`
- 系列课评分与决策：`apps/api/app/series/decision_scoring.py`
- 主工作流：`apps/api/app/workflows/course_graph.py`
- 示例环境变量：`.env.example`
