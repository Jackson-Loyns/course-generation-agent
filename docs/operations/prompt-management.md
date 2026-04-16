# Prompt Management

## Principle

- 所有 prompt 统一存放在根目录 `prompts/`
- 代码里只做变量注入，不直接写长 prompt 文本
- `prompts/prompt_catalog.yaml` 是唯一索引入口
- 每次模型调用前，通过 `PromptRegistry` 用 `prompt_id` 加载并渲染 prompt

## Injection Flow

1. 通过 `prompt_id` 在 `prompts/prompt_catalog.yaml` 中解析目标 prompt
2. 从 catalog 指向的 Markdown 文件读取模板
3. 用运行时上下文填充变量
4. 将渲染后的 prompt 传给 DeepSeek 客户端

## Benefits

- prompt 可以独立版本管理
- prompt 的 mode / step / purpose 能在 catalog 中直接看清
- debug 时可以直接查看 prompt 文件
- 不同模型后续可以按目录扩展
