#!/usr/bin/env python3
"""快速测试 GraphExecutor 核心模块（不需要启动服务）"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("GraphExecutor 核心模块测试")
print("=" * 60)

# 测试 1: 导入核心模块
print("\n1. 测试模块导入...")
try:
    from graphexecutor import (
        GraphNode, GraphEdge, SceneGraph,
        load_scene_graph, validate_scene_graph,
        build_full_prompt, summarize_scene_graph
    )
    from graphexecutor.vlm_layout import predict_layout
    from graphexecutor.visualization import draw_scene_graph_overlay
    print("✓ 所有核心模块导入成功")
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
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
    print(f"  {prompt}")
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
    predicted_graph = predict_layout(
        prompt="一只红色的猫坐在蓝色的椅子上",
        width=1024,
        height=1024,
    )
    print(f"✓ 布局预测成功: {len(predicted_graph.nodes)} 个节点")
except Exception as e:
    print(f"✗ 布局预测失败: {e}")
    sys.exit(1)

# 测试 7: 可视化
print("\n7. 测试可视化...")
try:
    img = draw_scene_graph_overlay(graph)
    output_path = PROJECT_ROOT / "test_output.png"
    img.save(output_path)
    print(f"✓ 可视化成功，已保存到: {output_path}")
except Exception as e:
    print(f"✗ 可视化失败: {e}")
    # 不退出，因为可能缺少某些依赖

# 测试 8: JSON 导出
print("\n8. 测试 JSON 导出...")
try:
    from graphexecutor.visualization import export_scene_graph_json
    json_path = PROJECT_ROOT / "test_scene_graph.json"
    export_scene_graph_json(graph, str(json_path))
    print(f"✓ JSON 导出成功: {json_path}")
except Exception as e:
    print(f"✗ JSON 导出失败: {e}")

# 测试 9: JSON 加载
print("\n9. 测试从 JSON 加载...")
try:
    if json_path.exists():
        loaded_graph = load_scene_graph(json_path)
        print(f"✓ JSON 加载成功: {len(loaded_graph.nodes)} 个节点")
except Exception as e:
    print(f"✗ JSON 加载失败: {e}")

print("\n" + "=" * 60)
print("核心模块测试完成!")
print("=" * 60)
print("\n下一步:")
print("1. 启动服务: ./start_service.sh 或 python app/main.py")
print("2. 访问文档: http://localhost:8000/docs")
print("3. 运行 API 测试: python test_api.py")
print("=" * 60)
