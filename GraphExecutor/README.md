# GraphExecutor API 服务

基于场景图的图像生成服务，将 GraphDiff 的核心功能封装为 REST API 接口。

## 项目概述

GraphExecutor 是一个将自然语言描述转换为结构化场景图，并基于场景图生成图像的服务。场景图包含对象（节点）和它们之间的关系（边），提供精确的布局和语义控制。

## 功能特性

- **布局预测**: 从自然语言提示自动预测场景布局
- **场景图管理**: 创建、验证、导出和可视化场景图
- **类型化关系**: 支持空间、接触、注视、反射、光照等多种关系类型
- **可视化工具**: 生成边界框覆盖图和图结构可视化
- **RESTful API**: 完整的 HTTP API 接口供前端调用

## 项目结构

```
GraphExecutor/
├── app/                          # 应用层
│   ├── main.py                   # FastAPI 主应用
│   ├── api/
│   │   └── routes.py             # API 路由定义
│   ├── services/
│   │   └── graph_service.py      # 业务逻辑服务
│   └── models/
│       └── schemas.py            # 数据模型
├── graphexecutor/                # 核心模块
│   ├── __init__.py
│   ├── graph_ir.py               # 场景图数据结构
│   ├── vlm_layout.py             # VLM 布局预测
│   └── visualization.py          # 可视化工具
├── outputs/                      # 输出文件目录
├── config.py                     # 配置文件
├── requirements.txt              # Python 依赖
└── README.md                     # 本文件
```

## 安装

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 配置环境变量（可选）：

创建 `.env` 文件：

```env
# VLM API 配置（可选，用于自动布局预测）
DASHSCOPE_API_KEY=your_api_key_here
QWEN_API_KEY=your_api_key_here

# 服务配置
HOST=0.0.0.0
PORT=8000

# 设备配置
DEVICE=cuda  # 或 cpu
```

## 快速开始

### 启动服务

```bash
# 方式 1: 直接运行
python app/main.py

# 方式 2: 使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问：
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/v1/health

### API 使用示例

#### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

#### 2. 从提示预测布局

```bash
curl -X POST "http://localhost:8000/api/v1/predict-layout" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一位服务员在咖啡馆桌前为两位顾客服务，一个孩子望向窗外",
    "width": 1024,
    "height": 1024
  }'
```

#### 3. 验证场景图

```bash
curl -X POST "http://localhost:8000/api/v1/validate-scene-graph" \
  -H "Content-Type: application/json" \
  -d '{
    "high_level_description": "咖啡馆场景",
    "style_description": "摄影风格，自然光照",
    "background": "咖啡馆内部",
    "width": 1024,
    "height": 1024,
    "elements": [
      {
        "id": "waiter",
        "type": "object",
        "bbox": [100, 200, 300, 800],
        "desc": "穿着白色围裙的服务员"
      },
      {
        "id": "customers",
        "type": "object",
        "bbox": [400, 300, 700, 750],
        "desc": "坐在桌前的两位顾客"
      }
    ],
    "edges": [
      {
        "id": "serving",
        "source": "waiter",
        "target": "customers",
        "type": "serving",
        "strength": 0.85
      }
    ]
  }'
```

#### 4. 创建可视化

```bash
curl -X POST "http://localhost:8000/api/v1/visualize" \
  -H "Content-Type: application/json" \
  -d @scene_graph.json \
  --output visualization.png
```

#### 5. 生成图像

```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一位服务员在咖啡馆桌前为两位顾客服务",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 32,
    "guidance_scale": 3.5,
    "save_visualization": true
  }'
```

### Python 客户端示例

```python
import requests

# 基础 URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. 预测布局
response = requests.post(f"{BASE_URL}/predict-layout", json={
    "prompt": "一只红色的猫坐在蓝色的椅子上，旁边有一棵绿色的植物",
    "width": 1024,
    "height": 1024
})
scene_graph = response.json()
print(f"预测到 {len(scene_graph['elements'])} 个对象")

