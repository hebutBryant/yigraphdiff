#!/usr/bin/env bash
# GraphExecutor 一键部署 + 运行
# 用法：bash deploy.sh
#
# 做三件事：
#   1. 校验 GraphAgent 环境与 torch/FluxPipeline 是否可用
#   2. 补装缺失的 Python 依赖（如 python-dotenv）
#   3. 调用 run_graphagent.sh 启动服务
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="/home/lipz/miniconda3/envs/GraphAgent/bin/python"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"

echo "[deploy] 1/3 校验 Python 环境 ..."
if [ ! -x "$PY" ]; then
  echo "[deploy] ✗ 找不到 GraphAgent 的 python: $PY" >&2
  echo "         请改用带 torch>=2.4 的环境，并修改本脚本与 run_graphagent.sh 的 PY 变量。" >&2
  exit 1
fi
"$PY" - <<'PYEOF'
import torch
from diffusers import FluxPipeline  # noqa: F401
assert torch.cuda.is_available(), "CUDA 不可用"
print(f"[deploy]   torch {torch.__version__} / CUDA {torch.version.cuda} / GPU x{torch.cuda.device_count()} OK")
PYEOF

echo "[deploy] 2/3 检查并补装依赖 ..."
"$PY" - <<'PYEOF' || "$PY" -m pip install --no-cache-dir python-dotenv >/dev/null
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec("dotenv") else 1)
PYEOF
echo "[deploy]   依赖就绪"

echo "[deploy] 3/3 启动服务 ..."
exec bash "$PROJECT_ROOT/run_graphagent.sh"
