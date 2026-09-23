import json
import os
import subprocess
from pathlib import Path

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
from PIL import Image
from diffusers import QwenImage21Pipeline

MODEL_PATH = "/home/hdd4/lpz/Qwen-Image-2.1"
ROOT = Path(__file__).resolve().parent
PORTRAIT_DIR = ROOT / "story_output/portraits"
OUT_DIR = ROOT / "story_output/crime_comics"
os.makedirs(OUT_DIR, exist_ok=True)

STORIES = {
    "extortion": {
        "title": "匿名来信",
        "summary": "林伟收到以曝光隐私为要挟的匿名信息，在门口发现信封，惊恐地确认自己正被监视，最终整理证据准备报案。",
        "character": "lin_wei",
        "identity": "Lin Wei is the exact person in <image1>: round thin-frame glasses, neat short black hair, light gray sweater over a white shirt. Preserve his face and outfit.",
        "scenes": [
            ("01_message", "23:18。屏幕亮起，陌生人以曝光隐私勒索林伟。",
             "Story beat 1 of a realistic crime comic, 23:18 in Lin Wei's modest Chinese apartment during a rainstorm. His phone suddenly lights up with an anonymous blackmail notification; the screen is a blurred glow with no legible lettering. Lin Wei sits alone at a wooden desk, eyes widening behind his round glasses, brows lifting, lips parting, one thumb frozen a few centimeters above the screen. A mug of tea sits untouched. Intimate medium close shot from desk height; his face and phone are both visible. Warm desk lamp on one cheek, cold blue rainlight on the other, shallow focus, natural skin texture and restrained dread."),
            ("02_envelope", "门外传来轻响，他发现一只没有署名的信封。",
             "Story beat 2, minutes later in the same apartment. Lin Wei has opened his front door only a crack; he crouches alone in the narrow empty hallway and reaches for a plain kraft envelope lying on the threshold. His shoulders are tight, his other hand grips the doorframe, his eyes dart toward the unseen end of the corridor, and his mouth is tense with fear. The gray sweater, white shirt and round glasses match the previous panel. Low diagonal camera angle, full upper body and envelope clearly readable as shapes, stark overhead corridor light, deep shadow behind the door, realistic concrete floor and damp shoe marks. The hallway is completely empty."),
            ("03_proof", "信封里是自家窗户的偷拍照片，恐惧变得具体。",
             "Story beat 3, back at the desk. Lin Wei sits alone opening the same kraft envelope with trembling fingers. It contains a small surveillance photograph of his own rain-streaked apartment window, shown without any person in the photograph. His glasses have slipped slightly down his nose; one hand covers his mouth, his eyes are fixed wide on the image, and his breathing seems arrested. Tight three-quarter close shot so his shocked expression, the envelope and the photograph dominate. Warm lamp light, blue night window in the background, tactile paper fibers, cinematic suspense without sensationalism."),
            ("04_decision", "天快亮时，他把信息和信封一同留存，决定求助。",
             "Story beat 4, first gray light before dawn in the same apartment. Lin Wei sits alone at the desk, photographing the anonymous message and the kraft envelope as evidence with a second device; the device displays no readable text. His hands are steadier now, his jaw set, eyes tired and frightened but deliberate. Place the envelope, phone and evidence sleeves on the desk in a clear visual triangle. Medium shot with face and hands visible, cool sunrise replacing the night lamp, rain fading outside, realistic domestic clutter. End on a quiet decision to seek help, not a triumphant pose."),
        ],
    },
    "theft": {
        "title": "消失的怀表",
        "summary": "闭馆后，赵敏发现古董怀表失踪；她检查展柜边缘的线索，循迹到储物室，在暗格里找回怀表。",
        "character": "zhao_min",
        "identity": "Zhao Min is the exact person in <image1>: low black ponytail, dark green knit cardigan over a cream turtleneck, small silver stud earrings. Preserve her face and outfit.",
        "scenes": [
            ("01_discovery", "闭馆时，展柜里的银色怀表不见了。",
             "Story beat 1 of a realistic crime comic at closing time in a small Chinese antiquarian gallery. Zhao Min stands alone before an open brass-framed glass display case. Its burgundy velvet cushion holds only the pale round impression of a missing silver pocket watch. She leans forward abruptly, eyebrows knitting, lips parting in disbelief, one hand hovering over the empty recess without touching it. Medium-wide shot balancing her readable face and the empty case; warm gallery spotlights against cool dusk at the windows, faint fingerprints on the glass, aged wooden cabinets and honest everyday detail."),
            ("02_trace", "她发现锁扣上挂着一缕红色绒线。",
             "Story beat 2 in the same empty gallery. Zhao Min crouches alone at the brass display-case latch, angling a small flashlight across a single burgundy thread snagged on the metal. Her expression sharpens from alarm to concentration; she holds her breath and points with one finger without touching the thread. The green cardigan, cream turtleneck, ponytail and earrings remain consistent. Close three-quarter shot showing her face, careful hand and latch together, raking flashlight beam revealing fine scratches in brass and dust on glass, the rest of the gallery falling softly out of focus."),
            ("03_search", "储物室里，一只抽屉的红绒内衬露出破口。",
             "Story beat 3 in the gallery's cramped storage room later that evening. Zhao Min is alone, kneeling beside a bank of old wooden drawers. She pulls one drawer halfway open and notices a small torn patch in its burgundy velvet lining matching the thread from the display-case latch. Her body is tense and still, gaze focused downward, mouth pressed into a thin line as she realizes this is the hiding place. Medium shot with face, hands and the torn lining visible, one warm utility bulb, tall shelves receding into shadow, realistic wood grain and fabric pile."),
            ("04_recovery_v2", "她掀开内衬，找到了失踪的怀表。",
             "Story beat 4 in the same storage room. ONE continuous camera exposure, ONE viewpoint, ONE Zhao Min, ONE face and ONE body. Zhao Min kneels alone beside the open wooden drawer and gently holds the recovered antique silver pocket watch in one palm above the torn burgundy velvet lining. Her face, the watch and the drawer are visible together in a single medium shot; she exhales with quiet relief while staying alert. Warm light catches scratched silver, dark shelves behind her, natural expression. Do not make a split screen, collage, inset, diptych, duplicated face, or extra panel."),
        ],
    },
    "collision": {
        "title": "雨夜逃离",
        "summary": "陈浩在雨夜撞倒路边无人停放的红色电动车；惊慌之下，他没有留下信息，而是驾车离开现场。",
        "character": "chen_hao",
        "identity": "Chen Hao is the exact person in <image1>: buzz-cut black hair, short trimmed beard, navy windbreaker over a black T-shirt. Preserve his face and outfit.",
        "scenes": [
            ("01_impact", "车头撞上路边无人停放的红色电动车。",
             "Story beat 1 of a realistic crime comic on a deserted Chinese city street during heavy rain at midnight. A dark sedan driven by Chen Hao has just struck an unoccupied red electric scooter parked at the curb. The scooter lies on its side with a broken mirror; the sedan's front-left headlight and bumper are cracked. Chen Hao is the only human, visible through the driver-side window, gripping the steering wheel with both hands, eyes wide and mouth open in shock. Wide three-quarter exterior view, frozen raindrops and wet asphalt reflecting amber streetlights, physically plausible collision aftermath, no rider, no pedestrian, no injury or blood."),
            ("02_aftermath_v2", "他下车查看，发现车头和电动车都已损坏。",
             "Story beat 2, less than a minute after the crash. It is MIDNIGHT on the same deserted street: black sky, no daylight, no dawn, no ambient blue hour; ONLY amber streetlamps and headlights illuminate the heavy rain. ONE continuous camera photograph with ONE Chen Hao. He stands alone between his dark sedan's cracked front-left bumper and the red scooter LYING HORIZONTALLY ON ITS SIDE at the curb, broken mirror on the wet ground. He bends at the waist, one hand on his knee and the other pressed against his forehead, eyes fixed on the damage, jaw clenched in shock. Medium-wide low roadside shot with his face and both damaged vehicles visible, wet navy windbreaker and reflective asphalt. No extra figures or collage."),
            ("03_choice_v3", "街上空无一人，他犹豫片刻，又握住车门。",
             "Story beat 3, still MIDNIGHT seconds after the crash: black sky, no daylight or dawn, ONLY amber streetlamps and headlights in the heavy rain. ONE continuous camera photograph, ONE Chen Hao, ONE car, ONE red scooter. Chen Hao stands alone by the open driver door of the dark sedan, one hand gripping the wet door frame; his body turns toward the seat while his anxious face looks back over his shoulder. Just behind him at the curb the red scooter is FULLY HORIZONTAL, LYING FLAT ON ITS SIDE on the asphalt with a broken mirror beside it. The car's front-left bumper stays cracked. Medium-wide roadside shot with his face, door and fallen scooter visible together, dark wet street and guilt in his posture. No collage, duplicated person, extra panel or other human."),
            ("04_escape_v2", "最后，他重新坐进驾驶座，驶离事故现场。",
             "Story beat 4, seconds later. ONE continuous camera photograph, ONE viewpoint, ONE Chen Hao, ONE car, ONE red scooter. Exterior three-quarter front view of the dark sedan MOVING AWAY through rain; Chen Hao is visibly driving inside behind the steering wheel, eyes frightened and fixed on the road, navy windbreaker and buzz cut recognizable. The car's front-left bumper is still cracked. Far behind the departing car, the red scooter STILL LIES ON ITS SIDE at the curb, small but recognizable. Wet streetlight reflections and modest motion blur convey escape. No split screen, collage, inset, duplicated face, repeated car, extra panel or other human."),
        ],
    },
}

