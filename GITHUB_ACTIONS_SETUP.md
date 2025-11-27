# GitHub Actions AUR自动更新配置指南

## 概述

本指南说明如何配置GitHub Actions来自动更新AUR包。由于权限限制，工作流文件需要手动在GitHub仓库中创建。

## 配置步骤

### 第一步：创建GitHub Actions工作流

在GitHub仓库中手动创建文件：`.github/workflows/aur-update.yml`

```yaml
name: Update AUR Packages

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  update-aur-bin:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Setup SSH
      uses: webfactory/ssh-agent@v0.9.0
      with:
        ssh-private-key: ${{ secrets.AUR_SSH_PRIVATE_KEY }}

    - name: Clone AUR binary repository
      run: |
        git clone ssh://aur@aur.archlinux.org/leetcode-fsrs-cli-bin.git aur-repo-bin

    - name: Update binary package files
      run: |
        # Copy updated files
        cp leetcode-fsrs-cli-bin/PKGBUILD aur-repo-bin/
        cp leetcode-fsrs-cli-bin/.SRCINFO aur-repo-bin/

        # Update version
        cd aur-repo-bin
        LATEST_TAG=$(git describe --tags --abbrev=0)
        VERSION=${LATEST_TAG#v}

        # Update PKGBUILD version
        sed -i "s/pkgver=.*/pkgver=$VERSION/" PKGBUILD

        # Update source URL with new version
        sed -i "s|source=.*|source=\"v$VERSION.tar.gz::https://github.com/SaintFore/LeetCodeCLI/archive/refs/tags/v$VERSION.tar.gz\"|" PKGBUILD

        # Update .SRCINFO
        makepkg --printsrcinfo > .SRCINFO

    - name: Commit and push binary package
      run: |
        cd aur-repo-bin
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add PKGBUILD .SRCINFO
        git commit -m "Update to version ${{ github.ref_name }}"
        git push origin master

  update-aur-main:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Setup SSH
      uses: webfactory/ssh-agent@v0.9.0
      with:
        ssh-private-key: ${{ secrets.AUR_SSH_PRIVATE_KEY }}

    - name: Clone AUR main repository
      run: |
        git clone ssh://aur@aur.archlinux.org/leetcode-fsrs-cli.git aur-repo-main

    - name: Update main package files
      run: |
        # Copy updated files
        cp PKGBUILD aur-repo-main/

        # Update version
        cd aur-repo-main
        LATEST_TAG=$(git describe --tags --abbrev=0)
        VERSION=${LATEST_TAG#v}

        # Update PKGBUILD version
        sed -i "s/pkgver=.*/pkgver=$VERSION/" PKGBUILD

        # Update source URL with new version
        sed -i "s|source=.*|source=\"https://github.com/SaintFore/LeetCodeCLI/archive/refs/tags/v$VERSION.tar.gz\"|" PKGBUILD

        # Update .SRCINFO
        makepkg --printsrcinfo > .SRCINFO

    - name: Commit and push main package
      run: |
        cd aur-repo-main
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add PKGBUILD .SRCINFO
        git commit -m "Update to version ${{ github.ref_name }}"
        git push origin master
```

### 第二步：配置GitHub Secrets

在GitHub仓库中设置以下Secret：

1. 进入仓库设置 → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加以下Secret：

**Secret名称**: `AUR_SSH_PRIVATE_KEY`
**Secret值**: 你的AUR SSH私钥

#### 获取AUR SSH私钥的步骤：

1. 如果你还没有AUR SSH密钥对：
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/aur
   ```

2. 将公钥添加到AUR账户：
   ```bash
   cat ~/.ssh/aur.pub
   ```
   复制输出内容，然后在AUR网站添加SSH密钥

3. 获取私钥内容：
   ```bash
   cat ~/.ssh/aur
   ```
   复制整个私钥内容作为Secret值

### 第三步：测试工作流

1. 手动触发工作流：
   - 进入仓库的Actions页面
   - 选择 "Update AUR Packages" 工作流
   - 点击 "Run workflow"

2. 或者通过创建新标签触发：
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

## 工作流说明

### 触发条件
- **自动触发**: 当推送新的版本标签时（如 `v1.1.0`）
- **手动触发**: 在GitHub Actions页面手动运行

### 执行的操作
1. 更新两个AUR包：
   - `leetcode-fsrs-cli` (源码版)
   - `leetcode-fsrs-cli-bin` (二进制版)

2. 自动更新：
   - 包版本号
   - 源代码下载URL
   - 依赖信息
   - .SRCINFO文件

## 故障排除

### 常见问题

1. **SSH连接失败**
   - 检查SSH私钥是否正确配置
   - 验证公钥是否已添加到AUR账户

2. **权限错误**
   - 确保AUR账户有权限推送对应包

3. **工作流不触发**
   - 检查标签格式是否正确（必须以 `v` 开头）
   - 确认工作流文件路径正确

### 手动更新AUR包（备用方案）

如果GitHub Actions无法使用，可以手动更新：

```bash
# 更新二进制版
cd leetcode-fsrs-cli-bin
git add PKGBUILD .SRCINFO
git commit -m "Update to version X.X.X"
git push origin master

# 更新源码版
# 需要手动编辑AUR仓库中的PKGBUILD和.SRCINFO
```

## 维护说明

- 每次发布新版本时，工作流会自动更新AUR包
- 确保本地 `PKGBUILD` 和 `leetcode-fsrs-cli-bin/PKGBUILD` 文件保持同步
- 定期检查工作流运行状态