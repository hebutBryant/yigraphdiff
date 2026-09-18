# GraphExecutor

复杂提示词 → 场景图（对象 + 关系）→ FLUX 图像生成。

输入一段自然语言，系统用 Qwen VLM 解析出结构化场景图（对象、边界框、typed 关系边），
在网页上交互式可视化，并可调用本地 FLUX 模型生成图像。

---

## 功能

- **场景图预测**：Qwen VLM 把复杂提示词解析成对象 + typed 关系边
- **交互式可视化**：SVG 场景图、边界框预览、节点/边明细
- **图像生成**：本地 FLUX.1-dev 生成图像（异步任务 + 前端轮询）
- **纯前端**：单页应用，由 FastAPI 直接托管，无需额外构建

---

## 一键部署 + 运行

```bash
cd /home/lipz/yigraphdiff/GraphExecutor
bash deploy.sh
```

`deploy.sh` 会自动完成：检查 GraphAgent 环境 → 补装缺失依赖（dotenv 等）→
校验 torch / FluxPipeline 可用 → 在 8888 端口启动服务。

启动后打开：

- 前端页面： http://localhost:8888/
- API 文档（Swagger）： http://localhost:8888/docs
- 健康检查： http://localhost:8888/api/v1/health

> 若只想启动（环境已就绪），直接： `bash run_graphagent.sh`

---

## 配置

运行参数由 `config.py` 读取，全部支持用环境变量或 `.env` 覆盖。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MODEL_PATH` | `/home/hdd4/lpz/FLUX.1-dev2` | FLUX 模型权重目录（约 23GB） |
| `DEVICE` | `cuda:2` | 推理设备，如 `cuda:0` / `cuda:2` |
| `DASHSCOPE_API_KEY` | *(见下方安全提示)* | Qwen/DashScope 布局预测 API Key |
| `QWEN_API_KEY` | 同上 | 同上（二选一即可） |
| `VLM_BASE_URL` | 空 | 自定义 OpenAI 兼容 VLM 地址（可选） |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8888` | 监听端口 |

推荐用 `.env` 覆盖，不要改源码：

```bash
cp .env.example .env
# 编辑 .env，填入自己的 key / 模型路径 / 设备
```

> ⚠️ **安全提示**：当前 `config.py` 里把 API Key 写成了硬编码默认值。
> 若本仓库要提交到 git 或分享，请先把 `config.py` 中的明文 key 删掉，
> 改由 `.env` 提供，并确认 `.env` 已在 `.gitignore` 中。

## 使用

浏览器打开 `http://<服务器IP>:8888/`：

1. 输入复杂提示词，例如「一位服务员在咖啡馆为两位顾客上菜，一个孩子望向窗外」
2. 点击 **生成场景图** —— Qwen 解析出对象、关系、布局
3. 切换标签查看 场景图 / 边界框预览 / 明细
4. 点击 **生成图像** —— FLUX 出图（首次需加载 23GB 模型，约 3-5 分钟；之后每张约 30-60 秒）

生成期间界面会显示加载动画，前端自动轮询任务状态，完成后自动显示图片。

## API 速览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/health` | 健康检查 / GPU 状态 |
| POST | `/api/v1/predict-layout` | 提示词 → 场景图 |
| POST | `/api/v1/visualize` | 场景图 → 布局 PNG |
| POST | `/api/v1/generate` | 场景图 → 提交生成任务 |
| GET | `/api/v1/task/{task_id}` | 查询生成任务状态 |
| GET | `/docs` | Swagger 交互文档 |

生成结果图片通过 `/outputs/generated_<task_id>.png` 访问。

## 常见问题

- **服务起不来，报 `cannot import name 'draw_scene_graph_overlay'`**
  路径被 `/home/lipz/GraphDiff` 下的同名包带偏。务必用 `run_graphagent.sh`（已钉住 `PYTHONPATH`/cwd、且不开 `--reload`），不要手动 `conda activate` 后裸跑。

- **`conda activate` 报 exit 144 / shell 异常**
  改用脚本里的方式：直接用 `GraphAgent/bin/python` 启动，绕开 activate。

- **图像生成失败，报 `torch.xpu` 或 torch 版本错误**
  说明用错了环境。必须用 **GraphAgent**（torch 2.12），`bounded-attention`（torch 2.0.1）无法加载 FLUX。

- **点了「生成图像」没反应**
  首次要加载 23GB 模型，请耐心等待；可 `GET /api/v1/task/{task_id}` 或看服务日志确认进度。

## 停止服务

```bash
pkill -f "uvicorn app.main:app.*--port 8888"
```
