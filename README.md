# LeetCode FSRS CLI

基于FSRS（Free Spaced Repetition Scheduler）记忆算法的LeetCode刷题CLI工具，通过科学的间隔重复算法帮助你高效刷题。

## 🚀 特性

- **科学记忆算法**: 使用FSRS v4算法计算最优复习间隔
- **智能复习调度**: 根据记忆状态自动安排复习计划
- **进度跟踪**: 详细的学习统计和分析
- **便捷使用**: 命令行界面，随时随地可用
- **数据持久化**: 本地JSON存储，无需数据库

## 📦 安装

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. 克隆或下载项目
```bash
git clone <repository-url>
cd leetcode-fsrs-cli
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 设置可执行权限
```bash
chmod +x main.py
```

## 🎯 快速开始

### 1. 初始化项目
```bash
python main.py init
```
这将创建必要的目录结构和示例题目。

### 2. 开始练习
```bash
python main.py practice
```
系统会根据FSRS算法安排需要复习的题目。

### 3. 查看统计
```bash
python main.py stats
```
查看学习进度和统计数据。

## 📋 命令详解

### 基础命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化项目 | `python main.py init` |
| `add` | 添加题目 | `python main.py add 1 "Two Sum" easy "array,hash-table"` |
| `practice` | 开始练习 | `python main.py practice --limit 20` |
| `stats` | 显示统计 | `python main.py stats` |
| `schedule` | 复习计划 | `python main.py schedule` |
| `list` | 列出题目 | `python main.py list --difficulty easy` |
| `search` | 搜索题目 | `python main.py search "binary"` |

### 详细用法

#### 添加题目
```bash
python main.py add <题目ID> <题目名称> <难度> <标签>
```

示例：
```bash
python main.py add 1 "Two Sum" easy "array,hash-table"
python main.py add 2 "Add Two Numbers" medium "linked-list,math"
```

#### 练习模式
```bash
python main.py practice [--limit 数量]
```

在练习过程中，系统会显示题目信息并要求你评价回忆难度：
- **1**: 完全忘记
- **2**: 很困难
- **3**: 中等难度
- **4**: 简单
- **5**: 完美掌握

#### 题目筛选
```bash
# 按难度筛选
python main.py list --difficulty easy
python main.py list --difficulty medium
python main.py list --difficulty hard

# 按标签筛选
python main.py list --tag "array"
python main.py list --tag "dynamic-programming"

# 搜索题目
python main.py search "tree"
python main.py search "sort"
```

## 🧠 FSRS算法说明

### 算法原理
FSRS（Free Spaced Repetition Scheduler）是一种基于记忆模型的间隔重复算法，它通过以下因素计算最优复习间隔：

- **记忆稳定性**: 表示记忆的牢固程度
- **题目难度**: 题目的固有难度
- **用户表现**: 每次复习的评分
- **时间衰减**: 记忆随时间的自然遗忘

### 评分系统
在每次复习时，你需要根据回忆难度给出1-5分的评分：

| 评分 | 描述 | 含义 |
|------|------|------|
| 1 | 完全忘记 | 完全不记得解法 |
| 2 | 很困难 | 需要很长时间才能想起 |
| 3 | 中等难度 | 需要一些提示才能完成 |
| 4 | 简单 | 能够独立完成但不够熟练 |
| 5 | 完美掌握 | 能够快速且准确地完成 |

### 间隔计算
基于你的评分，FSRS算法会计算下一次复习的最佳时间：
- 评分越高，间隔越长
- 评分越低，间隔越短
- 难度高的题目会有更频繁的复习

## 📊 数据文件说明

项目使用JSON文件存储数据：

- `data/questions.json`: 题目数据
- `data/reviews.json`: 复习记录
- `data/config.json`: 用户配置

### 备份数据
```bash
# 手动备份
cp -r data/ backup/
```

## 🔧 配置选项

你可以通过编辑 `data/config.json` 文件来自定义设置：

```json
{
    "daily_review_limit": 20,
    "auto_update_due": true,
    "show_progress_bar": true,
    "language": "zh",
    "fsrs_params": {
        "request_retention": 0.9,
        "maximum_interval": 36500,
        "easy_bonus": 1.3,
        "hard_factor": 1.2
    }
}
```

## 🎨 使用技巧

### 高效刷题建议
1. **每日坚持**: 每天完成当天的复习计划
2. **诚实评价**: 根据真实回忆难度给出评分
3. **定期回顾**: 使用 `stats` 命令查看学习进度
4. **循序渐进**: 从简单题目开始，逐步增加难度

### 题目管理建议
1. **分类标签**: 为题目添加准确的标签
2. **难度分级**: 合理评估题目难度
3. **定期导入**: 批量导入新题目

## 🐛 故障排除

### 常见问题

**Q: 初始化失败**
A: 检查Python版本和依赖安装

**Q: 练习时没有题目**
A: 确保已添加题目并运行 `init` 命令

**Q: 数据丢失**
A: 定期备份 `data/` 目录

### 日志查看
程序运行日志会输出到控制台，如有问题请查看错误信息。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License

## 🙏 致谢

- FSRS算法: [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki)
- LeetCode: 提供优质的算法题目

---

**开始你的高效刷题之旅吧！** 🚀