STYLE = (
    "Single panel of a coherent photorealistic cinematic crime comic. "
    "Use <image1> as the identity reference for the one visible person. "
    "Exactly one adult human in the entire image. No bystanders, silhouettes, "
    "faces on screens, or extra figures. Keep the recurring person, clothing, "
    "location and props consistent across panels. Natural anatomy and hands, "
    "subtle believable facial acting, refined composition, high detail, "
    "no speech bubbles, no captions, no readable text, no watermark."
)

jobs = []
for story_key, story in STORIES.items():
    for scene_key, caption, scene in story["scenes"]:
        jobs.append({
            "story": story_key, "title": story["title"],
            "summary": story["summary"], "character": story["character"],
            "scene": scene_key, "caption": caption,
            "prompt": f"{scene} {story['identity']} {STYLE}",
            "image": str(OUT_DIR / story_key / f"{scene_key}.png"),
        })

(OUT_DIR / "prompts.json").write_text(
    json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8"
)

if all(Path(job["image"]).exists() for job in jobs):
    print("✅ 十二个分镜已存在，无需重复加载模型。")
    raise SystemExit(0)

# ================== 加载模型 ==================
print("正在加载模型...")
pipe = QwenImage21Pipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
)
pipe.enable_model_cpu_offload()

# ================== 逐场景生成 ==================
# 为每个分镜指定稳定 seed，便于复现。
BASE_SEED = 777

for i, job in enumerate(jobs):
    out_path = Path(job["image"])
    if out_path.exists():
        print(f"⏭️ 已存在，跳过: {out_path}")
        continue
    print(f"\n🎬 生成场景: {job['story']}/{job['scene']}")
    print(f"提示词: {job['prompt']}")
    ref_image = Image.open(PORTRAIT_DIR / f"{job['character']}.png").convert("RGB")

    generator = torch.Generator("cuda").manual_seed(BASE_SEED + i)
    image = pipe(
        prompt=job["prompt"],
        image=[ref_image],         # 仅传入当前角色，始终对应 <image1>
        width=1024,
        height=1024,
        num_inference_steps=40,    # 官方推荐 40 步
        true_cfg_scale=1.0,        # 官方推荐关闭 CFG
        generator=generator,
    ).images[0]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    print(f"✅ 已保存: {out_path}")

print("\n🎉 三个犯罪故事、十二个单人分镜已生成。")
