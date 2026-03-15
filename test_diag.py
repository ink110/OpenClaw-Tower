#!/usr/bin/env python3
"""
测试 OpenClaw-Tower 交互视角诊断功能
"""
import sys
import os
import json
import time
import datetime
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app import get_latest_log

API_URL = "http://localhost:5000/api/status"


def write_test_log(message):
    """写入测试日志"""
    log_file = get_latest_log()
    if not log_file:
        print("错误：无法找到日志文件")
        return False

    now = datetime.datetime.now()
    # 构建日志行
    log_line = f'{now.strftime("%Y-%m-%d %H:%M:%S")} [agent] {message}\n'

    with open(log_file, 'a') as f:
        f.write(log_line)

    print(f"  写入: {message}")
    return True


def test_busy_with_user_message():
    """测试1：模拟用户消息 -> 确认 busy + user_msg"""
    print("\n" + "="*50)
    print("测试 1: 用户消息 -> busy + user_msg")
    print("="*50)

    # 写入 [thought] 日志（会触发 busy）
    print("\n[步骤1] 写入 [thought] 日志...")
    write_test_log("[thought] 正在分析用户请求：搜索今天的科技新闻")

    time.sleep(1)

    # 调用 API
    print("\n[步骤2] 调用 /api/status...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        emotion = data.get('emotion')
        current_step = data.get('current_step')
        last_interaction = data.get('last_interaction', {})
        user_msg = last_interaction.get('user_msg', '')

        print(f"  返回: emotion={emotion}, step={current_step}")
        print(f"  last_interaction: {json.dumps(last_interaction, ensure_ascii=False)}")

        # 验证
        if emotion == 'busy' and user_msg:
            print("\n✓ 测试通过! 返回 busy 且包含用户消息")
            return True
        else:
            print(f"\n✗ 测试失败! emotion={emotion}, user_msg={user_msg}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_error_with_detail():
    """测试2：模拟错误 -> 确认 error + error_detail"""
    print("\n" + "="*50)
    print("测试 2: 错误日志 -> error + error_detail")
    print("="*50)

    # 先写入 [thought] 进入 busy
    print("\n[步骤0] 先写入 busy 日志...")
    write_test_log("[thought] 正在处理用户请求...")
    time.sleep(1)

    # 确认进入 busy
    with urllib.request.urlopen(API_URL, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
    print(f"  当前状态: {data.get('emotion')}")

    # 写入错误日志
    print("\n[步骤1] 写入 TimeoutError 日志...")
    write_test_log("ERROR: TimeoutError: Request to external API timed out after 30s")

    time.sleep(1)

    # 调用 API
    print("\n[步骤2] 调用 /api/status...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        emotion = data.get('emotion')
        error_detail = data.get('error_detail', '')
        current_step = data.get('current_step', '')

        print(f"  返回: emotion={emotion}, step={current_step}")
        print(f"  error_detail: {error_detail}")

        # 验证
        if emotion == 'error' and ('timeout' in error_detail.lower() or 'error' in error_detail.lower()):
            print("\n✓ 测试通过! 返回 error 且准确抓取了错误详情")
            return True
        else:
            print(f"\n✗ 测试失败! emotion={emotion}, error_detail={error_detail}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_idle_with_ai_reply():
    """测试3：模拟回复完成 -> 确认 idle + ai_reply"""
    print("\n" + "="*50)
    print("测试 3: AI 回复 -> idle + ai_reply")
    print("="*50)

    # 写入用户消息
    print("\n[步骤1] 写入用户消息...")
    write_test_log("[thought] 用户刚刚发送了消息：今天天气怎么样")

    time.sleep(1)

    # 写入回复完成日志
    print("\n[步骤2] 写入回复完成日志...")
    write_test_log("feishu[default]: dispatch complete - response sent")

    time.sleep(1)

    # 调用 API
    print("\n[步骤3] 调用 /api/status...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        emotion = data.get('emotion')
        last_interaction = data.get('last_interaction', {})
        ai_reply = last_interaction.get('ai_reply', '')

        print(f"  返回: emotion={emotion}")
        print(f"  last_interaction: {json.dumps(last_interaction, ensure_ascii=False)}")

        # 验证
        if emotion == 'idle' and ai_reply:
            print("\n✓ 测试通过! 返回 idle 且包含 AI 回复")
            return True
        else:
            print(f"\n✗ 测试失败! emotion={emotion}, ai_reply={ai_reply}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def main():
    print("="*50)
    print("OpenClaw-Tower 交互视角诊断测试")
    print("="*50)

    # 检查 backend 是否运行
    try:
        with urllib.request.urlopen("http://localhost:5000/api/health", timeout=2):
            print("✓ Backend 服务运行中")
    except:
        print("✗ Backend 服务未运行，请先启动: python3 backend/app.py")
        return False

    results = []

    # 测试1: busy + user_msg
    results.append(("用户消息->busy", test_busy_with_user_message()))

    # 测试2: error + error_detail
    results.append(("错误检测", test_error_with_detail()))

    # 测试3: idle + ai_reply
    results.append(("回复完成->idle", test_idle_with_ai_reply()))

    # 总结
    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n所有测试通过!")
    else:
        print("\n部分测试失败!")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
