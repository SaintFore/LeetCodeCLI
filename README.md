# 🧠 LeetCode FSRS CLI

> **科学刷题，拒绝遗忘。**
> 基于 **FSRS (Free Spaced Repetition Scheduler)** 算法的下一代 LeetCode 刷题助手。

[![AUR](https://img.shields.io/aur/version/leetcode-fsrs-cli?style=for-the-badge&color=blue)](https://aur.archlinux.org/packages/leetcode-fsrs-cli)
[![AUR Binary](https://img.shields.io/aur/version/leetcode-fsrs-cli-bin?style=for-the-badge&color=orange&label=AUR%20BIN)](https://aur.archlinux.org/packages/leetcode-fsrs-cli-bin)
[![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

---

## 🚀 为什么选择 LeetCode FSRS?

你是否遇到过：
*   刷过的题过几天就忘？
*   不知道今天该复习哪些题？
*   盲目刷题，效率低下？

**LeetCode FSRS CLI** 完美解决这些问题！它将先进的 **FSRS v4 记忆算法** 引入 LeetCode 刷题流程，为你量身定制复习计划。

### ✨ 核心特性

*   **🧠 FSRS v4 算法内核**: 比 Anki 更先进的记忆算法，精准预测遗忘曲线。
*   **🔄 真实数据同步**: 一键同步 LeetCode 账号提交记录，自动导入新题。
*   **⚡ 极速体验**: 纯命令行操作，零延迟，专注刷题本身。
*   **📱 跨平台支持**: 完美支持 Linux (Arch AUR) 和 Python 环境。
*   **🔧 高度可定制**: 算法参数、复习限制、快捷键...一切由你掌控。
*   **📦 零依赖模式**: 提供独立二进制包，无需 Python 环境即可运行。

---

## 📦 快速安装

### 🐧 Arch Linux (推荐)

我们提供了 **AUR** 包，支持源码编译和二进制直接安装：

| 版本 | 包名 | 说明 |
| :--- | :--- | :--- |
| **源码版** | `leetcode-fsrs-cli` | 适合开发者，依赖 Python |
| **二进制版** | `leetcode-fsrs-cli-bin` | **推荐**，零依赖，开箱即用 |

```bash
# 使用 paru 安装二进制版 (推荐)
paru -S leetcode-fsrs-cli-bin

# 或者使用 yay
yay -S leetcode-fsrs-cli-bin
```

### 🐍 Python (通用)

```bash
# 克隆仓库
git clone https://github.com/SaintFore/LeetCodeCLI.git
cd LeetCodeCLI

# 安装
pip install .
```

---

## 🎮 使用指南

### 1. 🔐 登录认证
获取你的 LeetCode Cookie，开启同步之旅。

```bash
leetcode-fsrs auth login
```
> *提示: 登录后 Cookie 会安全保存在本地，用于同步题目状态。*

### 2. 🔄 同步数据
一键拉取你的 LeetCode 提交记录。

```bash
leetcode-fsrs sync
```

### 3. ⚔️ 开始练习 (核心功能)
启动每日复习！系统会根据算法自动筛选出你最需要复习的题目。

```bash
leetcode-fsrs practice
```
*   **智能推荐**: 自动混合新题和复习题。
*   **默认限制**: 每天默认推荐 **10** 道题 (可通过 `--limit` 修改)。
*   **评分反馈**: 练习后根据回忆难度打分 (1-5)，算法自动调整下次复习时间。

### 4. 📊 查看统计
可视化你的学习进度。

```bash
leetcode-fsrs stats
```

---

## 🛠️ 常用命令速查

| 命令 | 描述 | 示例 |
| :--- | :--- | :--- |
| `practice` | **开始练习** (默认 10 题) | `leetcode-fsrs practice` |
| `sync` | **同步** LeetCode 数据 | `leetcode-fsrs sync` |
| `auth` | **认证** 管理 | `leetcode-fsrs auth status` |
| `stats` | 查看 **统计** | `leetcode-fsrs stats` |
| `list` | **列出** 所有题目 | `leetcode-fsrs list --status due` |
| `info` | 查看 **题目详情** | `leetcode-fsrs info 1` |
| `config` | **配置** 管理 | `leetcode-fsrs config list` |

---

## ⚙️ 高级配置

配置文件位于 `~/.config/leetcode-fsrs-cli/config.json`。
你可以通过命令直接修改：

```bash
# 修改每日复习上限为 20
leetcode-fsrs config set daily_review_limit 20

# 开启自动优化 FSRS 参数 (需要 scipy)
leetcode-fsrs config optimize
```

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=SaintFore/LeetCodeCLI&type=Date)](https://star-history.com/#SaintFore/LeetCodeCLI&Date)

---

## 🤝 贡献与支持

*   **Bug 反馈**: 请提交 [Issue](https://github.com/SaintFore/LeetCodeCLI/issues)
*   **代码贡献**: 欢迎 Pull Request！
*   **开源协议**: MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/SaintFore">SaintFore</a>
</p>