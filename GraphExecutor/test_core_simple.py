#!/usr/bin/env python3
"""简化的核心模块测试（不需要可视化依赖）"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("GraphExecutor 核心模块测试（简化版）")
print("=" * 60)

# 测试 1: 导入核心模块
print("\n1. 测试核心模块导入...")
try:
    from graphexecutor.graph_ir import (
        GraphNode, GraphEdge, SceneGraph,
        load_scene_graph, validate_scene_graph,
        build_full_prompt, summarize_scene_graph
    )
    print("✓ 核心模块导入成功")
except Exception as e:
    print(f"✗ 核心模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 2: 创建场景图
print("\n2. 测试创建场景图...")
try:
    nodes = {
        "cat": GraphNode(
            id="cat",
            type="object",
            bbox=(100, 100, 400, 500),
            desc="一只红色的猫"
        ),
        "chair": GraphNode(
            id="chair",
            type="object",
            bbox=(300, 400, 700, 900),
            desc="一把蓝色的椅子"
        ),
    }

    edges = [
        GraphEdge(
            id="cat_on_chair",
            source="cat",
            target="chair",
            type="on",
            strength=0.9,
        )
    ]

    graph = SceneGraph(
        high_level_description="一只猫坐在椅子上",
        style_description="摄影风格",
        background="简单背景",
        nodes=nodes,
        edges=edges,
        width=1024,
        height=1024,
    )

    print(f"✓ 场景图创建成功: {len(graph.nodes)} 个节点, {len(graph.edges)} 条边")
except Exception as e:
    print(f"✗ 场景图创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: 验证场景图
print("\n3. 测试验证场景图...")
try:
    validate_scene_graph(graph)
    print("✓ 场景图验证通过")
except Exception as e:
    print(f"✗ 场景图验证失败: {e}")
    sys.exit(1)

# 测试 4: 构建提示
print("\n4. 测试构建提示...")
try:
    prompt = build_full_prompt(graph)
    print(f"✓ 提示构建成功:")
    print(f"  '{prompt}'")
except Exception as e:
    print(f"✗ 提示构建失败: {e}")
    sys.exit(1)

# 测试 5: 总结场景图
print("\n5. 测试总结场景图...")
try:
    summary = summarize_scene_graph(graph)
    print("✓ 场景图总结成功")
except Exception as e:
    print(f"✗ 场景图总结失败: {e}")
    sys.exit(1)

# 测试 6: VLM 布局预测（确定性回退）
print("\n6. 测试 VLM 布局预测...")
try:
    from graphexecutor.vlm_layout import predict_layout
    predicted_graph = predict_layout(
        prompt="一只红色的猫坐在蓝色的椅子上",
        width=1024,
        height=1024,
    )
    print(f"✓ 布局预测成功: {len(predicted_graph.nodes)} 个节点")
except Exception as e:
    print(f"✗ 布局预测失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 7: JSON 导出和加载
print("\n7. 测试 JSON 导出...")
try:
    import json
    json_path = PROJECT_ROOT / "test_scene_graph.json"

    # 手动导出
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
            }
            for edge in graph.edges
        ],
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ JSON 导出成功: {json_path}")

    # 测试加载
    loaded_graph = load_scene_graph(json_path)
    print(f"✓ JSON 加载成功: {len(loaded_graph.nodes)} 个节点")

except Exception as e:
    print(f"✗ JSON 操作失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 8: API 数据模型
print("\n8. 测试 API 数据模型...")
try:
    from app.models.schemas import SceneGraphInput, NodeInput, EdgeInput

    node_data = NodeInput(
        id="test_node",
        type="object",
        bbox=[100, 100, 400, 400],
        desc="测试节点"
    )

    scene_input = SceneGraphInput(
        high_level_description="测试场景",
        elements=[node_data],
        edges=[]
    )

    print(f"✓ API 数据模型验证成功")

except Exception as e:
    print(f"✗ API 数据模型失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("核心模块测试完成!")
print("=" * 60)
print("\n下一步:")
print("1. 安装可视化依赖: pip install matplotlib pillow networkx")
print("2. 启动服务: python app/main.py")
print("3. 访问文档: http://localhost:8000/docs")
print("=" * 60)
