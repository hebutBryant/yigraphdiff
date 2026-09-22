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
from PIL import Image
from diffusers import QwenImage21Pipeline

# ================== 配置 ==================
MODEL_PATH = "/home/hdd4/lpz/Qwen-Image-2.1"

# 参考图路径（你可以换成任何一张图）
REFERENCE_IMAGE = "/home/wangmh/projects/flux2/crime/image/reference.jpg"
OUTPUT_IMAGE = "qwen21_ref_test.png"

# ================== 加载模型 ==================
print("正在加载模型...")
pipe = QwenImage21Pipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
)
pipe.enable_model_cpu_offload()

# ================== 加载参考图 ==================
ref_image = Image.open(REFERENCE_IMAGE).convert("RGB")
print(f"✅ 已加载参考图：{REFERENCE_IMAGE}")

# ================== 提示词 ==================
# 使用 <image1> 语法明确指向参考图
prompt = (
    "Use <image1> as the primary character identity. "
    "Place the person in a sunny modern campus, wearing a casual outfit, "
    "natural lighting, photorealistic, 8k."
)

# ================== 生成 ==================
print("正在生成图片...")
generator = torch.Generator("cuda").manual_seed(42)

image = pipe(
    prompt=prompt,
    image=[ref_image],          # 传入参考图列表
    width=1024,
    height=1024,
    num_inference_steps=40,     # 官方推荐 40 步
    true_cfg_scale=1.0,         # 官方推荐关闭 CFG
    generator=generator,
).images[0]

image.save(OUTPUT_IMAGE)
print(f"✅ 图片已保存为 {OUTPUT_IMAGE}")