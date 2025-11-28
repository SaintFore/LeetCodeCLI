# LeetCode FSRS CLI

基于FSRS（Free Spaced Repetition Scheduler）记忆算法的LeetCode刷题CLI工具，通过科学的间隔重复算法帮助你高效刷题。

[![AUR](https://img.shields.io/aur/version/leetcode-fsrs-cli)](https://aur.archlinux.org/packages/leetcode-fsrs-cli)
[![AUR](https://img.shields.io/aur/version/leetcode-fsrs-cli-bin)](https://aur.archlinux.org/packages/leetcode-fsrs-cli-bin)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.6.2-blue.svg)](https://github.com/SaintFore/LeetCodeCLI/releases)

## ✨ 特性概览

- **🎯 科学记忆算法**: 基于FSRS v4间隔重复算法，优化记忆保留
- **⚙️ 高度可配置**: 支持自定义FSRS算法参数，适应不同记忆能力
- **🔄 真实数据同步**: 支持LeetCode账号登录，自动同步提交记录
- **🚀 零依赖二进制版**: 提供完全独立的二进制版本，无需Python环境
- **📊 智能复习调度**: 根据记忆稳定性自动计算最优复习间隔
- **🔧 轻量级设计**: 从6个依赖优化到2个必需依赖，极致精简
- **📱 跨平台支持**: 支持Arch Linux (AUR) 和Python环境
- **⚡ 自动化发布**: GitHub Actions自动更新AUR包
- **📝 完整文档**: 详细的用户指南和维护记录

## 🎉 版本亮点 (v1.5.1)

- ✅ **FSRS参数自定义**: 支持修改算法权重和参数，适应个体差异
- ✅ **配置管理**: 新增 `config` 命令组，方便管理所有设置
- ✅ **真实LeetCode认证**: 支持Cookie登录，获取个人数据
- ✅ **自动同步**: 同步LeetCode最近提交记录到本地
- ✅ **自动化发布流程**: GitHub Actions自动更新AUR双版本

## 🚀 快速开始

### 安装

#### Arch Linux (AUR)

**源码版** (推荐开发者)
```bash
# 使用 paru
paru -S leetcode-fsrs-cli

# 或使用 yay
yay -S leetcode-fsrs-cli
```

**二进制版** (零依赖，推荐普通用户)
```bash
# 使用 paru
paru -S leetcode-fsrs-cli-bin

# 或使用 yay
yay -S leetcode-fsrs-cli-bin
```

**版本对比**:
- **源码版** (`leetcode-fsrs-cli`): 需要安装 `python-click` 和 `python-requests` 依赖
- **二进制版** (`leetcode-fsrs-cli-bin`): 完全独立，无需安装任何Python包

#### 从源码安装
```bash
# 克隆仓库
git clone https://github.com/SaintFore/LeetCodeCLI.git
cd LeetCodeCLI

# 安装包 (会自动安装依赖)
pip install .

# 或开发模式安装
pip install -e .
```

**注意**: 当前GitHub仓库名为 `LeetCodeCLI`，但包名为 `leetcode-fsrs-cli`

### 使用方法

```bash
# 1. 登录 LeetCode (需要 Cookie)
leetcode-fsrs auth login

# 2. 同步题目数据
leetcode-fsrs sync

# 3. 开始练习
leetcode-fsrs practice

# 4. 查看复习计划
leetcode-fsrs practice --plan

# 5. 查看统计
leetcode-fsrs stats

# 6. 修改配置 (可选)
leetcode-fsrs config list
leetcode-fsrs config set fsrs_params.request_retention 0.85
```

## 📋 命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `auth` | 认证管理 | `leetcode-fsrs auth login` |
| `sync` | 同步题目 | `leetcode-fsrs sync` |
| `practice` | 开始练习 | `leetcode-fsrs practice --limit 20` |
| `stats` | 显示统计 | `leetcode-fsrs stats` |
| `list` | 列出题目 | `leetcode-fsrs list --difficulty easy` |
| `info` | 查看题目详情 | `leetcode-fsrs info 1` |
| `config` | 配置管理 | `leetcode-fsrs config set ...` |
| `optimize` | 自动优化参数 | `leetcode-fsrs config optimize` |

## 🧠 FSRS算法

FSRS（Free Spaced Repetition Scheduler）是一种基于记忆模型的间隔重复算法：

- **科学记忆**: 根据记忆稳定性计算最优复习间隔
- **自适应学习**: 根据用户表现调整复习频率
- **长期记忆**: 优化长期记忆保留效果

### 评分系统
在练习时，根据回忆难度给出1-5分：

- **1**: 完全忘记
- **2**: 很困难
- **3**: 中等难度
- **4**: 简单
- **5**: 完美掌握

## 📊 数据存储

- **数据目录**: `~/.config/leetcode-fsrs-cli/`
- **题目数据**: `questions.json`
- **复习记录**: `reviews.json`
- **用户配置**: `config.json`

## 🔧 配置选项

编辑 `~/.config/leetcode-fsrs-cli/config.json` 自定义设置：

```json
{
    "daily_review_limit": 20,
    "auto_update_due": true,
    "show_progress_bar": true,
    "language": "zh"
}
```

## 🐛 故障排除

### 常见问题

**Q: 命令找不到**
A: 确保包已正确安装，检查Python环境

**Q: 数据目录权限问题**
A: 确保对 `~/.config/` 有写权限

**Q: 练习时没有题目**
A: 确保已运行 `leetcode-fsrs sync` 同步题目

### 调试信息

```bash
# 检查安装
which leetcode-fsrs

# 检查数据目录
ls -la ~/.config/leetcode-fsrs-cli/

# 查看详细帮助
leetcode-fsrs --help
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- FSRS算法: [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki)
- LeetCode: 提供优质的算法题目

---

**开始你的高效刷题之旅！** 🚀