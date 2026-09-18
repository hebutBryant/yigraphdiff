# GraphExecutor 项目总结

## 项目概述

已成功将 GraphDiff 的核心功能迁移到 `/home/lipz/yigraphdiff/GraphExecutor`，并创建了完整的 REST API 服务供前端调用。

## 项目结构

```
/home/lipz/yigraphdiff/GraphExecutor/
├── app/                              # 应用层
│   ├── __init__.py
│   ├── main.py                       # FastAPI 主应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                 # API 路由定义（8个端点）
│   ├── services/
│   │   ├── __init__.py
│   │   └── graph_service.py          # 核心业务逻辑服务
│   └── models/
│       ├── __init__.py
│       └── schemas.py                # Pydantic 数据模型
│
├── graphexecutor/                    # 核心模块（从 GraphDiff 迁移）
│   ├── __init__.py
│   ├── graph_ir.py                   # 场景图数据结构和验证
│   ├── vlm_layout.py                 # VLM 布局预测器
│   └── visualization.py              # 可视化工具
│
├── examples/                         # 示例文件
│   └── cafe_scene.json               # 咖啡馆场景示例
│
├── outputs/                          # 输出文件目录（自动创建）
│
├── config.py                         # 配置文件
├── requirements.txt                  # Python 依赖
├── .env.example                      # 环境变量模板
├── .gitignore                        # Git 忽略文件
├── README.md                         # 项目文档
├── start_service.sh                  # 服务启动脚本
├── test_core.py                      # 核心模块测试
└── test_api.py                       # API 测试脚本
```

## 核心功能

### 1. 场景图处理 (graphexecutor/graph_ir.py)
- **GraphNode**: 场景中的对象节点（包含 ID、类型、边界框、描述）
- **GraphEdge**: 对象之间的关系边（空间、接触、注视、反射、光照等）
- **SceneGraph**: 完整的场景图结构
- **load_scene_graph()**: 从 JSON 加载场景图
- **validate_scene_graph()**: 验证场景图有效性
- **build_full_prompt()**: 从场景图生成文本提示

### 2. 布局预测 (graphexecutor/vlm_layout.py)
- **VLMLayoutPredictor**: VLM 布局预测器类
- **predict_layout()**: 从文本提示预测场景布局
- 支持 API 密钥配置或使用确定性网格布局作为回退

### 3. 可视化 (graphexecutor/visualization.py)
- **draw_scene_graph_overlay()**: 绘制边界框覆盖图
- **visualize_graph_structure()**: 可视化图结构（节点和边）
- **create_visualization_grid()**: 创建组合网格视图
- **export_scene_graph_json()**: 导出场景图为 JSON

## REST API 接口

服务提供以下 8 个 API 端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/predict-layout` | POST | 从文本提示预测布局 |
| `/api/v1/validate-scene-graph` | POST | 验证和规范化场景图 |
| `/api/v1/visualize` | POST | 创建可视化图像 |
| `/api/v1/export-scene-graph` | POST | 导出场景图为 JSON |
| `/api/v1/get-prompt` | POST | 从场景图生成文本提示 |
| `/api/v1/generate` | POST | 创建图像生成任务 |
| `/api/v1/task/{task_id}` | GET | 查询任务状态 |

## 快速开始

### 1. 安装依赖

```bash
cd /home/lipz/yigraphdiff/GraphExecutor
pip install -r requirements.txt
```

### 2. 配置环境（可选）

```bash
cp .env.example .env
# 编辑 .env 文件，添加 API 密钥等配置
```

### 3. 启动服务

```bash
# 方式 1: 使用启动脚本
./start_service.sh

# 方式 2: 直接运行
python app/main.py

# 方式 3: 使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **根路径**: http://localhost:8000/

### 5. 测试 API

```bash
# 测试核心模块（不需要启动服务）
python test_core.py

# 测试 API（需要先启动服务）
python test_api.py
```

## 使用示例

### Python 客户端

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. 健康检查
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. 从提示预测布局
response = requests.post(f"{BASE_URL}/predict-layout", json={
    "prompt": "一只猫坐在椅子上，旁边有一棵植物",
    "width": 1024,
    "height": 1024
})
scene_graph = response.json()

# 3. 创建可视化
response = requests.post(f"{BASE_URL}/visualize", json={
    "scene_graph": scene_graph,
    "visualization_type": "bbox_overlay",
    "show_labels": True
})
with open("visualization.png", "wb") as f:
    f.write(response.content)

# 4. 生成图像任务
response = requests.post(f"{BASE_URL}/generate", json={
    "scene_graph": scene_graph,
    "num_inference_steps": 32,
    "save_visualization": True
})
task_info = response.json()
print(f"任务 ID: {task_info['task_id']}")
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 预测布局
curl -X POST "http://localhost:8000/api/v1/predict-layout" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "一只猫坐在椅子上", "width": 1024, "height": 1024}'

# 创建可视化
curl -X POST "http://localhost:8000/api/v1/visualize" \
  -H "Content-Type: application/json" \
  -d @examples/cafe_scene.json \
  --output visualization.png
