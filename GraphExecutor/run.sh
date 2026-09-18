#!/bin/bash
# GraphExecutor 一键启动脚本

echo "=========================================="
echo "  GraphExecutor 服务一键启动"
echo "=========================================="

# 进入项目目录
cd /home/lipz/yigraphdiff/GraphExecutor

# 激活 conda 环境
echo "激活 conda base 环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base

# 检查依赖
echo "检查依赖..."
python -c "import fastapi, uvicorn, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装缺失的依赖..."
    pip install -r requirements.txt -q
fi

# 创建输出目录
mkdir -p outputs

echo ""
echo "=========================================="
echo "启动服务..."
echo "=========================================="
echo "访问以下地址查看文档:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo "  - 健康检查: http://localhost:8000/api/v1/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动服务
python app/main.py
