import os
import subprocess

# ================== 自动选择空闲 GPU ==================
def pick_freest_gpu():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,memory.free",
             "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        free = []
        for line in out.strip().split("\n"):
            idx, mem = line.split(", ")
            free.append((int(idx), int(mem)))
        free.sort(key=lambda x: x[1], reverse=True)
        return free[0][0]
    except Exception as e:
        print(f"⚠️ 自动选择 GPU 失败，默认用 0。原因: {e}")
        return 0

best_gpu = pick_freest_gpu()
print(f"✅ 自动选择 GPU {best_gpu}（空闲显存最多）")
os.environ["CUDA_VISIBLE_DEVICES"] = str(best_gpu)

# ================== 导入依赖 ==================
import torch
from diffusers import QwenImage21Pipeline

# ================== 配置 ==================
MODEL_PATH = "/home/hdd4/lpz/Qwen-Image-2.1"

# ================== 加载模型 ==================
print("正在加载模型...")
pipe = QwenImage21Pipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
)
pipe.enable_model_cpu_offload()

# ================== 生成图片 ==================
prompt = "A beautiful Chinese garden with a pavilion by the lake, sunset, photorealistic, 8k"
print(f"提示词: {prompt}")

generator = torch.Generator("cuda").manual_seed(42)

image = pipe(
    prompt=prompt,
    width=1024,
    height=1024,
    num_inference_steps=20,
    generator=generator,
).images[0]

image.save("qwen21_test.png")
print("✅ 图片已保存为 qwen21_test.png")