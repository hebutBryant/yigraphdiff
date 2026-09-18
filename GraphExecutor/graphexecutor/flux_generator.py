"""FLUX 图像生成模块

基于场景图构建提示词并调用 FLUX 生成图像。

说明：本项目未包含 GraphDiff 的注意力控制模块
(token_region_aligner / edge_compiler / attention_hook 等)，
因此 _GRAPHDIFF_AVAILABLE 恒为 False，统一走基础生成。
若日后接入这些模块，将 _GRAPHDIFF_AVAILABLE 置 True 并实现
_generate_with_control 即可。
"""

import os
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

# GraphExecutor 注意力控制模块在本项目中不可用
_GRAPHDIFF_AVAILABLE = False


class FLUXGenerator:
    """FLUX 图像生成器（延迟加载模型）"""

    def __init__(
        self,
        model_path: str = "/home/hdd4/lpz/FLUX.1-dev2",
        device: str = "cuda:2",
    ):
        self.model_path = Path(model_path)
        self.device = device
        self.pipe = None
        self._loaded = False

    def load_model(self):
        """加载 FLUX 模型（首次生成时触发，约 3-5 分钟）"""
        if self._loaded:
            return

        print(f"[FLUX] 正在加载模型: {self.model_path}")
        print(f"[FLUX] 设备: {self.device}")

        from diffusers import FluxPipeline

        self.pipe = FluxPipeline.from_pretrained(
            str(self.model_path),
            torch_dtype=torch.bfloat16,
        )
        self.pipe = self.pipe.to(self.device)
        self._loaded = True
        print("[FLUX] 模型加载完成")

    def generate_from_scene_graph(
        self,
        scene_graph,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 32,
        guidance_scale: float = 3.5,
        seed: Optional[int] = None,
        control_mode: str = "none",
        bias_scale: float = 0.5,
    ) -> Image.Image:
        """从场景图生成图像"""
        if not self._loaded:
            self.load_model()

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(int(seed))

        from graphexecutor.graph_ir import build_full_prompt
        prompt = build_full_prompt(scene_graph)

        print(f"[FLUX] 提示词: {prompt}")
        print(f"[FLUX] 控制模式: {control_mode}")

        if control_mode != "none" and not _GRAPHDIFF_AVAILABLE:
            print("[FLUX] 提示: 注意力控制模块不可用，使用基础生成")

        output = self.pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )
        return output.images[0]


# 全局生成器实例（延迟初始化）
_generator: Optional[FLUXGenerator] = None


def get_generator() -> FLUXGenerator:
    """获取全局生成器实例"""
    global _generator
    if _generator is None:
        from config import MODEL_PATH, DEVICE
        _generator = FLUXGenerator(model_path=MODEL_PATH, device=DEVICE)
    return _generator


def generate_image(
    scene_graph,
    width: int = 1024,
    height: int = 1024,
    num_inference_steps: int = 32,
    guidance_scale: float = 3.5,
    seed: Optional[int] = None,
    control_mode: str = "none",
) -> Image.Image:
    """便捷函数：从场景图生成图像"""
    generator = get_generator()
    return generator.generate_from_scene_graph(
        scene_graph=scene_graph,
        width=width,
        height=height,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        seed=seed,
        control_mode=control_mode,
    )
