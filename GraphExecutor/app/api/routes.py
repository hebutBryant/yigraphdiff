"""API 路由定义"""

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:  # torch 是可选依赖，仅用于 GPU 检测
    torch = None
    _TORCH_AVAILABLE = False

from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path

from app.models.schemas import (
    LayoutPredictionRequest,
    SceneGraphInput,
    SceneGraphOutput,
    VisualizationRequest,
    GenerationRequest,
    GenerationResponse,
    HealthResponse,
    ErrorResponse,
)
from app.services.graph_service import graph_service
import config


router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """检查服务健康状态"""
    gpu_available = bool(_TORCH_AVAILABLE and torch.cuda.is_available())

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        gpu_available=gpu_available,
        message=f"GraphExecutor 服务运行正常. GPU: {'可用' if gpu_available else '不可用'}"
    )


@router.post("/predict-layout", response_model=SceneGraphOutput, summary="从提示预测布局")
async def predict_layout(request: LayoutPredictionRequest):
    """
    从自然语言提示预测场景布局

    - **prompt**: 描述场景的文本提示
    - **width**: 画布宽度（像素）
    - **height**: 画布高度（像素）
    - **image_url**: 可选的参考图像 URL

    返回预测的场景图，包含对象、边界框和关系。
    """
    try:
        graph = graph_service.predict_layout_from_prompt(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            image_path=request.image_url,
        )

        output = graph_service.scene_graph_to_output(graph)
        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"布局预测失败: {str(e)}")


@router.post("/validate-scene-graph", response_model=SceneGraphOutput, summary="验证场景图")
async def validate_scene_graph(scene_graph: SceneGraphInput):
    """
    验证并规范化场景图

    - 检查节点和边的有效性
    - 裁剪越界的边界框
    - 验证边的端点引用

    返回验证后的场景图。
    """
    try:
        graph = graph_service.load_scene_graph_from_input(scene_graph)
        output = graph_service.scene_graph_to_output(graph)
        return output

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"场景图验证失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/visualize", response_class=FileResponse, summary="创建可视化")
async def create_visualization(request: VisualizationRequest):
    """
    为场景图创建可视化

    - **scene_graph**: 要可视化的场景图
    - **visualization_type**: 可视化类型
        - `bbox_overlay`: 边界框覆盖图（默认）
        - `graph_structure`: 图结构可视化（节点和边）
        - `grid`: 组合网格视图
    - **show_labels**: 是否显示节点标签

    返回可视化图像文件。
    """
    try:
        graph = graph_service.load_scene_graph_from_input(request.scene_graph)

        output_path = graph_service.create_visualization(
            graph=graph,
            visualization_type=request.visualization_type,
            show_labels=request.show_labels,
        )

        return FileResponse(
            path=str(output_path),
            media_type="image/png",
            filename=output_path.name
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"可视化创建失败: {str(e)}")


@router.post("/export-scene-graph", response_class=FileResponse, summary="导出场景图")
async def export_scene_graph(scene_graph: SceneGraphInput):
    """
    将场景图导出为 JSON 文件

    返回格式化的 JSON 文件，可以保存和重用。
    """
    try:
        graph = graph_service.load_scene_graph_from_input(scene_graph)
        output_path = graph_service.export_scene_graph(graph)

        return FileResponse(
            path=str(output_path),
            media_type="application/json",
            filename=output_path.name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/get-prompt", summary="获取完整提示")
async def get_full_prompt(scene_graph: SceneGraphInput, mode: str = "full"):
    """
    从场景图生成完整的文本提示

    - **scene_graph**: 场景图
    - **mode**: 提示模式
        - `full`: 包含所有描述（默认）
        - `high_level`: 仅高层描述

    返回格式化的提示文本。
    """
    try:
        graph = graph_service.load_scene_graph_from_input(scene_graph)
        prompt = graph_service.get_full_prompt(graph, mode=mode)

        return {
            "prompt": prompt,
            "mode": mode,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提示生成失败: {str(e)}")


@router.post("/generate", response_model=GenerationResponse, summary="生成图像")
async def generate_image(request: GenerationRequest):
    """
    从提示或场景图生成图像

    - **prompt**: 文本提示（将自动预测布局）
    - **scene_graph**: 或者提供预定义的场景图
    - **width**, **height**: 图像尺寸
    - **num_inference_steps**: 推理步数
    - **guidance_scale**: 引导比例
    - **seed**: 随机种子（可选）
    - **save_visualization**: 是否保存可视化

    返回生成任务的信息。

    注意：这是一个简化的实现，实际的图像生成需要完整的 FLUX 模型支持。
    """
    try:
        # 验证输入
        if not request.prompt and not request.scene_graph:
            raise HTTPException(
                status_code=400,
                detail="必须提供 prompt 或 scene_graph 之一"
            )

        # 加载或预测场景图
        if request.scene_graph:
            scene_graph = graph_service.load_scene_graph_from_input(request.scene_graph)
        else:
            scene_graph = graph_service.predict_layout_from_prompt(
                prompt=request.prompt,
                width=request.width,
                height=request.height,
            )

        # 创建任务
        task_id = graph_service.create_generation_task(
            prompt=request.prompt,
            scene_graph=scene_graph,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
        )

        # 如果需要，创建可视化
        visualization_path = None
        if request.save_visualization:
            visualization_path = graph_service.create_visualization(
                graph=scene_graph,
                visualization_type="bbox_overlay",
            )

        scene_graph_output = graph_service.scene_graph_to_output(scene_graph)

        # 获取任务状态（可能已经完成或正在处理）
        task_status = graph_service.get_task_status(task_id)
        status = task_status.get("status", "pending")
        image_url = task_status.get("image_url")
        message = task_status.get("message", "任务已创建")

        return GenerationResponse(
            task_id=task_id,
            status=status,
            image_url=image_url,
            visualization_url=str(visualization_path) if visualization_path else None,
            scene_graph=scene_graph_output,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成任务创建失败: {str(e)}")


@router.get("/task/{task_id}", summary="获取任务状态")
async def get_task_status(task_id: str):
    """
    获取生成任务的状态

    返回任务信息和当前状态。
    """
    task = graph_service.get_task_status(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    # 返回完整的任务信息
    return {
        "task_id": task["id"],
        "status": task["status"],
        "created_at": task["created_at"],
        "prompt": task.get("prompt"),
        "width": task.get("width"),
        "height": task.get("height"),
        "image_url": task.get("image_url"),
        "image_path": task.get("image_path"),
        "error": task.get("error"),
        "message": task.get("message"),
    }
