#!/usr/bin/env python3
"""
OpenClaw-Tower 后端服务 - 交互核心逻辑重构 v2
容错优化：
- 错误白名单：忽略 streaming start failed、HTTP 400 等非致命错误
- 结果优先：dispatch complete 出现后强制覆盖 error 状态
- 精准报错：只有致命错误才触发 error
"""

import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

# ==================== 全局状态 ====================
class InteractionState:
    def __init__(self):
        self.last_user_msg = ""
        self.last_ai_reply = ""
        self.error_detail = ""
        self.busy_start_time = None

    def reset(self):
        self.last_user_msg = ""
        self.last_ai_reply = ""
        self.error_detail = ""
        self.busy_start_time = None

state = InteractionState()

# 配置路径
OPENCLAW_HOME = Path.home() / ".openclaw"
CONFIG_FILE = OPENCLAW_HOME / "openclaw.json"
LOGS_DIR = OPENCLAW_HOME / "logs"
TEMP_LOGS_DIR = Path("/tmp/openclaw")
PID_FILE = OPENCLAW_HOME / "gateway.pid"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_gateway_process():
    try:
        result = subprocess.run(["pgrep", "-f", "openclaw-gateway"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return {"running": True, "pid": int(result.stdout.strip().split()[0])}
    except:
        pass
    return {"running": False, "pid": None}


def start_gateway():
    def run_gateway():
        try:
            config = load_config()
            gateway_cmd = config.get("gateway", {}).get("start_command", "openclaw gateway")
            process = subprocess.Popen(gateway_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(OPENCLAW_HOME))
            with open(PID_FILE, "w") as f:
                f.write(str(process.pid))
        except Exception as e:
            print(f"启动网关失败: {e}")
    threading.Thread(target=run_gateway, daemon=True).start()
    return True


def stop_gateway():
    try:
        subprocess.run(["pkill", "-f", "openclaw-gateway"], check=False)
        if PID_FILE.exists():
            PID_FILE.unlink()
        return True
    except:
        return False


def restart_gateway():
    stop_gateway()
    import time
    time.sleep(2)
    start_gateway()
    return True


def get_latest_log():
    """获取最新的日志文件"""
    all_files = []
    if TEMP_LOGS_DIR.exists():
        all_files.extend([f for f in TEMP_LOGS_DIR.glob("*.log") if f.is_file()])
    if LOGS_DIR.exists():
        all_files.extend([f for f in LOGS_DIR.glob("gateway*.log") if f.is_file() and ".err" not in f.name])
    if all_files:
        all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return all_files[0]
    return None


def extract_log_info(line):
    """从日志行提取时间和消息"""
    try:
        line = line.strip()
        if not line:
            return {"time": "", "message": ""}

        timestamp = ""
        msg = ""

        # JSON 格式
        if line.startswith('{'):
            try:
                data = json.loads(line)
                timestamp = data.get('time', '')
                msg = data.get('1') or data.get('message') or data.get('msg', '')
            except:
                pass
        else:
            # 文本格式
            time_match = re.match(r'(\d{4}-\d{2}-\d{2}T[\d:+\.]+)', line)
            if not time_match:
                time_match = re.match(r'(\d{4}-\d{2}-\d{2} [\d:]+)', line)
            if time_match:
                timestamp = time_match.group(1)
                rest = line[len(timestamp):].strip()
                m = re.search(r'\[([^\]]+)\]', rest)
                if m:
                    idx = rest.find(']')
                    if idx != -1:
                        msg = rest[idx+1:].strip()

        return {
            "time": timestamp.replace("+08:00", "").replace("T", " ") if timestamp else "",
            "message": msg[:200] if msg else ""
        }
    except:
        return {"time": "", "message": line[:200]}


# ==================== 容错核心逻辑 ====================

# 非致命错误白名单（不触发 error 状态）
ERROR_WHITELIST = [
    "streaming start failed",
    "stream response failed",
    "http 400",
    "http 401",
    "http 403",
    "http 404",
    "rate limit",
    "retrying",
    "reconnect"
]

# 致命错误关键词（触发 error 状态）
FATAL_ERROR_KEYWORDS = [
    "auth token expired",
    "authentication failed",
    "connection refused",
    "connection reset",
    "ECONNREFUSED",
    "ETIMEDOUT",
    "unauthorized",
    "invalid credentials",
    "token expired",
    "session expired",
    "service unavailable",
    "timeout",
    "error:"
]


def is_fatal_error(msg_lower):
    """判断是否为致命错误"""
    # 检查白名单
    for whitelisted in ERROR_WHITELIST:
        if whitelisted in msg_lower:
            return False
    # 检查致命错误
    for fatal in FATAL_ERROR_KEYWORDS:
        if fatal in msg_lower:
            return True
    # 纯 ERROR: 开头的致命错误
    if msg_lower.startswith("error: timeout"):
        return True
    return False


def extract_error_detail(log_lines):
    """提取错误详情（精简到15字以内）"""
    for line in log_lines:
        info = extract_log_info(line)
        msg = info.get("message", "")
        msg_lower = msg.lower()

        if is_fatal_error(msg_lower):
            # 精简到15字以内
            return msg[:15]
    return ""


def parse_interaction_status(log_lines):
    """
    容错交互状态机
    核心：先检查成功信号，再检查致命错误
    """
    global state
    now = datetime.now()

    # 解析最后30行
    entries = []
    for line in log_lines[-30:]:
        info = extract_log_info(line)
        msg = info.get("message", "")
        ts_str = info.get("time", "")

        if not msg:
            continue

        entry_time = None
        if ts_str:
            try:
                entry_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass

        entries.append({
            "message": msg,
            "message_lower": msg.lower(),
            "time": entry_time,
            "timestamp": ts_str
        })

    # 无日志
    if not entries:
        if state.busy_start_time:
            elapsed = (now - state.busy_start_time).total_seconds()
            if elapsed > 45:
                return "error", "error", "任务处理超时", state.error_detail or "45秒无响应"
        return "idle", "idle", "等待任务...", state.error_detail

    # 按时间倒序（最新在前）
    entries.sort(key=lambda x: x["time"] if x["time"] else datetime.min, reverse=True)

    # ==================== 核心逻辑 ====================
    # 步骤1：先检查是否有成功信号（dispatch complete / sent / response）
    for e in entries:
        msg_lower = e["message_lower"]
        if "dispatch complete" in msg_lower or "sent" in msg_lower or "response" in msg_lower:
            state.last_ai_reply = "任务已完成"
            state.busy_start_time = None
            state.error_detail = ""
            return "idle", "idle", "等待任务...", ""

    # 步骤2：检查致命错误（优先级高于用户消息）
    for e in entries:
        msg = e["message"]
        msg_lower = e["message_lower"]

        # 跳过白名单中的非致命错误
        if not is_fatal_error(msg_lower):
            continue

        # 找到了致命错误
        state.error_detail = extract_error_detail(log_lines)
        if not state.error_detail:
            state.error_detail = msg[:15]
        state.busy_start_time = None
        return "error", "error", f"错误: {msg[:15]}", state.error_detail

    # 步骤3：检查用户消息
    for e in entries:
        msg = e["message"]
        msg_lower = e["message_lower"]
        if "received" in msg_lower and ("message" in msg_lower or "msg" in msg_lower):
            match = re.search(r': (.+)$', msg)
            user_msg = match.group(1).strip()[:100] if match else msg[:100]
            state.last_user_msg = user_msg
            if not state.busy_start_time:
                state.busy_start_time = now
            state.error_detail = ""
            return "busy", "busy", f"用户: {user_msg[:40]}", ""

    # 步骤4：检查超时
    if state.busy_start_time:
        elapsed = (now - state.busy_start_time).total_seconds()
        if elapsed > 45:
            return "error", "error", "任务处理超时", state.error_detail or "45秒无响应"
        return "busy", "busy", "处理中...", ""

    return "idle", "idle", "等待任务...", ""


def format_interaction_logs(log_lines):
    """精简日志：用户指令 | AI回复 | 异常详情"""
    result = []

    for line in log_lines[-30:]:
        info = extract_log_info(line)
        msg = info.get("message", "")
        ts = info.get("time", "")
        msg_lower = msg.lower()

        if not msg or not ts:
            continue

        # 只显示致命错误
        if is_fatal_error(msg_lower):
            result.append({"time": ts, "type": "异常详情", "message": msg[:80]})
        elif "received" in msg_lower and ("message" in msg_lower or "msg" in msg_lower):
            match = re.search(r': (.+)$', msg)
            user_msg = match.group(1).strip()[:80] if match else msg[:80]
            result.append({"time": ts, "type": "用户指令", "message": user_msg})
        elif "dispatch complete" in msg_lower or "sent" in msg_lower or "response" in msg_lower:
            result.append({"time": ts, "type": "AI回复", "message": "任务已完成"})

    result.sort(key=lambda x: x.get("time", ""), reverse=True)
    return result[:20]


def read_logs():
    """读取日志"""
    log_file = get_latest_log()
    if not log_file:
        return {
            "logs": [], "file": None,
            "status": "idle", "emotion": "idle",
            "current_step": "等待任务...", "error_detail": ""
        }

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 10240))
            all_lines = f.read().splitlines()[-100:]
    except Exception as e:
        return {
            "logs": [], "file": str(log_file), "error": str(e),
            "status": "idle", "emotion": "idle",
            "current_step": "等待任务...", "error_detail": ""
        }

    if not all_lines:
        return {
            "logs": [], "file": str(log_file),
            "status": "idle", "emotion": "idle",
            "current_step": "等待任务...", "error_detail": ""
        }

    status, emotion, current_step, error_detail = parse_interaction_status(all_lines)
    logs = format_interaction_logs(all_lines)

    return {
        "logs": logs,
        "file": str(log_file),
        "status": status,
        "emotion": emotion,
        "current_step": current_step,
        "error_detail": error_detail
    }


