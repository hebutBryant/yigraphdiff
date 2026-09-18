"""场景图和布局可视化工具"""

import io
import json
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image, ImageDraw, ImageFont

from .graph_ir import SceneGraph


def draw_scene_graph_overlay(
    graph: SceneGraph,
    background_image: Optional[Image.Image] = None,
    show_labels: bool = True,
    line_width: int = 3,
) -> Image.Image:
    """在图像上绘制场景图的边界框覆盖层

    Args:
        graph: 场景图对象
        background_image: 可选的背景图像，如果为 None 则创建白色背景
        show_labels: 是否显示节点标签
        line_width: 边界框线宽

    Returns:
        带有边界框覆盖层的 PIL 图像
    """
    # 创建或使用背景图像
    if background_image is None:
        img = Image.new('RGB', (graph.width, graph.height), color='white')
    else:
        img = background_image.copy()
        img = img.resize((graph.width, graph.height))

    draw = ImageDraw.Draw(img)

    # 为每个节点分配颜色
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
        '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788'
    ]

    # 绘制边界框和标签
    for idx, node in enumerate(graph.node_list):
        x1, y1, x2, y2 = node.bbox
        color = colors[idx % len(colors)]

        # 绘制边界框
        draw.rectangle(
            [(x1, y1), (x2, y2)],
            outline=color,
            width=line_width
        )

        # 绘制标签
        if show_labels:
            label = f"{node.id}"
            # 简单的标签背景
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                font = ImageFont.load_default()

            # 获取文本边界框
            bbox = draw.textbbox((x1, y1 - 20), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 绘制标签背景
            draw.rectangle(
                [(x1, y1 - text_height - 4), (x1 + text_width + 8, y1)],
                fill=color
            )
            # 绘制文本
            draw.text((x1 + 4, y1 - text_height - 2), label, fill='white', font=font)

    return img


def visualize_graph_structure(graph: SceneGraph, output_path: Optional[str] = None) -> bytes:
    """可视化场景图的结构（节点和边）

    Args:
        graph: 场景图对象
        output_path: 可选的输出文件路径

    Returns:
        图像的字节数据
    """
    try:
        import networkx as nx
    except ImportError:
        print("警告: networkx 未安装，跳过图结构可视化")
        # 返回一个简单的占位符图像
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((300, 280), "需要 networkx 库", fill='black')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    # 创建有向图
    G = nx.DiGraph()

    # 添加节点
    for node in graph.node_list:
        G.add_node(node.id, type=node.type)

    # 添加边
    edge_colors = []
    edge_types = {
        'spatial': '#3498db',
        'contact': '#e74c3c',
        'gaze': '#f39c12',
        'reflection': '#9b59b6',
        'lighting': '#f1c40f',
        'negative': '#95a5a6',
    }

    for edge in graph.edges:
        G.add_edge(edge.source, edge.target, type=edge.type, strength=edge.strength)
        # 根据边类型选择颜色
        base_type = edge.type.split('_')[0] if '_' in edge.type else edge.type
        color = edge_types.get(base_type, '#34495e')
        edge_colors.append(color)

    # 绘制图
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=2, iterations=50)

    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_color='lightblue',
                          node_size=3000, alpha=0.9)

    # 绘制边
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors,
                          width=2, alpha=0.6, arrows=True,
                          arrowsize=20, arrowstyle='->')

    # 绘制标签
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    # 添加边标签（类型）
    edge_labels = {(e.source, e.target): e.type for e in graph.edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

    plt.title(f"场景图结构\n{len(graph.nodes)} 个节点, {len(graph.edges)} 条边",
             fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()

    # 保存到字节流或文件
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')

    plt.close()

    return buf.getvalue()


def create_visualization_grid(
    graph: SceneGraph,
    generated_image: Optional[Image.Image] = None,
    output_path: Optional[str] = None,
) -> Image.Image:
    """创建包含多个可视化的网格图

    Args:
        graph: 场景图对象
        generated_image: 可选的生成图像
        output_path: 可选的输出文件路径

    Returns:
        组合的可视化网格图像
    """
    # 创建边界框覆盖图
    bbox_overlay = draw_scene_graph_overlay(graph, background_image=generated_image)

    # 创建图结构可视化
    graph_viz_bytes = visualize_graph_structure(graph)
    graph_viz = Image.open(io.BytesIO(graph_viz_bytes))

    # 调整大小使它们匹配
    target_width = max(bbox_overlay.width, graph_viz.width)
    target_height = bbox_overlay.height + graph_viz.height + 20

    # 创建组合图像
    combined = Image.new('RGB', (target_width, target_height), color='white')

    # 粘贴边界框覆盖图
    combined.paste(bbox_overlay, (0, 0))

    # 粘贴图结构可视化
    graph_viz_resized = graph_viz.resize((target_width, graph_viz.height))
    combined.paste(graph_viz_resized, (0, bbox_overlay.height + 20))

    if output_path:
        combined.save(output_path)

    return combined


def export_scene_graph_json(graph: SceneGraph, output_path: str) -> None:
    """将场景图导出为 JSON 文件

    Args:
        graph: 场景图对象
        output_path: 输出文件路径
    """
    data = {
        "high_level_description": graph.high_level_description,
        "style_description": graph.style_description,
        "background": graph.background,
        "width": graph.width,
        "height": graph.height,
        "elements": [
            {
                "id": node.id,
                "type": node.type,
                "bbox": list(node.bbox),
                "desc": node.desc,
                "control_extend": node.control_extend,
            }
            for node in graph.node_list
        ],
        "edges": [
            {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "type": edge.type,
                "strength": edge.strength,
                "direction": edge.direction,
                "phase": edge.phase,
                "mode": edge.mode,
                "priority": edge.priority,
                "relation_phrase": edge.relation_phrase,
            }
            for edge in graph.edges
        ],
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
