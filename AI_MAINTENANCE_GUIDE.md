# AI 维护指南

## 🎯 项目概述

**LeetCode FSRS CLI** 是一个基于FSRS（Free Spaced Repetition Scheduler）记忆算法的LeetCode刷题CLI工具。

### 核心功能
- FSRS v4算法实现
- LeetCode题目管理
- 智能复习调度
- 命令行交互界面
- JSON数据持久化

## 🏗️ 架构理解

### 模块结构
```
leetcode_fsrs_cli/
├── cli.py           # CLI交互界面 (Click框架)
├── fsrs.py          # FSRS算法核心
├── leetcode.py      # 题目数据模型
├── scheduler.py     # 复习调度逻辑
└── storage.py       # 数据存储管理
```

### 数据流
1. **用户输入** → `cli.py` → 命令解析
2. **算法计算** → `fsrs.py` → 记忆间隔
3. **题目管理** → `leetcode.py` → 题目数据
4. **调度逻辑** → `scheduler.py` → 复习计划
5. **数据存储** → `storage.py` → JSON文件

## 🔧 维护任务

### 常规维护
- [ ] 检查依赖更新
- [ ] 测试功能完整性
- [ ] 更新文档
- [ ] 验证AUR包构建

### 版本更新流程
1. **代码变更** → 功能更新/修复
2. **版本号更新** → setup.py + PKGBUILD
3. **文档更新** → README + 维护记录
4. **测试验证** → 功能测试
5. **发布部署** → GitHub + AUR

### 依赖管理
- **Python依赖**: `requirements.txt`
- **系统依赖**: `PKGBUILD`中的depends
- **构建工具**: setuptools

## 🐛 故障排除

### 常见问题

#### 包安装问题
```bash
# 检查包安装
pip show leetcode-fsrs-cli

# 检查命令路径
which leetcode-fsrs

# 检查Python环境
python --version
```

#### 数据目录问题
```bash
# 检查数据目录
ls -la ~/.config/leetcode-fsrs-cli/

# 检查权限
chmod 755 ~/.config/leetcode-fsrs-cli/
```

#### AUR构建问题
```bash
# 测试构建
makepkg --nodeps

# 检查PKGBUILD语法
namcap PKGBUILD

# 验证SHA256
sha256sum v1.0.0.tar.gz
```

## 📝 代码维护要点

### 模块职责
- **cli.py**: 用户交互和命令解析
- **fsrs.py**: FSRS算法实现 (不要修改核心算法)
- **leetcode.py**: 题目数据模型和管理
- **scheduler.py**: 复习调度逻辑
- **storage.py**: JSON数据持久化

### 数据兼容性
- 更新时保持JSON数据格式兼容
- 使用版本迁移处理数据格式变更
- 备份用户数据

### 测试要求
- 验证所有CLI命令
- 测试数据持久化
- 验证AUR包构建
- 检查依赖兼容性

## 🚀 扩展开发

### 建议的新功能
- LeetCode API集成
- 移动端适配
- 云端同步
- 更多可视化
- 国际化支持

### 开发指南
1. **功能设计** → 明确需求和接口
2. **模块选择** → 选择合适模块添加功能
3. **数据设计** → 考虑数据存储格式
4. **测试验证** → 添加测试用例
5. **文档更新** → 更新用户和维护文档

## 📊 项目状态

### 当前状态
- ✅ 核心功能完成
- ✅ AUR发布成功
- ✅ GitHub仓库建立
- ✅ 文档完整
- ✅ 测试通过

### 发布信息
- **AUR包名**: `leetcode-fsrs-cli`
- **版本**: 1.0.0-1
- **GitHub**: https://github.com/SaintFore/LeetCodeCLI
- **AUR**: https://aur.archlinux.org/packages/leetcode-fsrs-cli

## 🔗 相关文档

- [MAINTENANCE_LOG.md](MAINTENANCE_LOG.md) - 详细维护记录
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [RELEASE_GUIDE.md](RELEASE_GUIDE.md) - 发布指南
- [README.md](README.md) - 用户文档

---

**最后更新**: 2025-11-28
**维护者**: Claude Code AI Assistant

这个指南将持续更新，为AI助手提供项目维护所需的关键信息。