# 2. 创建可视化
response = requests.post(f"{BASE_URL}/visualize", json={
    "scene_graph": scene_graph,
    "visualization_type": "bbox_overlay",
    "show_labels": True
})
with open("visualization.png", "wb") as f:
    f.write(response.content)

# 3. 获取完整提示
response = requests.post(f"{BASE_URL}/get-prompt", json={
    "scene_graph": scene_graph,
    "mode": "full"
})
print(f"完整提示: {response.json()['prompt']}")

# 4. 生成图像
response = requests.post(f"{BASE_URL}/generate", json={
    "scene_graph": scene_graph,
    "num_inference_steps": 32,
    "save_visualization": True
})
task_info = response.json()
print(f"任务 ID: {task_info['task_id']}")
```

## 场景图格式

### 节点（对象）

每个节点代表场景中的一个对象：

```json
{
  "id": "unique_node_id",
  "type": "object",
  "bbox": [x1, y1, x2, y2],
  "desc": "对象的自然语言描述",
  "control_extend": 0.0
}
```

### 边（关系）

边定义对象之间的关系：

```json
{
  "id": "unique_edge_id",
  "source": "source_node_id",
  "target": "target_node_id",
  "type": "relation_type",
  "strength": 0.85,
  "direction": "source_to_target",
  "phase": "mid",
  "mode": "soft_bias"
}
```

### 关系类型

- **spatial**: 空间关系 - `spatial`, `left_of`, `right_of`, `above`, `below`, `near`, `next_to`
- **contact**: 接触关系 - `contact`, `serving`, `holding`, `placed_on`, `carrying`, `on`, `in`
- **gaze**: 注视关系 - `gaze_pointing`, `looks_at`, `points_to`, `pointing`, `watching`
- **reflection**: 反射关系 - `reflection`, `reflected_by`
- **lighting**: 光照关系 - `lighting`, `illuminates`, `casts_shadow`, `specular_highlight`
- **negative**: 负向关系 - `negative_attribute` (抑制属性混合)

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/predict-layout` | POST | 从提示预测布局 |
| `/api/v1/validate-scene-graph` | POST | 验证场景图 |
| `/api/v1/visualize` | POST | 创建可视化 |
| `/api/v1/export-scene-graph` | POST | 导出场景图 JSON |
| `/api/v1/get-prompt` | POST | 获取完整提示 |
| `/api/v1/generate` | POST | 生成图像 |
| `/api/v1/task/{task_id}` | GET | 获取任务状态 |

## 配置选项

编辑 `config.py` 或设置环境变量：

- `HOST`: 服务监听地址（默认: 0.0.0.0）
- `PORT`: 服务端口（默认: 8000）
- `DEVICE`: 计算设备（默认: cuda）
- `DEFAULT_WIDTH`: 默认画布宽度（默认: 1024）
- `DEFAULT_HEIGHT`: 默认画布高度（默认: 1024）
- `DASHSCOPE_API_KEY`: VLM API 密钥（可选）

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black .
isort .
```

## 限制和注意事项

1. **图像生成**: 当前实现提供了完整的场景图处理和可视化功能。完整的图像生成需要集成 FLUX 模型（需要大量计算资源）。

2. **VLM 布局预测**: 默认使用确定性网格布局。要使用智能布局预测，需要配置 VLM API 密钥。

3. **资源需求**: 如果要运行完整的图像生成，建议使用 GPU 并确保有足够的显存（建议 ≥ 24GB）。

## 故障排查

### 服务无法启动

- 检查端口是否被占用
- 确认所有依赖已安装：`pip install -r requirements.txt`
- 查看日志输出

### 可视化失败

- 确认 matplotlib 和 PIL 已正确安装
- 检查输出目录权限

### GPU 不可用

- 检查 CUDA 安装
- 确认 PyTorch 版本与 CUDA 版本匹配

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 参考

基于 GraphDiff 项目的核心功能实现。
