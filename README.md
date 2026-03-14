# OpenClaw Tower

可视化工业级 AI 监控看板

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/flask-2.0+-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/tailwindcss-2.0+-cyan.svg" alt="Tailwind">
</p>

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
