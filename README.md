# 制课生成 Agent

一个基于 `LangGraph + LangChain + FastAPI + Vue` 的制课生成系统。系统通过真实对话补全需求、接收资料、生成 Markdown 主稿，并在自动优化 + 人工审核闭环里迭代改稿。

## 根目录结构

- `apps/api/`: 后端 API 服务
- `frontend/`: 当前唯一有效的前端页面目录
- `apps/web/`: 预留目录，当前不作为运行入口
- `config/`: 根目录运行配置
- `prompts/`: 所有 prompt 文件
- `docs/`: 架构、接口、运维、产品文档
- `apps/api/pyproject.toml`: Python 依赖与项目元数据权威入口
- `requirements.txt`: 兼容性安装清单

## 启动方式

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
# 或者使用权威入口：
# pip install -e ./apps/api[dev]

cp .env.example .env
# 把真实 key 放到 .env.local，不要提交到 Git
# DEEPSEEK_API_KEY=你的key
uvicorn app.main:app --app-dir apps/api --reload

unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
uvicorn app.main:app --app-dir apps/api --reload


```

```bash
cd frontend
npm install
npm run generate:api
npm run dev
```

## 说明

- DeepSeek 是当前唯一主模型
- `config/llm.yaml` 是新的模型配置入口，后续切换 provider/model 优先改这里
- API key 建议放在项目根目录 `.env.local`
- prompt 统一放在 `prompts/deepseek/`
- API 地址默认跟随当前页面主机名，减少本地联调跨域问题
- OpenAPI 契约导出到 `docs/api/openapi.json`
- 前端类型通过 `frontend/src/generated/api.d.ts` 自动生成
- 所有系统文档统一放在 `docs/` 子目录
- LLM API 接入说明见 `docs/operations/llm-api-integration.md`
- V2 设计文档放在 `docs/redesign/`