# ==================== API ====================

@app.route("/api/start", methods=["POST"])
def api_start():
    start_gateway()
    return jsonify({"success": True, "message": "网关启动命令已发送"})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    success = stop_gateway()
    state.reset()
    return jsonify({"success": success, "message": "网关已停止" if success else "停止失败"})


@app.route("/api/restart", methods=["POST"])
def api_restart():
    state.reset()
    restart_gateway()
    return jsonify({"success": True, "message": "网关重启中..."})


@app.route("/api/status", methods=["GET"])
def api_status():
    process_info = get_gateway_process()
    log_data = read_logs()

    return jsonify({
        "running": process_info["running"],
        "pid": process_info["pid"],
        "status": "online" if process_info["running"] else "offline",
        "emotion": log_data.get("emotion", "idle"),
        "current_step": log_data.get("current_step", "等待任务..."),
        "error_detail": log_data.get("error_detail", ""),
        "last_interaction": {
            "user_msg": state.last_user_msg,
            "ai_reply": state.last_ai_reply
        }
    })


@app.route("/api/logs", methods=["GET"])
def api_logs():
    return jsonify(read_logs())


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 50)
    print("OpenClaw-Tower 后端服务启动中...")
    print(f"配置文件: {CONFIG_FILE}")
    print(f"日志目录: {LOGS_DIR}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
