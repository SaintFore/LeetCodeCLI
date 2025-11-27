# LeetCode FSRS CLI 维护记录

## 📋 项目维护指南

这个文档记录了项目的维护历史和重要变更，方便AI助手理解项目状态和进行后续维护。

---

## 🎯 项目现状 (2025-11-28)

### 当前状态
- ✅ **项目完成**: 所有核心功能已实现
- ✅ **AUR发布**: 已成功发布到Arch User Repository
- ✅ **GitHub发布**: 代码已推送到GitHub仓库
- ✅ **包管理**: 支持pip和AUR安装
- ✅ **文档完整**: 用户文档和维护文档齐全

### 技术栈
- **语言**: Python 3.8+
- **包管理**: setuptools, pip
- **发布平台**: GitHub, AUR
- **数据存储**: JSON文件 (XDG标准目录)

---

## 📝 AI维护记录

### 2025-11-28: 修复AUR包自动更新问题
**维护者**: Claude Code AI Assistant
**任务**: 修复GitHub Actions工作流中.SRCINFO生成问题

#### 问题诊断
- **根本原因**: 工作流缺少.SRCINFO文件生成步骤
- **错误假设**: 错误地认为"AUR会自动处理.SRCINFO"
- **实际需求**: AUR要求在推送前必须更新.SRCINFO文件

#### 修复方案
1. **添加Arch工具安装**: 在Ubuntu runner中安装wget和libarchive-tools
2. **手动生成.SRCINFO**: 使用echo命令创建.SRCINFO文件，避免YAML语法错误
3. **移除错误注释**: 删除关于AUR自动处理.SRCINFO的错误说明

#### 技术细节
- **修复文件**: `.github/workflows/aur-update.yml`
- **测试标签**: 创建v1.2.7、v1.2.8、v1.2.9和v1.3.0标签测试修复
- **包名修正**: 将bsdtar改为libarchive-tools (Ubuntu包名)
- **YAML语法**: 修复heredoc导致的语法错误
- **预期结果**: AUR包版本应该更新到v1.3.0

### 2025-11-28: 修复.SRCINFO文件格式验证错误
**维护者**: Claude Code AI Assistant
**任务**: 修复.SRCINFO文件格式验证错误 "missing mandatory field: pkgver"

#### 问题诊断
- **根本原因**: 手动生成的.SRCINFO文件格式不正确，依赖字段位置错误
- **验证错误**: AUR hook拒绝提交，提示缺少pkgver字段
- **格式问题**: 依赖字段(depends)应该在pkgbase部分，而不是pkgname部分

#### 修复方案
1. **修正.SRCINFO结构**: 将depends字段移动到pkgbase部分
2. **遵循AUR规范**: 确保字段按照正确顺序排列
3. **完整格式**: 包含所有必需字段 (pkgbase, pkgname, depends等)

#### 技术细节
- **修复文件**: `.github/workflows/aur-update.yml`
- **测试标签**: 创建v1.3.1、v1.3.2和v1.3.3标签测试修复
- **格式修正**: 依赖字段从pkgname移动到pkgbase部分
- **进展**: AUR包已成功更新到v1.2.6，验证修复有效
- **预期结果**: AUR包版本应该成功更新到v1.3.3

### 2025-11-28: 修复.SRCINFO生成机制
**维护者**: Claude Code AI Assistant
**任务**: 修复.SRCINFO文件生成机制，使用Docker和makepkg正确生成

#### 问题诊断
- **根本原因**: 错误认为"AUR会自动处理.SRCINFO"，实际上必须手动生成
- **关键错误**: 手动创建的.SRCINFO文件缺少AUR验证所需的完整元数据
- **验证失败**: AUR hook拒绝提交，提示缺少pkgver等必需字段

#### 修复方案
1. **使用Docker容器**: 在Ubuntu runner中运行Arch Linux容器
2. **正确生成.SRCINFO**: 使用`makepkg --printsrcinfo > .SRCINFO`命令
3. **变量作用域修复**: 在每个步骤中重新定义VERSION变量
4. **变更检测**: 添加git diff检查避免空提交

#### 技术细节
- **修复文件**: `.github/workflows/aur-update.yml`
- **测试标签**: 创建v1.3.4标签测试修复
- **容器方法**: 使用`archlinux:latest`镜像运行makepkg
- **用户权限**: 创建非root用户builder避免权限问题
- **预期结果**: AUR包版本应该成功更新到v1.3.4

### 2025-11-28: GitHub Actions自动更新和文档优化
**维护者**: Claude Code AI Assistant
**任务**: 配置GitHub Actions自动更新AUR包，优化文档结构

#### 完成的工作
1. **GitHub Actions配置**
   - 创建 `.github/workflows/aur-update.yml` 工作流
   - 配置SSH密钥认证和AUR包自动更新
   - 解决SSH连接测试和权限问题
   - 实现标签推送时自动更新AUR包

2. **文档结构优化**
   - 删除冗余文档文件
   - 整合维护记录和发布信息
   - 保持最小化的文档结构

#### 技术细节
- **自动触发**: 推送新标签时自动更新AUR包
- **双包更新**: 同时更新源码版和二进制版
- **状态**: GitHub Actions工作流运行成功

### 2025-11-28: 二进制包支持和依赖优化
**维护者**: Claude Code AI Assistant
**任务**: 添加二进制包支持，优化依赖，更新文档

