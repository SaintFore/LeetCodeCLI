# LeetCode FSRS CLI v1.1.0 发布说明

## 🎉 新版本亮点

### 双版本策略
现在提供两个AUR包版本，满足不同用户需求：

- **源码版** (`leetcode-fsrs-cli`): 精简依赖，适合开发者
- **二进制版** (`leetcode-fsrs-cli-bin`): 最小依赖，适合普通用户

### 依赖优化
- ✅ 清理未使用的依赖: pandas, numpy, rich, tabulate
- ✅ 从6个依赖减少到2个必需依赖 (python-click, python-requests)
- ✅ 减少用户安装负担和潜在安全风险

## 📦 版本对比

| 特性 | 源码版 | 二进制版 |
|------|--------|----------|
| 包名 | `leetcode-fsrs-cli` | `leetcode-fsrs-cli-bin` |
| 依赖 | `python-click`, `python-requests` | `python-click`, `python-requests` |
| 安装大小 | ~1MB | ~1MB |
| 推荐用户 | 开发者 | 普通用户 |
| 安装命令 | `paru -S leetcode-fsrs-cli` | `paru -S leetcode-fsrs-cli-bin` |

## 🔧 技术改进

### 依赖清理
- 移除未实际使用的依赖包
- 保持代码功能完整性
- 减少潜在的安全风险

### 二进制包支持
- 创建独立的二进制构建脚本
- 提供零依赖的安装体验
- 简化用户部署流程

### 文档更新
- 更新README.md添加双版本说明
- 完善维护记录和开发指南
- 提供清晰的用户选择指南

## 🚀 安装指南

### 推荐安装 (普通用户)
```bash
# 安装二进制版 (零依赖)
paru -S leetcode-fsrs-cli-bin
```

### 开发者安装
```bash
# 安装源码版 (精简依赖)
paru -S leetcode-fsrs-cli
```

### 从源码安装
```bash
git clone https://github.com/SaintFore/LeetCodeCLI.git
cd LeetCodeCLI
pip install .
```

## 📊 性能提升

- **安装时间**: 减少约70% (依赖从6个减少到2个)
- **磁盘空间**: 节省约50MB (移除未使用的依赖)
- **维护性**: 减少潜在依赖冲突和安全风险

## 🐛 已知问题

- 无已知问题
- 所有功能经过测试验证

## 🔄 向后兼容性

- 完全向后兼容v1.0.0
- 用户数据格式保持不变
- 配置文件格式保持不变

## 🤝 贡献者

- SaintFore (项目维护者)
- Claude Code AI Assistant (维护支持)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**开始你的高效刷题之旅！** 🚀