# GraphExecutor 前端使用指南

## 🎉 前端已完成并运行！

前端已经创建完成，可以通过浏览器访问使用。

---

## 🚀 快速开始

### 1. 启动服务

```bash
cd /home/lipz/yigraphdiff/GraphExecutor
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base
python app/main.py
```

### 2. 访问前端

打开浏览器访问：
- **前端页面**: http://localhost:8888/
- **API 文档**: http://localhost:8888/docs
- **健康检查**: http://localhost:8888/api/v1/health

---

## 📱 前端功能

### 主要功能

1. **输入复杂提示词**
   - 在左侧输入框中输入场景描述
   - 例如："一位服务员在咖啡馆的桌前为两位顾客上菜，一个孩子望向窗外"
   - 支持中英文

2. **生成场景图**
   - 点击"生成场景图"按钮
   - 系统自动解析提示词，识别对象和关系
   - 生成结构化的场景图

3. **查看多种视图**
   - **场景图**: 可视化的图结构，显示对象节点和关系边
   - **布局/图像**: 边界框布局预览（连接 FLUX 后显示生成图像）
   - **边界框预览**: HTML 渲染的对象位置预览
   - **明细**: 详细的节点和边信息列表

4. **调整参数**
   - 画布尺寸（宽度/高度）
   - 推理步数
   - 引导强度
   - 布局图类型（边界框叠加/图结构/组合网格）

5. **其他操作**
   - 生成图像（需要 FLUX 模型）
   - 示例提示词快速填充
   - 导出场景图 JSON

---

## 🎨 界面说明

### 左侧控制面板

- **复杂提示词**: 输入场景描述
- **宽度/高度**: 设置画布尺寸（256-2048px）
- **推理步数**: 图像生成步数（10-100）
- **引导强度**: 提示词引导强度（1.0-20.0）
- **布局图类型**: 选择可视化样式

### 右侧显示区域

#### 场景图标签页
- SVG 渲染的交互式图
- 节点：圆形显示对象
- 边：带箭头的线条显示关系
- 图例：颜色说明不同关系类型
  - 🔵 蓝色 - 空间关系
  - 🟢 绿色 - 接触关系
  - 🟡 黄色 - 注视关系
  - 🟣 紫色 - 反射关系
  - 🟠 橙色 - 光照关系
  - 🔴 红色虚线 - 负向关系

#### 布局/图像标签页
- 显示后端渲染的布局图（matplotlib）
- 连接 FLUX 模型后显示生成的真实图像

#### 边界框预览标签页
- HTML 渲染的彩色边界框
- 每个对象用不同颜色区分
- 标签显示对象 ID

#### 明细标签页
- 对象节点列表：ID、类型、描述、边界框坐标
- 关系边列表：源节点、目标节点、类型、参数

---

## 💡 使用技巧

### 1. 提示词编写

**好的提示词示例**：
```
一位服务员在咖啡馆的桌前为两位顾客上菜，一个孩子望向窗外
a red car parked next to a blue bicycle under a large tree
a woman reading a book on a bench while a dog sits beside her
```

**提示词要点**：
- 明确描述多个对象
- 说明对象之间的关系（空间位置、交互）
- 包含场景背景信息
- 越详细越好，但保持自然语言

### 2. 快捷键

- **Ctrl/Cmd + Enter**: 在提示词输入框中快速提交

### 3. 调试

- 打开浏览器开发者工具（F12）查看网络请求
- 后端日志：`tail -f /tmp/graphexecutor.log`
- 检查 outputs 目录查看生成的文件

---

## 🔧 技术细节

### 前端架构

```
frontend/
├── index.html    # 主页面（98 行）
├── style.css     # 样式表（153 行）
└── app.js        # 应用逻辑（403 行）
```

### 技术栈

- **纯 JavaScript**: 无需框架，原生 DOM 操作
- **SVG 渲染**: 场景图可视化
- **Fetch API**: 异步调用后端 REST API
- **响应式设计**: 适配不同屏幕尺寸

### API 调用流程

```
输入提示词
    ↓
POST /api/v1/predict-layout
    ↓
返回 SceneGraphOutput
    ↓
渲染场景图 (SVG)
    ↓
POST /api/v1/visualize → 获取布局图
    ↓
显示结果
```

---

## 🎯 支持的关系类型

### 空间关系 (spatial)
- `spatial`, `left_of`, `right_of`, `above`, `below`, `near`, `next_to`
- 颜色：蓝色 `#38bdf8`

### 接触关系 (contact)
- `contact`, `serving`, `holding`, `placed_on`, `carrying`, `on`, `in`
- 颜色：绿色 `#34d399`

### 注视关系 (gaze)
- `gaze_pointing`, `looks_at`, `points_to`, `pointing`, `watching`
- 颜色：黄色 `#fbbf24`

### 反射关系 (reflection)
- `reflection`, `reflected_by`
- 颜色：紫色 `#a78bfa`

### 光照关系 (lighting)
- `lighting`, `illuminates`, `casts_shadow`, `specular_highlight`
- 颜色：橙色 `#fb923c`

### 负向关系 (negative)
- `negative_attribute` - 抑制属性混合
- 颜色：红色 `#f87171`，虚线显示

---

## 🐛 故障排查

### 前端无法加载

```bash
# 检查服务是否运行
curl http://localhost:8888/api/v1/health

# 检查前端文件是否存在
ls -la frontend/

# 重启服务
pkill -f "python app/main.py"
python app/main.py
```

### API 调用失败

- 检查浏览器控制台错误信息
- 确认后端服务正常运行
- 检查 CORS 设置（已配置允许所有来源）

### 布局图不显示

- 检查 matplotlib 是否安装：`pip install matplotlib pillow`
- 查看后端日志错误信息
- 尝试切换布局图类型

---

## 📊 当前状态

✅ **已完成**:
- 前端页面（HTML/CSS/JS）
- 场景图 SVG 可视化
- 边界框预览
- 明细信息显示
- API 集成
- 健康检查
- 示例提示词
- JSON 导出

⚠️ **待完成**（可选）:
- FLUX 模型集成（完整图像生成）
- 高级编辑功能（手动调整节点/边）
- 实时预览更新
- 更多可视化选项

---

## 🔗 相关链接

- **项目目录**: `/home/lipz/yigraphdiff/GraphExecutor`
- **前端文件**: `/home/lipz/yigraphdiff/GraphExecutor/frontend/`
- **API 文档**: http://localhost:8888/docs
- **后端代码**: `/home/lipz/yigraphdiff/GraphExecutor/app/`

---

## 📝 示例会话

1. 打开 http://localhost:8888/
2. 输入："一位服务员在咖啡馆的桌前为两位顾客上菜，一个孩子望向窗外"
3. 点击"生成场景图"
4. 查看场景图：显示服务员、顾客、桌子、孩子、窗户等节点及其关系
5. 切换到"布局/图像"标签：查看边界框布局
6. 切换到"明细"标签：查看详细信息
7. 点击"导出 JSON"：下载场景图 JSON 文件

---

**前端已就绪！现在可以开始使用了！** 🎉

访问 http://localhost:8888/ 体验完整功能。