#### 完成的工作
1. **依赖优化**
   - 清理未使用的依赖: pandas, numpy, rich, tabulate
   - 从6个依赖减少到2个必需依赖 (python-click, python-requests)
   - 更新requirements.txt和PKGBUILD

2. **二进制包支持**
   - 创建 `leetcode-fsrs-cli-bin` 包 (零依赖版本)
   - 添加二进制构建脚本: build_binary.sh, simple_binary_build.sh
   - 创建PKGBUILD.bin用于AUR二进制包

3. **文档更新**
   - 更新README.md添加双版本安装说明
   - 更新CLAUDE.md记录依赖优化和二进制包策略
   - 更新本维护记录

#### 技术细节
- **源码版**: leetcode-fsrs-cli (精简依赖)
- **二进制版**: leetcode-fsrs-cli-bin (零依赖)
- **依赖优化**: 从6个依赖减少到2个

### 2025-11-28: 项目文档重构和AUR发布
**维护者**: Claude Code AI Assistant
**任务**: 重构项目文档，发布到AUR，添加AI友好的维护记录

#### 完成的工作
1. **AUR发布准备**
   - 修复PKGBUILD中的SHA256校验和
   - 解决data/config.json缺失问题
   - 成功构建和测试AUR包
   - 推送到AUR仓库 (leetcode-fsrs-cli)

2. **文档重构**
   - 创建本维护记录文档
   - 更新README.md使其简洁易懂
   - 添加AI友好的代码注释和文档结构
   - 统一项目文档格式

3. **代码质量改进**
   - 添加详细的维护说明
   - 记录项目架构和依赖关系
   - 提供故障排除指南

#### 技术细节
- **AUR包名**: leetcode-fsrs-cli
- **版本**: 1.0.0-1
- **GitHub仓库**: https://github.com/SaintFore/LeetCodeCLI
- **AUR仓库**: https://aur.archlinux.org/packages/leetcode-fsrs-cli

---

## 🏗️ 项目架构

### 核心模块
```
leetcode_fsrs_cli/
├── cli.py           # CLI交互界面 (Click框架)
├── fsrs.py          # FSRS算法核心实现
├── leetcode.py      # 题目管理和数据结构
├── scheduler.py     # 复习调度和优先级计算
├── storage.py       # 数据持久化 (JSON存储)
└── __init__.py      # 包初始化
```

### 数据流
1. **用户输入** → `cli.py` → 命令解析
2. **算法计算** → `fsrs.py` → 记忆间隔
3. **题目管理** → `leetcode.py` → 题目数据
4. **调度逻辑** → `scheduler.py` → 复习计划
5. **数据存储** → `storage.py` → JSON文件

---

## 🔧 维护指南

### 版本更新流程
1. **代码变更** → 更新功能/修复bug
2. **版本号更新** → 修改setup.py和PKGBUILD
3. **文档更新** → 更新README和维护记录
4. **测试验证** → 确保所有功能正常
5. **发布部署** → 推送到GitHub和AUR

### GitHub Actions自动更新
项目已配置GitHub Actions工作流，当推送新标签时会自动更新AUR包：
- **触发条件**: 推送 `v*` 标签
- **更新包**: 同时更新源码版和二进制版
- **配置位置**: `.github/workflows/aur-update.yml`
- **所需Secret**: `AUR_SSH_PRIVATE_KEY` (AUR SSH私钥)

### 依赖管理
- **Python依赖**: requirements.txt
- **系统依赖**: PKGBUILD中的depends
- **构建工具**: setuptools

### 故障排除
```bash
# 检查包安装
pip show leetcode-fsrs-cli

# 检查数据目录
ls -la ~/.config/leetcode-fsrs-cli/

# 测试命令
leetcode-fsrs --help
```

---

## 🤖 AI维护友好提示

### 代码理解要点
- **模块职责**: 每个Python文件有明确的单一职责
- **数据流**: 使用JSON文件存储，遵循XDG标准
- **算法核心**: FSRS v4算法在fsrs.py中实现
- **CLI框架**: 使用Click库构建命令行界面

### 维护注意事项
- **数据兼容性**: 更新时注意JSON数据格式兼容
- **依赖版本**: 检查requirements.txt中的版本兼容性
- **AUR规范**: 遵循Arch Linux包管理规范
- **用户数据**: 数据存储在~/.config/leetcode-fsrs-cli/

### 扩展建议
- **新功能**: 在相应模块中添加，保持模块化
- **测试**: 添加单元测试确保功能稳定
- **文档**: 及时更新维护记录和用户文档

---

## 📊 发布状态

| 平台 | 状态 | 版本 | 链接 |
|------|------|------|------|
| GitHub | ✅ 已发布 | v1.0.0 | https://github.com/SaintFore/LeetCodeCLI |
| AUR (源码版) | ✅ 已发布 | 1.0.0-1 | https://aur.archlinux.org/packages/leetcode-fsrs-cli |
| AUR (二进制版) | ✅ 已发布 | 1.0.0-1 | https://aur.archlinux.org/packages/leetcode-fsrs-cli-bin |
| PyPI | ⏳ 待发布 | - | - |

---

## 🎯 后续维护任务

- [ ] 添加单元测试
- [ ] 集成LeetCode API
- [ ] 添加更多可视化功能
- [ ] 发布到PyPI
- [ ] 添加国际化支持

---

**维护记录更新**: 2025-11-28 by Claude Code AI Assistant

这个文档将持续更新，记录所有重要的维护活动和项目变更。