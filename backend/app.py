#!/usr/bin/env python3
"""
OpenClaw-Tower 后端服务
提供进程控制、状态监控、日志读取等 API
"""

import os
import json
import subprocess
import glob
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置路径
OPENCLAW_HOME = Path.home() / ".openclaw"
CONFIG_FILE = OPENCLAW_HOME / "openclaw.json"
LOGS_DIR = OPENCLAW_HOME / "logs"
PID_FILE = OPENCLAW_HOME / "gateway.pid"


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_gateway_process():
    """检查网关进程是否运行，返回进程信息"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "openclaw-gateway"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip().split()[0])
            return {"running": True, "pid": pid}
    except Exception:
        pass
    return {"running": False, "pid": None}


def start_gateway():
    """异步启动网关进程"""
    def run_gateway():
        try:
            # 从配置中获取启动命令
            config = load_config()
            gateway_cmd = config.get("gateway", {}).get("start_command", "openclaw gateway")

            # 启动进程
            process = subprocess.Popen(
                gateway_cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(OPENCLAW_HOME)
            )

            # 保存 PID
            with open(PID_FILE, "w") as f:
                f.write(str(process.pid))

        except Exception as e:
            print(f"启动网关失败: {e}")

    # 在后台线程中启动
    thread = threading.Thread(target=run_gateway, daemon=True)
    thread.start()
    return True


def stop_gateway():
    """停止网关进程"""
    try:
        # 使用 pkill 停止进程
        subprocess.run(["pkill", "-f", "openclaw-gateway"], check=False)

        # 删除 PID 文件
        if PID_FILE.exists():
            PID_FILE.unlink()

        return True
    except Exception:
        return False


def restart_gateway():
    """重启网关进程"""
    stop_gateway()
    import time
    time.sleep(2)  # 等待2秒确保进程完全停止
    start_gateway()
    return True


def get_latest_log():
    """获取最新的日志文件"""
    if not LOGS_DIR.exists():
        return None

    log_files = list(LOGS_DIR.glob("gateway*.log"))
    if not log_files:
        return None

    # 返回最新的日志文件
    return max(log_files, key=os.path.getmtime)


def read_logs(lines=50):
    """读取日志文件最后 N 行"""
    log_file = get_latest_log()
    if not log_file:
        return {"logs": [], "file": None, "has_error": False}

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        # 检查是否有 Error
        has_error = any("Error" in line or "ERROR" in line for line in last_lines)

        return {
            "logs": [line.strip() for line in last_lines],
            "file": str(log_file),
            "has_error": has_error
        }
    except Exception as e:
        return {"logs": [], "file": str(log_file), "has_error": False, "error": str(e)}


# ==================== API 路由 ====================

@app.route("/api/start", methods=["POST"])
def api_start():
    """启动网关"""
    start_gateway()
    return jsonify({
        "success": True,
        "message": "网关启动命令已发送"
    })


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """停止网关"""
    success = stop_gateway()
    return jsonify({
        "success": success,
        "message": "网关已停止" if success else "停止失败"
    })


@app.route("/api/restart", methods=["POST"])
def api_restart():
    """重启网关"""
    restart_gateway()
    return jsonify({
        "success": True,
        "message": "网关重启中..."
    })


@app.route("/api/status", methods=["GET"])
def api_status():
    """获取网关运行状态"""
    process_info = get_gateway_process()
    return jsonify({
        "running": process_info["running"],
        "pid": process_info["pid"],
        "status": "online" if process_info["running"] else "offline"
    })


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """获取日志"""
    lines = request.args.get("lines", 50, type=int)
    log_data = read_logs(lines)
    return jsonify(log_data)


@app.route("/api/health", methods=["GET"])
def api_health():
    """健康检查"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 50)
    print("OpenClaw-Tower 后端服务启动中...")
    print(f"配置文件: {CONFIG_FILE}")
    print(f"日志目录: {LOGS_DIR}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
