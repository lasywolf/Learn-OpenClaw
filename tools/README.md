# Tools - 工具系统

`tools` 目录提供了项目的工具调用能力，包含：

- 内置工具定义（`tools/builtins/`）
- 工具调用解析与执行（`tools/executor.py`）
- 对外统一入口（`tools/__init__.py`）
- 演示级快捷函数（`chat_with_tools`）

## 目录结构

```text
tools/
├── __init__.py          # 对外入口：get_tools / execute_tool / ToolExecutor
├── executor.py          # 解析并执行 LLM tool_calls
├── builtins/
│   ├── __init__.py
│   ├── tool_def.py      # Tool 类与 get_builtin_tools()
│   ├── read.py
│   ├── write.py
│   ├── edit.py
│   ├── bash.py
│   ├── grep.py
│   ├── find.py
│   ├── ls.py
│   └── search.py
└── skill_loader.py
```

## 内置工具

当前默认内置工具（由 `get_builtin_tools()` 返回）：

- `read`: 读取文件内容
- `write`: 写文件
- `edit`: 基于文本替换编辑文件
- `bash`: 执行命令
- `grep`: 内容搜索
- `find`: 按模式查找文件
- `ls`: 列目录
- `search`: 联网搜索（DuckDuckGo）

> `search` 依赖 `ddgs`。如果环境里没有该依赖，导入 `tools` 时会报错，需要先安装。

## 核心用法

### 1) 获取工具列表（给 LLM 注册 tools）

```python
from tools import get_tools

tools = get_tools()
llm_tools = [t.to_llm_format() for t in tools]
```

### 2) 执行单个工具

```python
from tools import execute_tool

result = execute_tool("ls", {"path": "."})
print(result)
```

### 3) 使用执行器处理 tool_calls

```python
from tools import ToolExecutor

executor = ToolExecutor()
tool_calls = executor.parse_tool_calls(assistant_message)
results = executor.execute_all(tool_calls)
messages.extend([r.to_message() for r in results])
```

### 4) 演示函数（非生产级）

```python
from tools import chat_with_tools

response = chat_with_tools("列出 tools 目录")
print(response)
```

`chat_with_tools()` 是规则驱动的演示函数，不会调用真实 LLM API。真实对话示例请参考 `examples/chatbot_with_tools/`。

## 执行流程（OpenAI `tool_calls`）

```mermaid
flowchart LR
    A[assistant message] --> B[parse_tool_calls]
    B --> C[ToolCall 列表]
    C --> D[execute_all]
    D --> E[ToolResult 列表]
    E --> F[to_message 写回对话历史]
```

## 说明

- `ToolExecutor.parse_tool_calls()` 当前只解析 OpenAI 风格的 `message.tool_calls`
- 工具名查找使用字典映射（`tool_map`），更直观
- 新增工具时，需在 `tools/builtins/tool_def.py` 的 `get_builtin_tools()` 中注册
- 运行示例建议使用 `uv run`，例如：`uv run examples/chatbot_with_tools/main.py`
