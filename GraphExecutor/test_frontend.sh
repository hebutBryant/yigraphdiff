#!/bin/bash
# GraphExecutor 前端功能测试脚本

API="http://localhost:8888/api/v1"

echo "═══════════════════════════════════════════════════════════"
echo "  GraphExecutor 前端功能测试"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. 健康检查
echo "1️⃣  测试健康检查..."
HEALTH=$(curl -s $API/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ 健康检查通过"
else
    echo "   ❌ 健康检查失败"
    exit 1
fi
echo ""

# 2. 布局预测
echo "2️⃣  测试布局预测..."
PREDICT=$(curl -s -X POST $API/predict-layout \
  -H "Content-Type: application/json" \
  -d '{"prompt":"一只猫坐在椅子上","width":1024,"height":1024}')

NODE_COUNT=$(echo "$PREDICT" | grep -o '"elements"' | wc -l)
if [ "$NODE_COUNT" -gt 0 ]; then
    echo "   ✅ 布局预测成功"
    echo "   📊 场景图: $(echo "$PREDICT" | grep -o '"id"' | wc -l) 个对象"
else
    echo "   ❌ 布局预测失败"
fi
echo ""

# 3. 前端页面
echo "3️⃣  测试前端页面..."
FRONTEND=$(curl -s http://localhost:8888/)
if echo "$FRONTEND" | grep -q "GraphExecutor"; then
    echo "   ✅ 前端页面加载成功"
else
    echo "   ❌ 前端页面加载失败"
fi
echo ""

# 4. 静态资源
echo "4️⃣  测试静态资源..."
CSS=$(curl -s http://localhost:8888/frontend/style.css)
JS=$(curl -s http://localhost:8888/frontend/app.js)
if echo "$CSS" | grep -q "GraphExecutor" && echo "$JS" | grep -q "API"; then
    echo "   ✅ CSS 和 JS 加载成功"
else
    echo "   ❌ 静态资源加载失败"
fi
echo ""

# 5. API 文档
echo "5️⃣  测试 API 文档..."
DOCS=$(curl -s http://localhost:8888/docs)
if echo "$DOCS" | grep -q "swagger"; then
    echo "   ✅ API 文档可访问"
else
    echo "   ❌ API 文档不可用"
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  测试完成！"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 访问地址:"
echo "   • 前端: http://localhost:8888/"
echo "   • 文档: http://localhost:8888/docs"
echo ""
