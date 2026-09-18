"""GraphExecutor FastAPI 应用主入口"""

from pathlib import Path
import sys

# 添加项目根目录到 Python 路径（必须在所有导入之前）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 移除可能冲突的 GraphDiff 路径
sys.path = [p for p in sys.path if 'GraphDiff' not in p]
# 将当前项目路径插入到最前面
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
import config


# 创建 FastAPI 应用
app = FastAPI(
    title="GraphExecutor API",
    description="""
    GraphExecutor - 基于场景图的图像生成服务

    ## 功能特性

    * **布局预测**: 从自然语言提示预测场景布局
    * **场景图管理**: 创建、验证、导出场景图
    * **可视化**: 生成边界框覆盖图和图结构可视化
    * **图像生成**: 基于场景图的图像生成（需要 FLUX 模型）

    ## 核心概念

    **场景图 (Scene Graph)**:
    - **节点 (Nodes)**: 场景中的对象，每个对象有边界框和描述
    - **边 (Edges)**: 对象之间的关系（空间关系、接触、注视、反射、光照等）

    **边类型**:
    - `spatial`: 空间关系 (left_of, right_of, above, below, near)
    - `contact`: 接触关系 (holding, placed_on, carrying, on, in)
    - `gaze`: 注视关系 (looks_at, points_to, watching)
    - `reflection`: 反射关系
    - `lighting`: 光照关系 (illuminates, casts_shadow)
    - `negative`: 负向关系（抑制属性混合）

    ## 工作流程

    1. **预测布局**: POST `/predict-layout` - 从文本提示生成场景图
    2. **验证**: POST `/validate-scene-graph` - 验证和规范化场景图
    3. **可视化**: POST `/visualize` - 创建可视化图像
    4. **生成**: POST `/generate` - 生成最终图像

    ## 示例

    ```python
    # 1. 从提示预测布局
    response = requests.post("/predict-layout", json={
        "prompt": "一位服务员在咖啡馆桌前为两位顾客服务，一个孩子望向窗外",
        "width": 1024,
        "height": 1024
    })
    scene_graph = response.json()

    # 2. 创建可视化
    response = requests.post("/visualize", json={
        "scene_graph": scene_graph,
        "visualization_type": "bbox_overlay"
    })

    # 3. 生成图像
    response = requests.post("/generate", json={
        "scene_graph": scene_graph,
        "num_inference_steps": 32
    })
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于访问生成的图像）
if config.OUTPUT_DIR.exists():
    app.mount("/outputs", StaticFiles(directory=str(config.OUTPUT_DIR)), name="outputs")

# 挂载前端静态资源（style.css / app.js 等）
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# 注册路由
app.include_router(router, prefix="/api/v1", tags=["GraphExecutor"])


@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    """根路径 - 返回前端页面（若不存在则返回服务信息 JSON）"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "GraphExecutor API",
        "version": "1.0.0",
        "description": "基于场景图的图像生成服务",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api", tags=["Root"])
async def api_info():
    """服务信息"""
    return {
        "service": "GraphExecutor API",
        "version": "1.0.0",
        "description": "基于场景图的图像生成服务",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("=" * 60)
    print("GraphExecutor API 服务启动")
    print(f"配置信息:")
    print(f"  - 输出目录: {config.OUTPUT_DIR}")
    print(f"  - 默认画布尺寸: {config.DEFAULT_WIDTH}x{config.DEFAULT_HEIGHT}")
    print(f"  - GPU 可用: {config.DEVICE}")
    print(f"API 文档: http://{config.HOST}:{config.PORT}/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("GraphExecutor API 服务关闭")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,  # 直接传入 app 对象，不使用字符串
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )
