"""项目配置文件"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 模型配置
MODEL_PATH = os.getenv("MODEL_PATH", "/home/hdd4/lpz/FLUX.1-dev2")
DEVICE = os.getenv("DEVICE", "cuda:2")

# VLM 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-ws-H.PMXDRLL.1RTk.MEYCIQCGTfgSxyOrpr2kt-Hm54k1hCKgqndVN36bhtMh91480QIhALzjtH46qgaxPp9aX34SfU3Z7Zg0_tBr7Y9JFtsSpDSG")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "sk-ws-H.PMXDRLL.1RTk.MEYCIQCGTfgSxyOrpr2kt-Hm54k1hCKgqndVN36bhtMh91480QIhALzjtH46qgaxPp9aX34SfU3Z7Zg0_tBr7Y9JFtsSpDSG")
VLM_BASE_URL = os.getenv("VLM_BASE_URL", "")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8888))

# 输出目录
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# 图像生成默认参数
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 32
DEFAULT_GUIDANCE_SCALE = 3.5
