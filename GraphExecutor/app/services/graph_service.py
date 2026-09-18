"""核心业务逻辑服务"""

import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from graphexecutor.graph_ir import (
    SceneGraph, GraphNode, GraphEdge,
    load_scene_graph, validate_scene_graph,
    build_full_prompt, summarize_scene_graph
)
from graphexecutor.vlm_layout import predict_layout
from graphexecutor.visualization import (
    draw_scene_graph_overlay,
    visualize_graph_structure,
    create_visualization_grid,
    export_scene_graph_json,
)
from app.models.schemas import SceneGraphInput, SceneGraphOutput, NodeOutput, EdgeOutput
import config

# 尝试导入 FLUX 生成器（可选）
try:
    from graphexecutor.flux_generator import generate_image, get_generator
    _FLUX_AVAILABLE = True
except Exception as e:
    print(f"[Service] FLUX 生成器不可用: {e}")
    _FLUX_AVAILABLE = False


class GraphService:
    """场景图服务"""

    def __init__(self):
        """初始化服务"""
        self.output_dir = config.OUTPUT_DIR
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def predict_layout_from_prompt(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        image_path: Optional[str] = None,
    ) -> SceneGraph:
        """从文本提示预测布局

        Args:
            prompt: 文本提示
            width: 画布宽度
            height: 画布高度
            image_path: 可选的参考图像路径

        Returns:
            预测的场景图
        """
        graph = predict_layout(
            prompt=prompt,
            width=width,
            height=height,
            image_path=image_path,
            api_key=config.DASHSCOPE_API_KEY or config.QWEN_API_KEY,
        )
        return graph

    def load_scene_graph_from_input(self, scene_graph_input: SceneGraphInput) -> SceneGraph:
        """从输入数据加载场景图

        Args:
            scene_graph_input: 场景图输入数据

        Returns:
            场景图对象
        """
        # 转换节点
        nodes = {}
        for elem in scene_graph_input.elements:
            nodes[elem.id] = GraphNode(
                id=elem.id,
                type=elem.type,
                bbox=tuple(elem.bbox),
                desc=elem.desc,
                control_extend=elem.control_extend,
            )

        # 转换边
        edges = []
        for edge_input in scene_graph_input.edges:
            edges.append(GraphEdge(
                id=edge_input.id,
                source=edge_input.source,
                target=edge_input.target,
                type=edge_input.type,
                strength=edge_input.strength,
                direction=edge_input.direction,
                phase=edge_input.phase,
                mode=edge_input.mode,
                priority=edge_input.priority,
                relation_phrase=edge_input.relation_phrase,
            ))

        graph = SceneGraph(
            high_level_description=scene_graph_input.high_level_description,
            style_description=scene_graph_input.style_description,
            background=scene_graph_input.background,
            nodes=nodes,
            edges=edges,
            width=scene_graph_input.width,
            height=scene_graph_input.height,
        )

        validate_scene_graph(graph)
        return graph

    def scene_graph_to_output(self, graph: SceneGraph) -> SceneGraphOutput:
        """将场景图转换为输出格式

        Args:
            graph: 场景图对象

        Returns:
            场景图输出数据
        """
        elements = [
            NodeOutput(
                id=node.id,
                type=node.type,
                bbox=list(node.bbox),
                desc=node.desc,
                control_extend=node.control_extend,
            )
            for node in graph.node_list
        ]

        edges = [
            EdgeOutput(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                type=edge.type,
                strength=edge.strength,
                direction=edge.direction,
                phase=edge.phase,
                mode=edge.mode,
                priority=edge.priority,
                relation_phrase=edge.relation_phrase,
            )
            for edge in graph.edges
        ]

        summary = summarize_scene_graph(graph)

        return SceneGraphOutput(
            high_level_description=graph.high_level_description,
            style_description=graph.style_description,
            background=graph.background,
            width=graph.width,
            height=graph.height,
            elements=elements,
            edges=edges,
            summary=summary,
        )

    def create_visualization(
        self,
        graph: SceneGraph,
        visualization_type: str = "bbox_overlay",
        show_labels: bool = True,
    ) -> Path:
        """创建可视化

        Args:
            graph: 场景图对象
            visualization_type: 可视化类型
            show_labels: 是否显示标签

        Returns:
            可视化文件路径
        """
        task_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if visualization_type == "bbox_overlay":
            output_path = self.output_dir / f"bbox_overlay_{timestamp}_{task_id}.png"
            img = draw_scene_graph_overlay(graph, show_labels=show_labels)
            img.save(output_path)

        elif visualization_type == "graph_structure":
            output_path = self.output_dir / f"graph_structure_{timestamp}_{task_id}.png"
            visualize_graph_structure(graph, output_path=str(output_path))

        elif visualization_type == "grid":
            output_path = self.output_dir / f"visualization_grid_{timestamp}_{task_id}.png"
            create_visualization_grid(graph, output_path=str(output_path))

        else:
            raise ValueError(f"未知的可视化类型: {visualization_type}")

        return output_path

    def export_scene_graph(self, graph: SceneGraph, task_id: Optional[str] = None) -> Path:
        """导出场景图为 JSON

        Args:
            graph: 场景图对象
            task_id: 可选的任务 ID

        Returns:
            JSON 文件路径
        """
        if task_id is None:
            task_id = str(uuid.uuid4())[:8]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"scene_graph_{timestamp}_{task_id}.json"

        export_scene_graph_json(graph, str(output_path))
        return output_path

    def get_full_prompt(self, graph: SceneGraph, mode: str = "full") -> str:
        """获取完整提示

        Args:
            graph: 场景图对象
            mode: 提示模式

        Returns:
            完整提示文本
        """
        return build_full_prompt(graph, mode=mode)

    def create_generation_task(
        self,
        prompt: Optional[str] = None,
        scene_graph: Optional[SceneGraph] = None,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> str:
        """创建图像生成任务

        Args:
            prompt: 文本提示
            scene_graph: 场景图对象
            width: 宽度
            height: 高度
            **kwargs: 其他参数

        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())

        # 如果提供了提示但没有场景图，则预测布局
        if prompt and not scene_graph:
            scene_graph = self.predict_layout_from_prompt(prompt, width, height)

        # 存储任务信息
        self.tasks[task_id] = {
            "id": task_id,
            "status": "pending",
            "scene_graph": scene_graph,
            "prompt": prompt,
            "width": width,
            "height": height,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }

        # 如果 FLUX 可用，异步生成图像
        if _FLUX_AVAILABLE and scene_graph:
            try:
                self._run_generation_async(task_id, scene_graph, width, height, **kwargs)
            except Exception as e:
                print(f"[Service] 图像生成失败: {e}")
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
        else:
            # FLUX 不可用，只返回布局图
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["message"] = "FLUX 模型未加载，仅生成布局图"

        return task_id

    def _run_generation_async(
        self,
        task_id: str,
        scene_graph: SceneGraph,
        width: int,
        height: int,
        **kwargs
    ):
        """异步运行图像生成"""
        import threading

        def generate():
            try:
                print(f"[Service] 开始生成任务 {task_id}")
                self.tasks[task_id]["status"] = "processing"

                # 调用 FLUX 生成
                image = generate_image(
                    scene_graph=scene_graph,
                    width=width,
                    height=height,
                    num_inference_steps=kwargs.get("num_inference_steps", 32),
                    guidance_scale=kwargs.get("guidance_scale", 3.5),
                    seed=kwargs.get("seed"),
                    control_mode=kwargs.get("control_mode", "graph_executor"),
                )

                # 保存图像
                output_path = self.output_dir / f"generated_{task_id}.png"
                image.save(output_path)

                # 更新任务状态
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["image_path"] = str(output_path)
                self.tasks[task_id]["image_url"] = f"/outputs/generated_{task_id}.png"

                print(f"[Service] 任务 {task_id} 完成")

            except Exception as e:
                print(f"[Service] 任务 {task_id} 失败: {e}")
                import traceback
                traceback.print_exc()
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)

        # 在后台线程运行
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务信息
        """
        return self.tasks.get(task_id)


# 创建全局服务实例
graph_service = GraphService()
