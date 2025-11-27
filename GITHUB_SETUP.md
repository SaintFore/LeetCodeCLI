# GitHub 和 AUR 发布指南

## 🚀 发布到 GitHub

### 1. 创建 GitHub 仓库

1. 在 GitHub 上创建新仓库：`leetcode-fsrs-cli`
2. 设置仓库为 public
3. 添加合适的描述和标签

### 2. 初始化本地 Git 仓库

```bash
# 在项目目录中
git init
git add .
git commit -m "Initial commit: LeetCode FSRS CLI v1.0.0"

# 添加远程仓库
git remote add origin https://github.com/your-username/leetcode-fsrs-cli.git

# 推送代码
git push -u origin main
```

### 3. 创建发布版本

在 GitHub 上：
1. 点击 "Releases"
2. "Draft a new release"
3. 标签：`v1.0.0`
4. 标题：`LeetCode FSRS CLI v1.0.0`
5. 描述：包含功能列表和更新说明
6. 附件：上传源代码压缩包

## 📦 发布到 AUR

### 1. 准备 AUR 包

确保以下文件存在：
- `PKGBUILD`
- `.SRCINFO` (需要生成)
- 源代码压缩包

### 2. 生成 .SRCINFO

```bash
# 安装 aurutils 或类似工具
paru -S aurutils

# 在项目目录中生成 .SRCINFO
makepkg --printsrcinfo > .SRCINFO
```

### 3. 创建 AUR 仓库

```bash
# 克隆 AUR 仓库 (需要 AUR 账户)
git clone ssh://aur@aur.archlinux.org/leetcode-fsrs-cli.git

# 复制文件到 AUR 仓库
cp PKGBUILD .SRCINFO leetcode-fsrs-cli/

# 提交到 AUR
cd leetcode-fsrs-cli
git add .
git commit -m "Initial package release"
git push
```

### 4. 更新 AUR 包

当有新版本时：
1. 更新 `PKGBUILD` 中的版本号
2. 重新生成 `.SRCINFO`
3. 提交到 AUR 仓库

## 🔧 用户安装指南

### 从 AUR 安装

```bash
# 使用 paru (推荐)
paru -S leetcode-fsrs-cli

# 或使用 yay
yay -S leetcode-fsrs-cli
```

### 从 GitHub 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/leetcode-fsrs-cli.git
cd leetcode-fsrs-cli

# 安装依赖
pip install -r requirements.txt

# 安装包
python setup.py install
```

## 📝 维护指南

### 版本管理
- 使用语义化版本号 (SemVer)
- 每次发布更新 `PKGBUILD` 和 `setup.py` 中的版本号

### 依赖更新
- 定期检查并更新 `requirements.txt`
- 测试新版本兼容性

### 用户支持
- 维护 GitHub Issues
- 更新文档
- 处理用户反馈

## 🎯 发布检查清单

- [ ] 代码测试通过
- [ ] 文档更新
- [ ] 版本号更新
- [ ] PKGBUILD 更新
- [ ] .SRCINFO 生成
- [ ] GitHub 发布创建
- [ ] AUR 包更新
- [ ] 安装测试通过

## 🔗 有用的链接

- [AUR 提交指南](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- [PKGBUILD 参考](https://wiki.archlinux.org/title/PKGBUILD)
- [Python 包分发指南](https://packaging.python.org/)