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

import torch
from diffusers import QwenImage21Pipeline

MODEL_PATH = "/home/hdd4/lpz/Qwen-Image-2.1"
OUT_DIR = "story_output/portraits"
os.makedirs(OUT_DIR, exist_ok=True)

# ================== 三名固定角色设定卡 ==================
# 一个普通中式都市三人小队：把相貌、发型、服装锁死，作为后续参考图的 identity 锚点。
CHARACTERS = {
    "lin_wei": (
        "A 28-year-old Chinese man named Lin Wei, oval face, short neat black hair, "
        "thick straight eyebrows, warm brown eyes, clean-shaven, a small mole near "
        "the left corner of his mouth, wearing round thin-frame glasses, "
        "a light gray crew-neck sweater over a white shirt."
    ),
    "zhao_min": (
        "A 26-year-old Chinese woman named Zhao Min, round soft face, long straight "
        "black hair tied in a low ponytail, gentle almond eyes, light freckles across "
        "the nose, a single dimple on the right cheek, small silver stud earrings, "
        "wearing a dark green knit cardigan over a cream turtleneck."
    ),
    "chen_hao": (
        "A 32-year-old Chinese man named Chen Hao, square jaw, tanned skin, "
        "buzz-cut black hair, a short trimmed beard, a faint scar above the right "
        "eyebrow, broad shoulders, wearing a navy blue windbreaker jacket over "
        "a plain black t-shirt."
    ),
}

PORTRAIT_TEMPLATE = (
    "Studio portrait headshot of {desc} "
    "Neutral light gray background, soft even lighting, looking straight at the camera, "
    "sharp focus on the face, natural skin texture, photorealistic, 8k, "
    "high detail, front view, upper body."
)

# 固定每个角色一个 seed，保证肖像稳定、可复现
SEEDS = {"lin_wei": 101, "zhao_min": 202, "chen_hao": 303}

# ================== 加载模型 ==================
print("正在加载模型...")
pipe = QwenImage21Pipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
)
pipe.enable_model_cpu_offload()

# ================== 逐个生成肖像 ==================
for name, desc in CHARACTERS.items():
    prompt = PORTRAIT_TEMPLATE.format(desc=desc)
    print(f"\n🎨 生成角色肖像: {name}")
    print(f"提示词: {prompt}")

    generator = torch.Generator("cuda").manual_seed(SEEDS[name])
    image = pipe(
        prompt=prompt,
        width=1024,
        height=1024,
        num_inference_steps=30,
        generator=generator,
    ).images[0]

    out_path = os.path.join(OUT_DIR, f"{name}.png")
    image.save(out_path)
    print(f"✅ 已保存: {out_path}")

print("\n🎉 三张角色肖像已全部生成，作为下一步的参考图。")
