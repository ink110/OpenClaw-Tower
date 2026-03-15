# OpenClaw Tower

可视化工业级 AI 监控看板

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/flask-2.0+-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/tailwindcss-2.0+-cyan.svg" alt="Tailwind">
</p>

---

## AI 协作与自动化开发准则 (AI-Driven Development SOP)

> 本准则适用于所有 AI 参与的代码修改和功能开发场景，确保开发过程可追溯、可测试、可回滚。

### 1. 环境自检 (Self-Diagnostic)

**原则**：在修改任何代码前，Claude 必须先通过命令行工具（如 `ls`, `cat`, `grep`）扫描相关路径，确保对当前项目结构和逻辑有物理层面的认知。

**操作规范**：
- 读取或修改文件前，先用 `ls` 确认文件存在
- 用 `grep` 或 `cat` 查看关键代码片段
- 确认涉及的配置文件、日志路径、依赖版本等信息

**示例**：
```bash
# 修改 backend/app.py 前，先确认项目结构
ls -la
ls -la backend/
grep -n "parse_status" backend/app.py
```

---

### 2. 测试驱动 (Test-First)

**原则**：所有关于后端逻辑（如 `app.py` 的状态判断）的修改，必须先编写或更新自动化测试脚本，然后再修改代码。

**操作规范**：
- 创建 `test_*.py` 测试脚本
- 修改代码后，运行测试并确认 `Success`
- 测试必须覆盖：正常流程、边界条件、异常处理

**示例**：
```bash
# 运行测试
python3 test_emotion.py

# 预期输出
=== 测试总结 ===
  [thought] 模式: ✓ 通过
  5秒衰减: ✓ 通过
  噪音过滤: ✓ 通过
所有测试通过!
```

---

### 3. 实时性红线

**原则**：严禁在代码中使用硬编码的日期或绝对路径。所有时间判断必须基于系统实时时钟，所有路径必须基于项目根目录。

**禁止做法**：
```python
# ❌ 禁止：硬编码日期
if "2026-03-15" in line:
    ...

# ❌ 禁止：硬编码绝对路径
log_file = "/tmp/openclaw/openclaw-2026-03-14.log"
```

**正确做法**：
```python
# ✅ 正确：动态获取当前时间
from datetime import datetime
now = datetime.now()

# ✅ 正确：基于项目根目录的相对路径
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
```

---

### 4. Git 存档规范

**原则**：每次完成功能并测试通过后，Claude 应主动运行 `git status` 并建议用户进行 commit。

**操作规范**：
1. 运行 `git status` 查看改动文件
2. 运行 `git diff` 预览改动内容
3. 编写 commit message，包含：
   - **改动点**：本次修改的核心内容
   - **测试结果**：自动化测试的通过情况

**示例**：
```bash
git status
git diff

git commit -m "$(cat <<'EOF'
feat: 优化情绪检测逻辑

改动点：
- 新增 [thought] 模式检测
- 添加 5 秒情绪衰减机制
- 增强噪音过滤规则

测试结果：
- [thought] 模式: ✓ 通过
- 5秒衰减: ✓ 通过
- 噪音过滤: ✓ 通过
EOF
)"
```

---

### 5. 持续集成检查清单

在提交代码前，Claude 必须确认：

- [ ] 代码语法检查通过 (`python3 -m py_compile`)
- [ ] 自动化测试全部通过
- [ ] 无硬编码日期或绝对路径
- [ ] 新增功能已更新文档（如 README.md）

---

## 定位

专为设计师和开发者打造的可视化监控面板，解决 OpenClaw 运行黑盒、手动启停繁琐的痛点。

## 核心功能

| 功能 | 描述 |
|------|------|
| 一键启停 | 点击按钮即可启动/停止/重启 OpenClaw 网关 |
| 状态实时监控 | 实时显示运行状态、进程 PID，带呼吸灯效果 |
| 异常自愈重启 | 自动检测日志中的 Error，显示报警横幅并提供紧急重启按钮 |
| 日志流可视化 | 实时读取并展示网关日志，支持滚动查看 |

## 快速开始

### 环境要求

- Python 3.8+
- macOS / Linux

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/OpenClaw-Tower.git
cd OpenClaw-Tower

# 2. 运行安装脚本
chmod +x setup.sh
./setup.sh

# 3. 启动服务
# 终端 1 - 后端
cd backend && python3 app.py

# 终端 2 - 前端
cd src && python3 -m http.server 8080
```

然后在浏览器打开：http://localhost:8080

## 项目结构

```
OpenClaw-Tower/
├── backend/
│   ├── app.py          # Flask 后端 API
│   └── requirements.txt
├── src/
│   └── index.html      # 前端监控面板
├── setup.sh            # 安装脚本
└── README.md
```

## 技术栈

- **后端**: Flask + Flask-CORS
- **前端**: HTML5 + TailwindCSS
- **监控**: 进程检测 (pgrep/pkill) + 日志文件读取

## 致谢

本项目由设计师主导定义，是一次 AI 协作开发的实践成果。感谢所有参与设计和开发的伙伴。

---

<p align="center">Built with ❤️ by Designer-Driven AI Collaboration</p>
