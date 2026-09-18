"""数据模型和请求/响应架构"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BBox(BaseModel):
    """边界框"""
    x1: int = Field(..., description="左上角 X 坐标")
    y1: int = Field(..., description="左上角 Y 坐标")
    x2: int = Field(..., description="右下角 X 坐标")
    y2: int = Field(..., description="右下角 Y 坐标")


class NodeInput(BaseModel):
    """节点输入"""
    id: str = Field(..., description="节点唯一标识符")
    type: str = Field(default="object", description="节点类型")
    bbox: List[int] = Field(..., description="边界框 [x1, y1, x2, y2]")
    desc: str = Field(..., description="节点描述")
    control_extend: float = Field(default=0.0, description="控制扩展")


class EdgeInput(BaseModel):
    """边输入"""
    id: str = Field(..., description="边唯一标识符")
    source: str = Field(..., description="源节点 ID")
    target: str = Field(..., description="目标节点 ID")
    type: str = Field(default="spatial", description="边类型")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="强度")
    direction: str = Field(default="source_to_target", description="方向")
    phase: str = Field(default="mid", description="阶段")
    mode: str = Field(default="soft_bias", description="模式")
    priority: float = Field(default=1.0, description="优先级")
    relation_phrase: str = Field(default="", description="关系短语")


class SceneGraphInput(BaseModel):
    """场景图输入"""
    high_level_description: str = Field(..., description="高层描述")
    style_description: str = Field(default="", description="风格描述")
    background: str = Field(default="", description="背景描述")
    width: int = Field(default=1024, ge=256, le=2048, description="画布宽度")
    height: int = Field(default=1024, ge=256, le=2048, description="画布高度")
    elements: List[NodeInput] = Field(..., description="场景元素（节点）")
    edges: List[EdgeInput] = Field(default=[], description="元素之间的关系（边）")


class LayoutPredictionRequest(BaseModel):
    """布局预测请求"""
    prompt: str = Field(..., description="文本提示")
    width: int = Field(default=1024, ge=256, le=2048, description="画布宽度")
    height: int = Field(default=1024, ge=256, le=2048, description="画布高度")
    image_url: Optional[str] = Field(None, description="参考图像 URL（可选）")


class NodeOutput(BaseModel):
    """节点输出"""
    id: str
    type: str
    bbox: List[int]
    desc: str
    control_extend: float


class EdgeOutput(BaseModel):
    """边输出"""
    id: str
    source: str
    target: str
    type: str
    strength: float
    direction: str
    phase: str
    mode: str
    priority: float
    relation_phrase: str


class SceneGraphOutput(BaseModel):
    """场景图输出"""
    high_level_description: str
    style_description: str
    background: str
    width: int
    height: int
    elements: List[NodeOutput]
    edges: List[EdgeOutput]
    summary: Optional[str] = None


class VisualizationRequest(BaseModel):
    """可视化请求"""
    scene_graph: SceneGraphInput = Field(..., description="场景图")
    show_labels: bool = Field(default=True, description="是否显示标签")
    visualization_type: str = Field(
        default="bbox_overlay",
        description="可视化类型: bbox_overlay, graph_structure, grid"
    )


class GenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: Optional[str] = Field(None, description="文本提示（用于布局预测）")
    scene_graph: Optional[SceneGraphInput] = Field(None, description="预定义的场景图")
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    num_inference_steps: int = Field(default=32, ge=10, le=100)
    guidance_scale: float = Field(default=3.5, ge=1.0, le=20.0)
    seed: Optional[int] = Field(None, description="随机种子")
    save_visualization: bool = Field(default=True, description="是否保存可视化")


class GenerationResponse(BaseModel):
    """图像生成响应"""
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="状态")
    image_url: Optional[str] = Field(None, description="生成的图像 URL")
    visualization_url: Optional[str] = Field(None, description="可视化图像 URL")
    scene_graph: Optional[SceneGraphOutput] = Field(None, description="使用的场景图")
    message: Optional[str] = Field(None, description="消息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    gpu_available: bool
    message: str


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    status_code: int
