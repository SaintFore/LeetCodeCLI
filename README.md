# LeetCode FSRS

一个以 Textual TUI 为主、Typer CLI 为辅的 LeetCode 间隔复习工具。调度由官方 `py-fsrs` 完成；多设备复制交给 Syncthing、WebDAV 客户端等成熟工具。

## 安装

需要 Python 3.11+。

### Arch Linux / paru

开发版本用于正式发版前验收：

```bash
paru -S leetcode-fsrs-git
```

如果 AUR 元数据尚未发布，可以直接从仓库构建并安装；`paru` 会同时解析 AUR 中的 `python-fsrs`：

```bash
git clone https://github.com/SaintFore/LeetCodeCLI.git
cd LeetCodeCLI
scripts/build_arch_package.sh -i
```

GitHub Actions 的 **Build Arch package** 工作流会在 `main` 的相关文件变化后构建并上传 `.pkg.tar.zst`。首次创建或更新 AUR 元数据时，手动运行该工作流并启用 `publish_aur`；仓库需要配置 `AUR_SSH_PRIVATE_KEY` secret。

### Python

```bash
python -m venv .venv
.venv/bin/pip install -e .
```

启动 TUI：

```bash
leetcode-fsrs
```

首次启动会询问：

- 一个外部同步工具管理的共享目录；
- 固定的 IANA 时区，例如 `Asia/Shanghai`；
- 可选的 LeetCode 用户名。

也可以无交互初始化：

```bash
leetcode-fsrs init ~/Sync/leetcode-fsrs --timezone Asia/Shanghai --username YOUR_NAME
```

## LeetCode 导入

Cookie 只保存在本机系统 keyring，不会进入共享目录：

```bash
leetcode-fsrs auth login
leetcode-fsrs import-accepted
```

无可用 keyring 时，不会把 Cookie 降级保存到明文文件。可在当前 shell 中使用：

```bash
export LEETCODE_SESSION='...'
leetcode-fsrs import-accepted
```

导入会缓存题目目录，并将新的 Accepted 题目登记为新卡片；它不会伪造一次 FSRS 评分。

## 日常流程

Today 队列默认最多 20 题，其中新题最多 5 题；到期复习先于新题。选择题目后：

1. 打开解题器；TUI 暂停并启动外部程序。
2. 退出解题器后，选择 Again、Hard、Good 或 Easy。
3. 不想评分时选择“跳过”。

默认解题器命令是 `nvim +Leet`，适配 `kawre/leetcode.nvim` 的 dashboard。也可使用占位符配置任意命令：

```bash
leetcode-fsrs config solver 'nvim +Leet'
leetcode-fsrs config solver 'my-solver {slug} {url}'
```

进程还会收到 `LEETCODE_FSRS_KEY`、`LEETCODE_FSRS_SLUG` 和 `LEETCODE_FSRS_URL` 环境变量。

## CLI

```bash
leetcode-fsrs today [--json]
leetcode-fsrs rate two-sum good
leetcode-fsrs card enroll two-sum
leetcode-fsrs card suspend two-sum
leetcode-fsrs card resume two-sum
leetcode-fsrs config set daily_limit 20
leetcode-fsrs status
```

## 多设备同步与两层存储

共享目录是事实来源，只包含清单和不可变事件：

```text
shared-directory/
├── library.json
└── events/
    ├── <device-a>/<UTC-day>.ndjson
    └── <device-b>/<UTC-day>.ndjson
```

每台设备另有本地 SQLite 投影，用于快速查询；它可以随时由事件重建，因此不要同步 SQLite。这里的“两层”不是保存两份都需要合并的数据，而是“可同步事实 + 可丢弃索引”。

文件数量按“活跃设备 × 活跃 UTC 天数”增长，不是每次复习一个文件。单设备每天最多一个事件文件；一年约 365 个小文件。损坏的完整行会被报告并跳过，写到一半的最后一行会等同步完成后再读取。

完整说明见 [同步与恢复](docs/sync.md) 和 [架构](docs/architecture.md)。

## 开发

```bash
.venv/bin/pip install -e '.[test]'
.venv/bin/pytest -q
```

旧版 JSON 不自动迁移；2.0 从新的事件库开始。
