"""VLM 布局预测器 - 简化版本

将自然语言提示转换为结构化的场景图。
这是一个简化的实现，提供基本的布局预测功能。
"""

import json
import os
import re
from typing import Optional, Dict, List, Any

from .graph_ir import SceneGraph, GraphNode, GraphEdge


class VLMLayoutPredictor:
    """VLM 布局预测器"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """初始化预测器

        Args:
            api_key: API 密钥
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        self.model = model or "qwen-vl-max"

    def predict_layout(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        image_path: Optional[str] = None,
    ) -> SceneGraph:
        """从文本提示预测场景布局

        Args:
            prompt: 文本提示
            width: 图像宽度
            height: 图像高度
            image_path: 可选的参考图像路径

        Returns:
            预测的场景图
        """
        # 如果没有 API 密钥，使用确定性网格布局作为回退
        if not self.api_key:
            print("[VLM] 警告: 未设置 API 密钥，使用确定性网格布局")
            return self._create_deterministic_layout(prompt, width, height)

        # 这里可以集成真实的 VLM API 调用
        # 现在先使用简化的布局生成
        return self._create_simple_layout(prompt, width, height)

    def _create_deterministic_layout(
        self,
        prompt: str,
        width: int,
        height: int,
    ) -> SceneGraph:
        """创建确定性网格布局（回退方案）"""
        # 简单的关键词提取
        words = re.findall(r'\b\w+\b', prompt.lower())

        # 识别可能的对象
        common_objects = ['person', 'man', 'woman', 'child', 'boy', 'girl',
                         'table', 'chair', 'window', 'door', 'tree', 'car',
                         'cat', 'dog', 'bird', 'flower', 'book', 'cup']

        detected_objects = [obj for obj in common_objects if obj in words]

        if not detected_objects:
            # 如果没有检测到对象，创建一个单一的中心对象
            detected_objects = ['main_object']

        # 限制对象数量
        detected_objects = detected_objects[:4]

        # 创建网格布局
        num_objects = len(detected_objects)
        cols = 2 if num_objects > 2 else num_objects
        rows = (num_objects + cols - 1) // cols

        cell_width = width // cols
        cell_height = height // rows
        margin = 50

        nodes = {}
        for idx, obj_name in enumerate(detected_objects):
            row = idx // cols
            col = idx % cols

            x1 = col * cell_width + margin
            y1 = row * cell_height + margin
            x2 = (col + 1) * cell_width - margin
            y2 = (row + 1) * cell_height - margin

            node_id = f"{obj_name}_{idx}" if detected_objects.count(obj_name) > 1 else obj_name
            nodes[node_id] = GraphNode(
                id=node_id,
                type="object",
                bbox=(x1, y1, x2, y2),
                desc=f"a {obj_name}",
            )

        # 创建简单的空间关系边
        edges = []
        node_ids = list(nodes.keys())
        for i in range(len(node_ids) - 1):
            edges.append(GraphEdge(
                id=f"edge_{i}",
                source=node_ids[i],
                target=node_ids[i + 1],
                type="spatial",
                strength=0.7,
                phase="early",
            ))

        return SceneGraph(
            high_level_description=prompt,
            style_description="photographic style, natural lighting",
            background="simple background",
            nodes=nodes,
            edges=edges,
            width=width,
            height=height,
        )

    def _create_simple_layout(
        self,
        prompt: str,
        width: int,
        height: int,
    ) -> SceneGraph:
        """创建简单布局（可以在这里集成真实的 VLM API）"""
        # 这里可以调用真实的 VLM API
        # 现在使用确定性布局作为占位符
        return self._create_deterministic_layout(prompt, width, height)


def predict_layout(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    image_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> SceneGraph:
    """便捷函数：从提示预测布局

    Args:
        prompt: 文本提示
        width: 图像宽度
        height: 图像高度
        image_path: 可选的参考图像路径
        api_key: API 密钥
        model: 模型名称

    Returns:
        预测的场景图
    """
    predictor = VLMLayoutPredictor(api_key=api_key, model=model)
    return predictor.predict_layout(prompt, width, height, image_path)
