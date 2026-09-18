#!/bin/bash
# GraphExecutor 服务启动脚本

echo "=========================================="
echo "  GraphExecutor API 服务启动"
echo "=========================================="

# 检查 Python 版本
python_version=$(python3 --version 2>&1)
echo "Python 版本: $python_version"

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "警告: FastAPI 未安装"
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 创建输出目录
mkdir -p outputs
mkdir -p examples

echo ""
echo "启动服务..."
echo "主机: 0.0.0.0"
echo "端口: 8000"
echo ""
echo "访问以下地址查看文档:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动服务
python3 app/main.py
