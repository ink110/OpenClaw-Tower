#!/usr/bin/env python3
"""
OpenClaw-Tower 集成测试 - 三段式交互验证
测试场景：
1. 发送用户指令 -> 等待 2 秒 -> 确认 busy + user_msg
2. 发送回复完成 -> 确认 idle + ai_reply
3. 发送错误 -> 确认 error + error_detail
"""
import sys
import os
import json
import time
import datetime
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app import get_latest_log, state

API_URL = "http://localhost:5000/api/status"


def clear_logs():
    """清空测试日志"""
    log_file = get_latest_log()
    if log_file:
        with open(log_file, 'w') as f:
            f.write('')
        print(f"  日志已清空: {log_file}")


def write_log(message):
    """写入测试日志"""
    log_file = get_latest_log()
    if not log_file:
        print(f"错误：无法找到日志文件")
        return False

    now = datetime.datetime.now()
    log_line = f'{now.strftime("%Y-%m-%d %H:%M:%S")} [agent] {message}\n'

    with open(log_file, 'a') as f:
        f.write(log_line)
    return True


def call_api():
    """调用状态 API"""
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"API 调用失败: {e}")
        return None


def test_scenario_1():
    """场景1: 用户发送指令 -> busy + user_msg"""
    print("\n" + "="*60)
    print("场景 1: 用户发送指令 -> busy + user_msg")
    print("="*60)

    # 清空日志
    print("[步骤0] 清空日志...")
    clear_logs()

    # 重置状态
    state.reset()
    print("[步骤1] 状态已重置")

    # 写入用户消息
    print("[步骤2] 写入用户消息...")
    write_log("feishu[default]: received message from ou_123: 帮我搜索今天的科技新闻")

    # 等待 2 秒
    print("[步骤3] 等待 2 秒...")
    time.sleep(2)

    # 调用 API
    print("[步骤4] 调用 API...")
    data = call_api()
    if not data:
        return False

    emotion = data.get("emotion")
    current_step = data.get("current_step", "")
    last_interaction = data.get("last_interaction", {})
    user_msg = last_interaction.get("user_msg", "")

    print(f"  返回: emotion={emotion}")
    print(f"  current_step: {current_step}")
    print(f"  last_interaction: {json.dumps(last_interaction, ensure_ascii=False)}")

    # 校验
    if emotion == "busy" and user_msg:
        print("\n✓ 场景1 通过: busy + user_msg 正确")
        return True
    else:
        print(f"\n✗ 场景1 失败: emotion={emotion}, user_msg={user_msg}")
        return False


def test_scenario_2():
    """场景2: 回复完成 -> idle + ai_reply"""
    print("\n" + "="*60)
    print("场景 2: 回复完成 -> idle + ai_reply")
    print("="*60)

    # 清空日志
    print("[步骤0] 清空日志...")
    clear_logs()

    # 重置状态
    state.reset()

    # 写入回复完成
    print("[步骤1] 写入回复完成...")
    write_log("feishu[default]: dispatch complete - response sent")

    # 等待 2 秒
    print("[步骤2] 等待 2 秒...")
    time.sleep(2)

    # 调用 API
    print("[步骤3] 调用 API...")
    data = call_api()
    if not data:
        return False

    emotion = data.get("emotion")
    last_interaction = data.get("last_interaction", {})
    ai_reply = last_interaction.get("ai_reply", "")

    print(f"  返回: emotion={emotion}")
    print(f"  last_interaction: {json.dumps(last_interaction, ensure_ascii=False)}")

    # 校验
    if emotion == "idle" and ai_reply:
        print("\n✓ 场景2 通过: idle + ai_reply 正确")
        return True
    else:
        print(f"\n✗ 场景2 失败: emotion={emotion}, ai_reply={ai_reply}")
        return False


def test_scenario_3():
    """场景3: 错误检测 -> error + error_detail"""
    print("\n" + "="*60)
    print("场景 3: 错误检测 -> error + error_detail")
    print("="*60)

    # 清空日志
    print("[步骤0] 清空日志...")
    clear_logs()

    # 重置状态
    state.reset()

    # 先写入 busy 日志
    print("[步骤1] 写入 busy 日志...")
    write_log("feishu[default]: received message from ou_456: 查询数据库")
    time.sleep(1)

    # 确认 busy
    data = call_api()
    print(f"  当前状态: {data.get('emotion')}")

    # 写入错误日志
    print("[步骤2] 写入错误日志...")
    write_log("ERROR: TimeoutError: Request to external API timed out after 30s")

    # 等待 2 秒
    print("[步骤3] 等待 2 秒...")
    time.sleep(2)

    # 调用 API
    print("[步骤4] 调用 API...")
    data = call_api()
    if not data:
        return False

    emotion = data.get("emotion")
    error_detail = data.get("error_detail", "")

    print(f"  返回: emotion={emotion}")
    print(f"  error_detail: {error_detail}")

    # 校验: emotion 是 error 且有 error_detail
    if emotion == "error" and error_detail:
        print("\n✓ 场景3 通过: error + error_detail 正确")
        return True
    else:
        print(f"\n✗ 场景3 失败: emotion={emotion}, error_detail={error_detail}")
        return False


def main():
    print("="*60)
    print("OpenClaw-Tower 集成测试 - 三段式交互验证")
    print("="*60)

    # 检查后端
    try:
        with urllib.request.urlopen("http://localhost:5000/api/health", timeout=2):
            print("✓ Backend 服务运行中")
    except:
        print("✗ Backend 服务未运行，请先启动: python3 backend/app.py")
        return False

    results = []

    # 场景1
    results.append(("场景1: busy + user_msg", test_scenario_1()))

    # 场景2
    results.append(("场景2: idle + ai_reply", test_scenario_2()))

    # 场景3
    results.append(("场景3: error + error_detail", test_scenario_3()))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 所有测试通过! 交互核心逻辑验证成功!")
    else:
        print("\n⚠️ 部分测试失败，请检查状态机逻辑")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
