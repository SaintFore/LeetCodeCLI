# 🚀 LeetCode FSRS CLI

LeetCode FSRS CLI 是一个基于 [FSRS (Free Spaced Repetition Scheduler)](https://github.com/open-spaced-repetition/fsrs.js) 算法的 LeetCode 刷题工具。它可以帮助你更高效地复习和记忆 LeetCode 题目。

## ✨ 主要功能

- **智能复习**: 基于 FSRS 算法，智能安排复习计划，让你的学习更高效。
- **自动同步**: 自动从你的 LeetCode 账户同步题目列表和提交记录。
- **数据统计**: 提供详细的学习统计数据，让你对自己的学习进度一目了然。
- **高度可配置**: 支持自定义 FSRS 算法参数，以适应你的个人学习习惯。
- **自动优化**: 支持根据你的复习历史自动优化 FSRS 算法参数。
- **跨平台**: 支持 Windows, macOS 和 Linux。

## 🛠️ 安装

1.  **从 PyPI 安装**:
    ```bash
    pip install leetcode-fsrs-cli
    ```
2.  **从源码安装**:
    ```bash
    git clone https://github.com/SaintFore/LeetCodeCLI.git
    cd LeetCodeCLI
    pip install .
    ```

## 🚀 使用方法

### 1. 登录

在使用前，你需要先登录你的 LeetCode 账户。

```bash
leetcode-fsrs auth login
```

然后根据提示输入你的 LeetCode cookie。

### 2. 同步题目

登录后，你需要同步你的 LeetCode 题目。

```bash
leetcode-fsrs sync
```

### 3. 开始练习

同步完成后，你就可以开始练习了。

```bash
leetcode-fsrs practice
```

程序会根据 FSRS 算法为你安排复ri习计划。

### 4. 查看统计

你可以随时查看你的学习统计数据。

```bash
leetcode-fsrs stats
```

### 5. 列出题目

你也可以列出你的所有题目。

```bash
leetcode-fsrs list
```

## ⚙️ 配置

你可以通过 `config` 命令来配置你的 LeetCode FSRS CLI。

```bash
# 列出所有配置
leetcode-fsrs config list

# 设置每日复习上限
leetcode-fsrs config set daily_review_limit 20

# 设置 FSRS 算法参数
leetcode-fsrs config set-weights "0.8,1.5,3.7,..."
```

## 🤝 贡献

欢迎任何形式的贡献！如果你有任何建议或问题，请随时提出 Issue。