```

## 场景图格式

### 完整示例

```json
{
  "high_level_description": "场景的高层描述",
  "style_description": "摄影风格，光照描述",
  "background": "背景描述",
  "width": 1024,
  "height": 1024,
  "elements": [
    {
      "id": "object1",
      "type": "object",
      "bbox": [x1, y1, x2, y2],
      "desc": "对象描述"
    }
  ],
  "edges": [
    {
      "id": "edge1",
      "source": "object1",
      "target": "object2",
      "type": "spatial",
      "strength": 0.85,
      "direction": "source_to_target",
      "phase": "mid",
      "mode": "soft_bias"
    }
  ]
}
```

### 支持的边类型

- **spatial**: `spatial`, `left_of`, `right_of`, `above`, `below`, `near`, `next_to`
- **contact**: `contact`, `serving`, `holding`, `placed_on`, `carrying`, `on`, `in`
- **gaze**: `gaze_pointing`, `looks_at`, `points_to`, `pointing`, `watching`
- **reflection**: `reflection`, `reflected_by`
- **lighting**: `lighting`, `illuminates`, `casts_shadow`, `specular_highlight`
- **negative**: `negative_attribute`

## 技术栈

- **Web 框架**: FastAPI 0.104+
- **数据验证**: Pydantic 2.5+
- **可视化**: Matplotlib, Pillow, NetworkX
- **深度学习**: PyTorch (可选，用于完整图像生成)
- **服务器**: Uvicorn

## 配置选项

在 `config.py` 或 `.env` 文件中配置：

```python
HOST = "0.0.0.0"              # 服务地址
PORT = 8000                    # 服务端口
DEVICE = "cuda"                # 计算设备
DEFAULT_WIDTH = 1024           # 默认画布宽度
DEFAULT_HEIGHT = 1024          # 默认画布高度
DASHSCOPE_API_KEY = ""         # VLM API 密钥
MODEL_PATH = ""                # FLUX 模型路径（用于完整图像生成）
```

## 前端集成

### JavaScript/TypeScript 示例

```javascript
const API_BASE = 'http://localhost:8000/api/v1';

// 预测布局
async function predictLayout(prompt, width = 1024, height = 1024) {
  const response = await fetch(`${API_BASE}/predict-layout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, width, height })
  });
  return await response.json();
}

// 创建可视化
async function visualize(sceneGraph, type = 'bbox_overlay') {
  const response = await fetch(`${API_BASE}/visualize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scene_graph: sceneGraph,
      visualization_type: type,
      show_labels: true
    })
  });
  return await response.blob();
}

// 使用示例
const sceneGraph = await predictLayout('一只猫坐在椅子上');
const imageBlob = await visualize(sceneGraph);
const imageUrl = URL.createObjectURL(imageBlob);
document.getElementById('image').src = imageUrl;
```

## 注意事项

1. **完整图像生成**: 当前实现提供了完整的场景图处理和可视化功能。完整的图像生成需要集成 FLUX 模型（需要大量 GPU 资源）。

2. **VLM 布局预测**: 默认使用确定性网格布局。要使用智能布局预测，需要配置 VLM API 密钥。

3. **资源需求**: 
   - 基本功能：CPU + 2GB 内存
   - 完整图像生成：GPU (≥24GB 显存) + FLUX 模型

4. **CORS**: 服务已配置允许跨域访问（生产环境应限制具体域名）。

## 扩展功能

如需集成完整的图像生成功能，需要：

1. 从 `/home/lipz/GraphDiff/graphexecutor/` 复制以下模块：
   - `attention_routing.py`
   - `attention_hook.py`
   - `graph_scheduler.py`
   - `edge_compiler.py`
   - `token_region_aligner.py`
   - `semantic_affinity.py`

2. 安装 FLUX 模型和相关依赖

3. 在 `graph_service.py` 中实现完整的生成逻辑

## 故障排查

### 服务无法启动
```bash
# 检查端口占用
lsof -i :8000

# 检查依赖
pip install -r requirements.txt

# 查看详细日志
python app/main.py
```

### 导入错误
```bash
# 确保在项目根目录
cd /home/lipz/yigraphdiff/GraphExecutor

# 重新安装依赖
pip install -r requirements.txt
```

## 项目状态

✅ **已完成**:
- 核心场景图数据结构
- VLM 布局预测（带回退）
- 可视化工具（边界框、图结构）
- 完整的 REST API 服务
- 数据验证和错误处理
- API 文档（自动生成）
- 测试脚本和示例

🔄 **可选扩展**:
- 完整的 FLUX 图像生成集成
- 数据库持久化
- 任务队列和异步处理
- 用户认证和授权
- 更多可视化选项

## 联系和支持

- 项目路径: `/home/lipz/yigraphdiff/GraphExecutor`
- 源代码: `/home/lipz/GraphDiff`
- 文档: `README.md`
- API 文档: http://localhost:8000/docs
