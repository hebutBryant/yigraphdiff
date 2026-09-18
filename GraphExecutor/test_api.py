#!/usr/bin/env python
"""测试 GraphExecutor API 的示例脚本"""

import requests
import json
from pathlib import Path

# API 基础 URL
BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """测试健康检查"""
    print("\n" + "=" * 60)
    print("1. 测试健康检查")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_predict_layout():
    """测试布局预测"""
    print("\n" + "=" * 60)
    print("2. 测试布局预测")
    print("=" * 60)

    data = {
        "prompt": "一只红色的猫坐在蓝色的椅子上，旁边有一棵绿色的植物",
        "width": 1024,
        "height": 1024
    }

    response = requests.post(f"{BASE_URL}/predict-layout", json=data)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"预测到 {len(result['elements'])} 个对象")
        print(f"预测到 {len(result['edges'])} 条边")
        print(f"\n摘要:\n{result.get('summary', 'N/A')}")
        return result
    else:
        print(f"错误: {response.text}")
        return None


def test_validate_scene_graph():
    """测试场景图验证"""
    print("\n" + "=" * 60)
    print("3. 测试场景图验证")
    print("=" * 60)

    # 加载示例场景图
    example_path = Path(__file__).parent / "examples" / "cafe_scene.json"

    if not example_path.exists():
        print(f"示例文件不存在: {example_path}")
        # 创建一个简单的示例
        scene_graph = {
            "high_level_description": "咖啡馆场景",
            "style_description": "摄影风格，自然光照",
            "background": "咖啡馆内部",
            "width": 1024,
            "height": 1024,
            "elements": [
                {
                    "id": "waiter",
                    "type": "object",
                    "bbox": [100, 200, 300, 800],
                    "desc": "穿着白色围裙的服务员"
                },
                {
                    "id": "table",
                    "type": "object",
                    "bbox": [350, 600, 750, 900],
                    "desc": "咖啡馆的木质桌子"
                }
            ],
            "edges": [
                {
                    "id": "waiter_near_table",
                    "source": "waiter",
                    "target": "table",
                    "type": "near",
                    "strength": 0.7
                }
            ]
        }
    else:
        with open(example_path, 'r', encoding='utf-8') as f:
            scene_graph = json.load(f)

    response = requests.post(f"{BASE_URL}/validate-scene-graph", json=scene_graph)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"验证成功!")
        print(f"节点数: {len(result['elements'])}")
        print(f"边数: {len(result['edges'])}")
        return result
    else:
        print(f"错误: {response.text}")
        return None


def test_visualize(scene_graph):
    """测试可视化"""
    print("\n" + "=" * 60)
    print("4. 测试可视化")
    print("=" * 60)

    if not scene_graph:
        print("没有场景图，跳过可视化测试")
        return

    data = {
        "scene_graph": scene_graph,
        "visualization_type": "bbox_overlay",
        "show_labels": True
    }

    response = requests.post(f"{BASE_URL}/visualize", json=data)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        output_path = Path("test_visualization.png")
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"可视化已保存到: {output_path}")
    else:
        print(f"错误: {response.text}")


def test_get_prompt(scene_graph):
    """测试获取完整提示"""
    print("\n" + "=" * 60)
    print("5. 测试获取完整提示")
    print("=" * 60)

    if not scene_graph:
        print("没有场景图，跳过提示测试")
        return

    response = requests.post(
        f"{BASE_URL}/get-prompt",
        json=scene_graph,
        params={"mode": "full"}
    )
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"完整提示:\n{result['prompt']}")
        print(f"\n节点数: {result['node_count']}")
        print(f"边数: {result['edge_count']}")
    else:
        print(f"错误: {response.text}")


def test_generate(scene_graph):
    """测试图像生成"""
    print("\n" + "=" * 60)
    print("6. 测试图像生成")
    print("=" * 60)

    if not scene_graph:
        print("没有场景图，跳过生成测试")
        return

    data = {
        "scene_graph": scene_graph,
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 32,
        "guidance_scale": 3.5,
        "save_visualization": True
    }

    response = requests.post(f"{BASE_URL}/generate", json=data)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"任务已创建:")
        print(f"  任务 ID: {result['task_id']}")
        print(f"  状态: {result['status']}")
        print(f"  消息: {result['message']}")

        if result.get('visualization_url'):
            print(f"  可视化 URL: {result['visualization_url']}")

        return result['task_id']
    else:
        print(f"错误: {response.text}")
        return None


def test_task_status(task_id):
    """测试获取任务状态"""
    print("\n" + "=" * 60)
    print("7. 测试获取任务状态")
    print("=" * 60)

    if not task_id:
        print("没有任务 ID，跳过状态查询")
        return

    response = requests.get(f"{BASE_URL}/task/{task_id}")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"任务信息:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print(" " * 20 + "GraphExecutor API 测试")
    print("=" * 80)

    try:
        # 1. 健康检查
        test_health()

        # 2. 布局预测
        predicted_graph = test_predict_layout()

        # 3. 场景图验证
        validated_graph = test_validate_scene_graph()

        # 选择一个场景图用于后续测试
        scene_graph = validated_graph or predicted_graph

        # 4. 可视化
        test_visualize(scene_graph)

        # 5. 获取提示
        test_get_prompt(scene_graph)

        # 6. 生成图像
        task_id = test_generate(scene_graph)

        # 7. 查询任务状态
        test_task_status(task_id)

        print("\n" + "=" * 80)
        print(" " * 30 + "测试完成!")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到服务器")
        print("请确保服务正在运行: python app/main.py")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
