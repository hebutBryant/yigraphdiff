"""场景图中间表示 (IR)

定义场景图的内存数据结构和辅助函数，用于从 JSON 加载/验证图并构建最终的文本提示。
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #
@dataclass
class GraphNode:
    """场景图中的节点

    节点可以是对象、区域或效果区域（阴影/高光/反射），参与注意力路由。
    """
    id: str
    type: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) 像素坐标
    desc: str
    control_extend: float = 0.0  # 手动控制扩展
    tokens: Optional[List[int]] = None  # 由对齐器填充
    patch_indices: Optional[List[int]] = None  # 由对齐器填充


@dataclass
class GraphEdge:
    """两个节点之间的类型化语义传播边"""
    id: str
    source: str
    target: str
    type: str
    strength: float = 1.0
    direction: str = "source_to_target"  # 或 "bidirectional" / "target_to_source"
    phase: str = "mid"  # "early" / "mid" / "late"
    mode: str = "soft_bias"  # "soft_bias" / "hard_mask" / "negative"
    priority: float = 1.0
    relation_phrase: str = ""  # 表达此关系的文本短语


@dataclass
class SceneGraph:
    """完整的场景图"""
    high_level_description: str
    style_description: str
    background: str
    nodes: Dict[str, GraphNode]
    edges: List[GraphEdge]
    width: int = 1024
    height: int = 1024
    meta: Dict = field(default_factory=dict)

    @property
    def node_list(self) -> List[GraphNode]:
        return list(self.nodes.values())


# --------------------------------------------------------------------------- #
# 加载
# --------------------------------------------------------------------------- #
EFFECT_TYPES = {"effect", "effect_region", "shadow_region", "highlight_region", "reflection_region"}


def load_scene_graph(
    json_path: str | Path,
    default_width: int = 1024,
    default_height: int = 1024,
) -> SceneGraph:
    """从 JSON 文件加载并验证场景图"""
    json_path = Path(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    width = int(raw.get("width", default_width))
    height = int(raw.get("height", default_height))

    nodes: Dict[str, GraphNode] = {}
    for idx, el in enumerate(raw.get("elements", [])):
        if "id" not in el or not str(el["id"]).strip():
            raise ValueError(
                f"元素 #{idx} 在 {json_path} 中没有 'id' 字段 "
                f"(每个元素必须有唯一的 id)"
            )
        node_id = str(el["id"]).strip()
        if node_id in nodes:
            raise ValueError(f"重复的元素 id '{node_id}' 在 {json_path}")

        bbox = el.get("bbox", [0, 0, width, height])
        if len(bbox) != 4:
            raise ValueError(f"元素 '{node_id}' 的 bbox 必须有 4 个值，得到 {bbox}")
        bbox = tuple(int(round(v)) for v in bbox)

        nodes[node_id] = GraphNode(
            id=node_id,
            type=str(el.get("type", "object")),
            bbox=bbox,
            desc=str(el.get("desc", "")).strip(),
            control_extend=float(el.get("control_extend", 0.0)),
        )

    edges: List[GraphEdge] = []
    for idx, e in enumerate(raw.get("edges", [])):
        edge_id = str(e.get("id", f"edge_{idx}"))
        edges.append(
            GraphEdge(
                id=edge_id,
                source=str(e["source"]),
                target=str(e["target"]),
                type=str(e.get("type", "spatial")),
                strength=float(e.get("strength", 1.0)),
                direction=str(e.get("direction", "source_to_target")),
                phase=str(e.get("phase", "mid")),
                mode=str(e.get("mode", "soft_bias")),
                priority=float(e.get("priority", 1.0)),
                relation_phrase=str(e.get("relation_phrase", "")).strip(),
            )
        )

    graph = SceneGraph(
        high_level_description=str(raw.get("high_level_description", "")).strip(),
        style_description=str(raw.get("style_description", "")).strip(),
        background=str(raw.get("background", "")).strip(),
        nodes=nodes,
        edges=edges,
        width=width,
        height=height,
        meta={k: v for k, v in raw.items()
              if k not in {"elements", "edges", "high_level_description",
                           "style_description", "background", "width", "height"}},
    )

    validate_scene_graph(graph)
    return graph


# --------------------------------------------------------------------------- #
# 验证
# --------------------------------------------------------------------------- #
def validate_scene_graph(graph: SceneGraph) -> SceneGraph:
    """验证节点 ID、边端点，并裁剪越界的边界框"""
    if not graph.nodes:
        raise ValueError("场景图没有节点")

    # 将边界框裁剪到画布内，必要时发出警告
    for node in graph.nodes.values():
        x1, y1, x2, y2 = node.bbox
        cx1 = max(0, min(x1, graph.width))
        cy1 = max(0, min(y1, graph.height))
        cx2 = max(0, min(x2, graph.width))
        cy2 = max(0, min(y2, graph.height))
        # 标准化顺序
        if cx2 < cx1:
            cx1, cx2 = cx2, cx1
        if cy2 < cy1:
            cy1, cy2 = cy2, cy1
        if (cx1, cy1, cx2, cy2) != (x1, y1, x2, y2):
            print(f"[graph_ir] 警告: 节点 '{node.id}' 的边界框 {node.bbox} "
                  f"越界，已裁剪到 {(cx1, cy1, cx2, cy2)}")
            node.bbox = (cx1, cy1, cx2, cy2)
        if cx2 <= cx1 or cy2 <= cy1:
            print(f"[graph_ir] 警告: 节点 '{node.id}' 有退化的边界框 "
                  f"{node.bbox} (零面积)")

    # 边的端点必须引用现有节点
    for edge in graph.edges:
        if edge.source not in graph.nodes:
            raise ValueError(
                f"边 '{edge.id}' 引用了未知的源节点 '{edge.source}'"
            )
        if edge.target not in graph.nodes:
            raise ValueError(
                f"边 '{edge.id}' 引用了未知的目标节点 '{edge.target}'"
            )

    return graph


# --------------------------------------------------------------------------- #
# 提示构建
# --------------------------------------------------------------------------- #
def build_full_prompt(graph: SceneGraph, mode: str = "full") -> str:
    """构建提供给文本编码器的自然语言提示

    mode:
        "full"        high_level_description + background + 每个节点的描述 + style_description
        "high_level"  仅 high_level_description (+ style_description)
    """
    parts: List[str] = []
    if graph.high_level_description:
        parts.append(graph.high_level_description)

    if mode == "full":
        if graph.background:
            parts.append(graph.background)
        # 对象描述，按节点插入顺序
        for node in graph.node_list:
            if node.desc:
                parts.append(node.desc)
    elif mode != "high_level":
        raise ValueError(f"未知的提示模式: {mode!r}")

    if graph.style_description:
        parts.append(graph.style_description)

    # 使用 ". " 作为稳定的分隔符
    prompt = ". ".join(p.rstrip(". ").strip() for p in parts if p.strip())
    if prompt and not prompt.endswith("."):
        prompt += "."
    return prompt


# --------------------------------------------------------------------------- #
# 摘要
# --------------------------------------------------------------------------- #
def summarize_scene_graph(graph: SceneGraph) -> str:
    """返回（并打印）图的可读摘要"""
    edge_types = Counter(e.type for e in graph.edges)
    node_types = Counter(n.type for n in graph.node_list)

    lines = [
        "=" * 60,
        "[graph_ir] 场景图摘要",
        f"  画布尺寸    : {graph.width} x {graph.height}",
        f"  节点数      : {len(graph.nodes)}  ({dict(node_types)})",
        f"  边数        : {len(graph.edges)}",
        f"  边类型      : {dict(edge_types)}",
    ]
    for n in graph.node_list:
        lines.append(f"    节点 {n.id:<18} 类型={n.type:<16} 边界框={n.bbox}")
    for e in graph.edges:
        lines.append(
            f"    边 {e.id:<22} {e.source} -[{e.type}]-> {e.target}  "
            f"(强度={e.strength}, 阶段={e.phase}, 模式={e.mode})"
        )
    lines.append("=" * 60)
    text = "\n".join(lines)
    print(text)
    return text
