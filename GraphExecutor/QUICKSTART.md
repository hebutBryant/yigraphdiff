# GraphExecutor 快速入门指南

## 1. 安装依赖

```bash
cd /home/lipz/yigraphdiff/GraphExecutor
pip install -r requirements.txt
```

如果遇到依赖问题，可以单独安装：

```bash
pip install fastapi uvicorn pydantic pillow matplotlib networkx requests python-dotenv
```

## 2. 启动服务

```bash
# 方式 1: 使用启动脚本（推荐）
chmod +x start_service.sh
./start_service.sh

# 方式 2: 直接运行
python app/main.py

# 方式 3: 使用 uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后会显示：
```
GraphExecutor API 服务启动
配置信息:
  - 输出目录: /home/lipz/yigraphdiff/GraphExecutor/outputs
  - 默认画布尺寸: 1024x1024
  - GPU 可用: cuda
API 文档: http://0.0.0.0:8000/docs
```

## 3. 访问 API 文档

打开浏览器访问：
- **交互式文档**: http://localhost:8000/docs
- **备用文档**: http://localhost:8000/redoc

## 4. 测试 API

### 方式 1: 在浏览器中测试

访问 http://localhost:8000/docs，可以直接在页面上测试所有 API。

### 方式 2: 使用测试脚本

```bash
# 先启动服务，然后在另一个终端运行：
python test_api.py
```

### 方式 3: 使用 cURL

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 预测布局
curl -X POST "http://localhost:8000/api/v1/predict-layout" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只红色的猫坐在蓝色的椅子上",
    "width": 1024,
    "height": 1024
  }'
```

## 5. 核心功能演示

### A. 从文本提示预测布局

```python
import requests

response = requests.post("http://localhost:8000/api/v1/predict-layout", json={
    "prompt": "一位服务员在咖啡馆为两位顾客服务，一个孩子望向窗外",
    "width": 1024,
    "height": 1024
})

scene_graph = response.json()
print(f"预测到 {len(scene_graph['elements'])} 个对象")
```

### B. 创建可视化

```python
response = requests.post("http://localhost:8000/api/v1/visualize", json={
    "scene_graph": scene_graph,
    "visualization_type": "bbox_overlay",
    "show_labels": True
})

with open("visualization.png", "wb") as f:
    f.write(response.content)
print("可视化已保存")
```

### C. 使用预定义场景图

```python
# 使用示例场景图
with open("examples/cafe_scene.json", "r") as f:
    cafe_scene = json.load(f)

response = requests.post("http://localhost:8000/api/v1/validate-scene-graph", 
                        json=cafe_scene)
validated = response.json()
print(f"场景图验证成功: {len(validated['elements'])} 个对象, {len(validated['edges'])} 条边")
```

## 6. 前端集成示例

### JavaScript/Fetch API

```javascript
// 预测布局
async function predictLayout(prompt) {
  const response = await fetch('http://localhost:8000/api/v1/predict-layout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: prompt,
      width: 1024,
      height: 1024
    })
  });
  return await response.json();
}

// 创建可视化
async function visualize(sceneGraph) {
  const response = await fetch('http://localhost:8000/api/v1/visualize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scene_graph: sceneGraph,
      visualization_type: 'bbox_overlay',
      show_labels: true
    })
  });
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

// 使用
const sceneGraph = await predictLayout('一只猫坐在椅子上');
const imageUrl = await visualize(sceneGraph);
document.getElementById('result').src = imageUrl;
```

### Axios

```javascript
import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
});

// 预测布局
const { data: sceneGraph } = await API.post('/predict-layout', {
  prompt: '一只猫坐在椅子上',
  width: 1024,
  height: 1024
});

// 可视化
const { data: imageBlob } = await API.post('/visualize', {
  scene_graph: sceneGraph,
  visualization_type: 'bbox_overlay'
}, {
  responseType: 'blob'
});
```

## 7. API 端点快速参考

| 端点 | 功能 | 请求体示例 |
|------|------|-----------|
| `GET /api/v1/health` | 健康检查 | 无 |
| `POST /api/v1/predict-layout` | 预测布局 | `{"prompt": "...", "width": 1024, "height": 1024}` |
| `POST /api/v1/validate-scene-graph` | 验证场景图 | 完整场景图对象 |
| `POST /api/v1/visualize` | 创建可视化 | `{"scene_graph": {...}, "visualization_type": "bbox_overlay"}` |
| `POST /api/v1/get-prompt` | 获取提示 | 场景图对象 |
| `POST /api/v1/generate` | 生成任务 | `{"prompt": "..." or "scene_graph": {...}}` |
| `GET /api/v1/task/{id}` | 任务状态 | 无 |

## 8. 故障排查

### 端口被占用
```bash
# 查看占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
PORT=8001 python app/main.py
```

### 依赖缺失
```bash
# 查看具体缺失什么
python -c "import fastapi, uvicorn, pydantic"

# 重新安装所有依赖
pip install -r requirements.txt --force-reinstall
```

### 可视化失败
```bash
# 确保安装了 matplotlib 和 pillow
pip install matplotlib pillow networkx

# 如果是无头服务器，设置后端
export MPLBACKEND=Agg
python app/main.py
```

## 9. 生产部署建议

### 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用 Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app/main.py"]
```

## 10. 下一步

- 查看完整文档: `README.md`
- 项目总结: `PROJECT_SUMMARY.md`
- 测试核心功能: `python test_core.py`
- 浏览示例: `examples/cafe_scene.json`

## 常见问题

**Q: 可以离线运行吗？**
A: 是的，默认使用确定性布局，无需 API 密钥。

**Q: 如何使用智能布局预测？**
A: 在 `.env` 文件中配置 `DASHSCOPE_API_KEY` 或 `QWEN_API_KEY`。

**Q: 能生成真实图像吗？**
A: 当前提供场景图处理和可视化。完整图像生成需集成 FLUX 模型。

**Q: 支持什么图像尺寸？**
A: 256-2048 像素，默认 1024×1024。

**Q: 如何添加自定义关系类型？**
A: 编辑 `graphexecutor/graph_ir.py`，添加到相应的类型列表中。
