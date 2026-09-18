"""GraphExecutor — 基于图的场景生成引擎核心模块

Pipeline:
    prompt -> 场景图 JSON -> SceneGraph -> token/region 对齐
    -> 类型化边编译 -> 时序调度器 -> 注意力路由偏置 -> 图像生成

公共接口:
    * graph_ir: 加载/验证/总结场景图
    * vlm_layout: VLM 布局预测器
    * visualization: 可视化工具
"""

from .graph_ir import (
    GraphNode,
    GraphEdge,
    SceneGraph,
    load_scene_graph,
    validate_scene_graph,
    build_full_prompt,
    summarize_scene_graph,
)

__all__ = [
    "GraphNode",
    "GraphEdge",
    "SceneGraph",
    "load_scene_graph",
    "validate_scene_graph",
    "build_full_prompt",
    "summarize_scene_graph",
]
