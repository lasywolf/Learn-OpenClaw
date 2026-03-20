# Examples - 示例代码

本目录包含使用 PocketFlow 框架的各种示例。

## 目录结构

```
examples/
├── chatbot/              # 简单对话机器人
├── chatbot_with_tools/   # 带工具调用的对话机器人
└── workflow/             # 工作流示例
```

## 示例说明

### 1. Chatbot - 简单对话机器人

基础对话机器人，演示简单的 Node 和 Flow 使用。

```bash
python examples/chatbot/main.py
```

**流程图:**
```mermaid
flowchart LR
    User[用户输入] --> Chat[ChatNode]
    Chat --> Output[OutputNode]
    Output --> User
```

---

### 2. Chatbot with Tools - 带工具调用的对话机器人

演示如何让 LLM 调用工具（如 ls, read 等）并获取结果。

```bash
python examples/chatbot_with_tools/main.py
```

**流程图:**
```mermaid
flowchart TD
    User[用户输入] --> Chat1[ChatNode]
    Chat1 -->|tool_calls| Tool[ToolCallNode]
    Tool -->|tool result| Chat2[ChatNode]
    Chat2 --> Output[OutputNode]
    Output --> User

    style Tool fill:#f9f,stroke:#333,stroke-width:2px
```

---

### 3. Workflow - 工作流示例

演示多节点协作的工作流模式。

```bash
python examples/workflow/main.py
```

**搜索工作流:**

```mermaid
flowchart LR
    Query[QueryNode<br/>接收查询] -->|search| Search[SearchNode<br/>执行搜索]
    Search -->|summarize| Summary[SummarizeNode<br/>生成摘要]
    Summary --> Result[最终结果]

    style Query fill:#e1f5ff,stroke:#333
    style Search fill:#fff3e0,stroke:#333
    style Summary fill:#e8f5e9,stroke:#333
```

**工作流程说明:**
1. **QueryNode**: 接收用户查询，决定路由
2. **SearchNode**: 执行搜索，获取结果
3. **SummarizeNode**: 基于搜索结果生成摘要

---

## Node 核心概念

### 基本 Node

```python
from core.node import Node

class MyNode(Node):
    def exec(self, payload):
        # 处理逻辑
        result = process(payload)
        # 返回 (action, result)
        return "default", result
```

### 节点连接

```mermaid
flowchart LR
    A[Node A] -->|action1| B[Node B]
    A -->|action2| C[Node C]
    B -->|default| D[Node D]
```

```python
# 代码实现
node_a - "action1" >> node_b
node_a - "action2" >> node_c
node_b >> node_d
```

### Batch Node

```mermaid
flowchart LR
    Input[输入列表<br/>[a,b,c]] --> Batch[BatchNode]
    Batch -->|串行处理| R1[结果1]
    Batch -->|串行处理| R2[结果2]
    Batch -->|串行处理| R3[结果3]
```

### Parallel Batch Node

```mermaid
flowchart LR
    Input[输入列表<br/>[a,b,c]] --> Parallel[ParallelBatchNode]
    Parallel -->|并行| R1[结果1]
    Parallel -->|并行| R2[结果2]
    Parallel -->|并行| R3[结果3]
```

---

## 运行环境

所有示例需要设置 OpenAI API Key:

```bash
export OPENAI_API_KEY=your_key_here
```

或者使用其他支持的模型（如 Anthropic）。
