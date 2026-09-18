#!/usr/bin/env bash
# GraphExecutor 启动脚本 —— 使用 GraphAgent 环境（torch 2.12 + FluxPipeline 可用）
#
# 固化三条避坑规则：
#   1. 直接用 GraphAgent 的 python，不用 conda activate（会触发 shell exit 144）
#   2. PYTHONPATH + cwd 钉在项目根，保证加载本项目的 graphexecutor
#      （而不是 /home/lipz/GraphDiff 下的同名包）
#   3. 不开 --reload（reloader 子进程不继承 sys.path，会把路径带偏）

set -euo pipefail

PROJECT_ROOT="/home/lipz/yigraphdiff/GraphExecutor"
PY="/home/lipz/miniconda3/envs/GraphAgent/bin/python"
HOST="0.0.0.0"
PORT="${PORT:-8888}"

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"

# 若已有占用同端口的本项目进程，先停掉
OLD_PID=$(pgrep -f "uvicorn app.main:app.*--port ${PORT}" || true)
if [ -n "$OLD_PID" ]; then
  echo "[run] 停止旧服务 PID: $OLD_PID"
  kill $OLD_PID 2>/dev/null || true
  sleep 2
fi

echo "[run] 启动服务： $PY (GraphAgent) 端口 $PORT"
exec "$PY" -m uvicorn app.main:app --host "$HOST" --port "$PORT"
