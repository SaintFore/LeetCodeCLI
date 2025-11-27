# LeetCode FSRS CLI 发布指南

## 🎉 项目状态

✅ **项目已成功完成并测试通过！**

## 📁 当前项目结构

```
leetcode-fsrs-cli/
├── leetcode_fsrs_cli/          # Python包目录
│   ├── __init__.py
│   ├── cli.py                  # CLI交互界面
│   ├── fsrs.py                 # FSRS算法核心
│   ├── leetcode.py             # 题目管理
│   ├── scheduler.py            # 复习调度器
│   ├── storage.py              # 数据持久化
│   └── data/                   # 默认配置数据
│       └── config.json
├── setup.py                    # Python包配置
├── PKGBUILD                    # Arch Linux包配置
├── .SRCINFO                    # AUR元数据
├── requirements.txt            # Python依赖
├── README.md                   # 用户文档
├── LICENSE                     # MIT许可证
├── quick_start.sh              # 快速启动脚本
├── PROJECT_SUMMARY.md          # 项目总结
├── GITHUB_SETUP.md             # GitHub发布指南
└── RELEASE_GUIDE.md            # 本文件
```

## 🚀 用户安装方法

### 方法1: 从AUR安装（推荐）

```bash
# 使用 paru
paru -S leetcode-fsrs-cli

# 或使用 yay
yay -S leetcode-fsrs-cli
```

### 方法2: 从GitHub安装

```bash
# 克隆仓库
git clone https://github.com/your-username/leetcode-fsrs-cli.git
cd leetcode-fsrs-cli

# 安装依赖和包
pip install .

# 或使用开发模式
pip install -e .
```

### 方法3: 从PyPI安装（如果发布）

```bash
pip install leetcode-fsrs-cli
```

## 📦 发布到GitHub

### 步骤1: 创建GitHub仓库

1. 在GitHub上创建新仓库：`leetcode-fsrs-cli`
2. 设置仓库为public
3. 添加描述："A CLI tool for LeetCode practice using FSRS spaced repetition algorithm"

### 步骤2: 推送代码

```bash
git init
git add .
git commit -m "Initial release: LeetCode FSRS CLI v1.0.0"
git branch -M main
git remote add origin https://github.com/your-username/leetcode-fsrs-cli.git
git push -u origin main
```

### 步骤3: 创建发布版本

1. 在GitHub仓库页面点击 "Releases"
2. "Draft a new release"
3. 标签：`v1.0.0`
4. 标题：`LeetCode FSRS CLI v1.0.0`
5. 描述：包含功能列表和使用说明
6. 附件：上传源代码压缩包

## 📋 发布到AUR

### 步骤1: 准备AUR包

确保以下文件正确：
- `PKGBUILD` - 包构建脚本
- `.SRCINFO` - AUR元数据
- 源代码压缩包

### 步骤2: 创建AUR仓库

```bash
# 克隆AUR仓库（需要AUR账户）
git clone ssh://aur@aur.archlinux.org/leetcode-fsrs-cli.git

# 复制必要文件
cp PKGBUILD .SRCINFO leetcode-fsrs-cli/

# 提交到AUR
cd leetcode-fsrs-cli
git add .
git commit -m "Initial package release v1.0.0"
git push
```

### 步骤3: 验证安装

```bash
# 从AUR安装测试
paru -S leetcode-fsrs-cli

# 测试功能
leetcode-fsrs --help
leetcode-fsrs init
leetcode-fsrs stats
```

## 🔧 用户使用指南

### 快速开始

```bash
# 1. 初始化项目
leetcode-fsrs init

# 2. 开始练习
leetcode-fsrs practice

# 3. 查看统计
leetcode-fsrs stats
```

### 主要命令

- `leetcode-fsrs init` - 初始化项目和数据目录
- `leetcode-fsrs practice` - 开始交互式练习
- `leetcode-fsrs stats` - 显示学习统计
- `leetcode-fsrs list` - 列出所有题目
- `leetcode-fsrs search <关键词>` - 搜索题目
- `leetcode-fsrs schedule` - 生成复习计划
- `leetcode-fsrs add <id> <title> <difficulty> <tags>` - 添加新题目

### 数据存储

- **数据目录**: `~/.config/leetcode-fsrs-cli/`
- **配置文件**: `config.json`
- **题目数据**: `questions.json`
- **复习记录**: `reviews.json`

## 🧪 功能验证清单

- [x] 包安装成功
- [x] 命令行工具可用
- [x] 项目初始化正常
- [x] 数据目录创建正确
- [x] 所有命令正常工作
- [x] 导入和相对导入正确
- [x] XDG标准目录使用

## 🔄 更新维护

### 版本更新流程

1. 更新代码和功能
2. 更新 `setup.py` 中的版本号
3. 更新 `PKGBUILD` 中的版本号
4. 重新生成 `.SRCINFO`
5. 创建新的GitHub发布
6. 更新AUR包

### 依赖管理

- 定期检查 `requirements.txt`
- 测试新版本兼容性
- 更新依赖版本

## 🐛 故障排除

### 常见问题

**Q: 命令找不到**
A: 确保包已正确安装，检查Python环境

**Q: 数据目录权限问题**
A: 确保对 `~/.config/` 有写权限

**Q: 导入错误**
A: 检查Python路径和包安装

### 调试信息

```bash
# 检查安装位置
which leetcode-fsrs

# 检查Python包
pip show leetcode-fsrs-cli

# 检查数据目录
ls -la ~/.config/leetcode-fsrs-cli/
```

## 📞 支持与贡献

- **GitHub Issues**: 报告问题和功能请求
- **文档**: 更新README和用户指南
- **测试**: 贡献测试用例
- **代码**: 提交Pull Request

## 🎊 发布成功！

你的LeetCode FSRS CLI工具现在已经：

✅ **功能完整** - 所有核心功能实现并测试
✅ **易于安装** - 支持多种安装方式
✅ **用户友好** - 清晰的命令行界面
✅ **标准兼容** - 使用XDG标准目录
✅ **可发布** - 准备好GitHub和AUR发布

**现在可以开始推广和使用你的工具了！** 🚀