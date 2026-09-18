"""VLM 布局预测器 - 集成 Qwen API

将自然语言提示转换为结构化的场景图。
"""

import json
import os
import re
import requests
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
        self.model = model or "qwen-vl-plus"
        self.base_url = os.getenv("VLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

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

        # 尝试调用真实的 VLM API
        try:
            return self._call_qwen_api(prompt, width, height)
        except Exception as e:
            print(f"[VLM] API 调用失败: {e}，回退到确定性布局")
            return self._create_deterministic_layout(prompt, width, height)

    def _call_qwen_api(self, prompt: str, width: int, height: int) -> SceneGraph:
        """调用 Qwen API 生成场景图"""

        system_prompt = """你是一个场景图生成专家。根据用户的文本描述，生成结构化的场景图。

场景图包含：
1. 对象（objects）：场景中的实体，需要包含 id、描述和边界框坐标
2. 关系（edges）：对象之间的关系，如空间位置、交互等

边界框坐标格式：[x1, y1, x2, y2]，范围 0-1024

关系类型：
- spatial: 空间关系（left_of, right_of, above, below, near）
- contact: 接触关系（holding, on, in, serving）
- gaze: 注视关系（looks_at, points_to）
- lighting: 光照关系（illuminates, casts_shadow）

请以 JSON 格式返回，结构如下：
{
  "objects": [{"id": "obj1", "desc": "描述", "bbox": [x1,y1,x2,y2]}],
  "relations": [{"source": "obj1", "target": "obj2", "type": "spatial"}]
}"""

        user_prompt = f"场景描述：{prompt}\n\n请生成该场景的结构化表示，识别所有对象及其位置关系。"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"API 返回错误: {response.status_code} - {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 解析 LLM 返回的 JSON
        return self._parse_llm_response(content, prompt, width, height)

    def _parse_llm_response(self, content: str, prompt: str, width: int, height: int) -> SceneGraph:
        """解析 LLM 返回的内容并转换为 SceneGraph"""
        try:
            # 提取 JSON（可能在 markdown 代码块中）
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = content

            data = json.loads(json_str)

            # 构建节点
            nodes = {}
            for obj in data.get("objects", []):
                node_id = obj["id"]
                bbox = obj["bbox"]
                # 确保 bbox 在范围内
                bbox = [max(0, min(v, width if i % 2 == 0 else height))
                       for i, v in enumerate(bbox)]
                nodes[node_id] = GraphNode(
                    id=node_id,
                    type="object",
                    bbox=tuple(bbox),
                    desc=obj.get("desc", f"a {node_id}"),
                )

            # 构建边
            edges = []
            for idx, rel in enumerate(data.get("relations", [])):
                edges.append(GraphEdge(
                    id=f"edge_{idx}",
                    source=rel["source"],
                    target=rel["target"],
                    type=rel.get("type", "spatial"),
                    strength=rel.get("strength", 0.8),
                ))

            return SceneGraph(
                high_level_description=prompt,
                style_description="photographic style, natural lighting",
                background=data.get("background", "realistic background"),
                nodes=nodes,
                edges=edges,
                width=width,
                height=height,
            )

        except Exception as e:
            print(f"[VLM] 解析 LLM 响应失败: {e}")
            print(f"[VLM] 响应内容: {content[:200]}...")
            # 回退到确定性布局
            return self._create_deterministic_layout(prompt, width, height)

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
