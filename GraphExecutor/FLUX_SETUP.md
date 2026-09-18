# FLUX 图像生成集成指南

## 🎯 当前状态

✅ **已完成**:
- Qwen API 场景图生成
- 场景图可视化
- 边界框布局预览
- FLUX 生成模块已创建（`graphexecutor/flux_generator.py`）
- 后端 API 已集成生成功能

⚠️ **待启用**:
- FLUX 模型加载（需要安装 PyTorch）
- GPU 加速推理

## 📦 FLUX 模型位置

模型已存在于：`/home/hdd4/lpz/FLUX.1-dev2/`

包含文件：
- `flux1-dev.safetensors` (23GB) - 主模型
- `ae.safetensors` - 自动编码器
- `text_encoder/` - 文本编码器 1
- `text_encoder_2/` - 文本编码器 2
- `vae/` - VAE
- `transformer/` - Transformer

## 🔧 启用 FLUX 生成的步骤

### 1. 安装 PyTorch

```bash
cd /home/lipz/yigraphdiff/GraphExecutor
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base

# 安装 PyTorch (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 或者使用 CUDA 12.1
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 2. 安装 FLUX 依赖

```bash
pip install diffusers>=0.25.0 transformers>=4.36.0 accelerate>=0.25.0 sentencepiece
```

### 3. 重启服务

```bash
pkill -f "python app/main.py"
python app/main.py
```

### 4. 验证

访问 http://localhost:8888/api/v1/health

如果 GPU 可用，应该显示：
```json
{
  "gpu_available": true
}
```

## 📊 当前配置

**config.py**:
```python
MODEL_PATH = "/home/hdd4/lpz/FLUX.1-dev2"
DEVICE = "cuda:2"
DASHSCOPE_API_KEY = "sk-ws-H.PMXDRLL..."
```

## 🚀 使用方式

### 前端使用

1. 输入提示词："一位服务员在咖啡馆为两位顾客服务"
2. 点击"生成场景图" → 显示场景图和布局
3. 点击"生成图像" → 调用 FLUX 生成真实图像

### API 调用

```bash
# 1. 生成场景图和图像
curl -X POST http://localhost:8888/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一位服务员在咖啡馆为两位顾客服务",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 32,
    "guidance_scale": 3.5,
    "save_visualization": true
  }'

# 返回示例
{
  "task_id": "abc-123-def",
  "status": "processing",
  "image_url": null,  # 完成后会有
  "visualization_url": "/outputs/viz_abc-123.png",
  "scene_graph": {...}
}

# 2. 查询任务状态
curl http://localhost:8888/api/v1/task/abc-123-def

# 返回示例（完成后）
{
  "task_id": "abc-123-def",
  "status": "completed",
  "image_url": "/outputs/generated_abc-123-def.png",
  "image_path": "/home/lipz/.../outputs/generated_abc-123-def.png"
}
```

## 🎨 FLUX 生成流程

```
用户提示词
  ↓
Qwen API 解析 → 场景图（对象+关系）
  ↓
Token-Region 对齐
  ↓
边编译 + 时序调度
  ↓
语义亲和性矩阵
  ↓
GraphExecutor 控制器
  ↓
FLUX 推理（带注意力路由）
  ↓
生成图像
```

## 🔍 技术细节

### 控制模式

- `graph_executor`: 完整的 GraphExecutor 控制（默认）
- `layout_only`: 仅布局控制
- `layout_strong`: 强布局引导
- `none`: 无控制，标准 FLUX 生成

### 参数说明

- `num_inference_steps`: 推理步数（10-100，默认 32）
- `guidance_scale`: 引导强度（1.0-20.0，默认 3.5）
- `seed`: 随机种子（可选，用于复现）
- `bias_scale`: 注意力偏置强度（0.0-2.0，默认 0.5）

### 性能

- **模型大小**: 23GB
- **显存需求**: ~24GB（完整精度）或 ~12GB（bfloat16）
- **推理时间**: ~30-60秒/张（取决于步数和硬件）
- **推荐硬件**: RTX 3090 / A100 / H100

## ❌ 当前限制（torch 未安装时）

当前服务可以：
- ✅ 解析提示词生成场景图
- ✅ 显示对象和关系
- ✅ 生成布局可视化
- ✅ 导出 JSON

当前服务**不能**：
- ❌ 生成真实图像
- ❌ 使用 FLUX 模型
- ❌ GPU 加速

点击"生成图像"按钮会返回：
```
"message": "FLUX 模型未加载，仅生成布局图"
```

## 🐛 故障排查

### 问题：torch 未安装

```bash
[Service] FLUX 生成器不可用: No module named 'torch'
```

**解决**：安装 PyTorch（见上文步骤 1）

### 问题：GPU 不可用

```bash
"gpu_available": false
```

**检查**：
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### 问题：显存不足

```bash
RuntimeError: CUDA out of memory
```

**解决**：
1. 减少 batch size
2. 使用更小的分辨率
3. 使用 CPU 推理（慢很多）

### 问题：模型加载失败

```bash
[FLUX] 模型加载失败: ...
```

**检查**：
1. 模型路径是否正确
2. 模型文件是否完整
3. 是否有读取权限

## 📝 代码结构

```
GraphExecutor/
├── graphexecutor/
│   ├── flux_generator.py      # FLUX 生成模块（新增）
│   ├── vlm_layout.py           # Qwen VLM 集成
│   ├── graph_ir.py             # 场景图数据结构
│   └── visualization.py        # 可视化工具
├── app/
│   ├── api/routes.py           # API 路由（已更新）
│   └── services/graph_service.py # 业务逻辑（已更新）
└── config.py                   # 配置（已更新）
```

## 🚀 下一步

### 立即可做（无需 torch）

1. ✅ 使用 Qwen API 生成复杂场景图
2. ✅ 查看场景图可视化
3. ✅ 调整布局和关系
4. ✅ 导出 JSON 场景图

### 安装 PyTorch 后可做

1. 🔄 完整图像生成
2. 🔄 GraphExecutor 注意力控制
3. 🔄 多种控制模式对比
4. 🔄 批量生成和实验

## 📞 快速启用命令

```bash
# 一键安装所有依赖
cd /home/lipz/yigraphdiff/GraphExecutor
source ~/miniconda3/etc/profile.d/conda.sh && conda activate base
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# 重启服务
pkill -f "python app/main.py"
python app/main.py

# 测试
curl http://localhost:8888/api/v1/health
```

---

**当前服务地址**: http://localhost:8888/
**状态**: ✅ 运行中（场景图生成功能完整）
**FLUX 生成**: ⚠️ 待启用（需安装 PyTorch）
