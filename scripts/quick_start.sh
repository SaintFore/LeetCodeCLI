#!/bin/bash

# LeetCode FSRS CLI 快速启动脚本

echo "🚀 LeetCode FSRS CLI 快速启动"
echo "================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.8+"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 找不到 requirements.txt"
    exit 1
fi

echo "📦 安装依赖..."
pip install -r requirements.txt

echo "🔧 安装包..."
pip install .

echo ""
echo "✅ 安装完成！"
echo ""
echo "🎯 开始使用:"
echo "   leetcode-fsrs init        # 初始化项目"
echo "   leetcode-fsrs practice    # 开始练习"
echo "   leetcode-fsrs stats       # 查看统计"
echo "   leetcode-fsrs list        # 列出题目"
echo ""
echo "📖 更多命令:"
echo "   leetcode-fsrs --help"
echo ""