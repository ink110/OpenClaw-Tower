#!/usr/bin/env python3
"""
飞书交互精准监控 - 自动化闭环测试
"""
import sys
import os
import json
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app import get_latest_log, state

API_URL = "http://localhost:5000/api/status"

def clear_log():
    """清空日志"""
    log_file = get_latest_log()
    if log_file:
        with open(log_file, 'w') as f:
            f.write('')

def write_log(msg):
    """写入日志"""
    log_file = get_latest_log()
    if not log_file:
        return False
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f'{now} [feishu] {msg}\n')
    return True

def call_api():
    """调用API"""
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return None

def test_busy():
    """测试A: 伪造指令 -> busy"""
    print("\n" + "="*50)
    print("测试A: 伪造指令 -> busy")
    print("="*50)

    clear_log()
    state.reset()

    # 写入用户消息
    write_log('feishu[default]: received message from ou_test: 测试用户消息')
    time.sleep(1)

    data = call_api()
    if not data:
        print("✗ API调用失败")
        return False

    emotion = data.get('emotion')
    print(f"  返回: emotion={emotion}")

    if emotion == 'busy':
        print("✓ 测试A通过")
        return True
    print(f"✗ 测试A失败: 预期busy，实际{emotion}")
    return False

def test_idle():
    """测试B: 伪造成功 -> idle"""
    print("\n" + "="*50)
    print("测试B: 伪造成功 -> idle")
    print("="*50)

    clear_log()
    state.reset()

    # 先写入成功信号
    write_log('feishu[default]: dispatch complete (queuedFinal=true)')
    time.sleep(1)

    data = call_api()
    if not data:
        print("✗ API调用失败")
        return False

    emotion = data.get('emotion')
    print(f"  返回: emotion={emotion}")

    if emotion == 'idle':
        print("✓ 测试B通过")
        return True
    print(f"✗ 测试B失败: 预期idle，实际{emotion}")
    return False

def test_error():
    """测试C: 伪造错误 -> error (<=15字)"""
    print("\n" + "="*50)
    print("测试C: 伪造错误 -> error")
    print("="*50)

    clear_log()
    state.reset()

    # 写入错误
    write_log('ERROR: Connection Refused to external service')
    time.sleep(1)

    data = call_api()
    if not data:
        print("✗ API调用失败")
        return False

    emotion = data.get('emotion')
    error_detail = data.get('error_detail', '')

    # 检查error_detail长度
    error_len = len(error_detail)
    print(f"  返回: emotion={emotion}, error_detail={error_detail} (长度:{error_len})")

    if emotion == 'error' and error_len <= 15:
        print("✓ 测试C通过")
        return True

    if error_len > 15:
        print(f"✗ 错误描述超过15字: {error_len}字")
    else:
        print(f"✗ 测试C失败: 预期error，实际{emotion}")
    return False

def test_logs_reversed():
    """测试D: 日志倒序"""
    print("\n" + "="*50)
    print("测试D: 日志倒序")
    print("="*50)

    clear_log()

    # 写入多条日志
    write_log('feishu[default]: received message from ou_1: 消息1')
    time.sleep(0.1)
    write_log('feishu[default]: dispatch complete')
    time.sleep(0.1)
    write_log('ERROR: Test error')

    time.sleep(1)

    try:
        with urllib.request.urlopen("http://localhost:5000/api/logs", timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except:
        print("✗ API调用失败")
        return False

    logs = data.get('logs', [])
    if not logs:
        print("✗ 无日志返回")
        return False

    # 检查是否倒序
    times = [log.get('time', '') for log in logs]
    print(f"  日志时间顺序: {times}")

    if len(times) >= 2 and times[0] >= times[1]:
        print("✓ 测试D通过 (日志倒序)")
        return True

    print("✗ 日志未倒序")
    return False

def main():
    print("="*50)
    print("飞书交互精准监控 - 自动化闭环测试")
    print("="*50)

    # 检查后端
    try:
        with urllib.request.urlopen("http://localhost:5000/api/health", timeout=2):
            print("✓ Backend运行中")
    except:
        print("✗ Backend未运行")
        return False

    results = []
    max_try = 3

    for i in range(max_try):
        print(f"\n=== 第{i+1}轮测试 ===")

        a = test_busy()
        b = test_idle()
        c = test_error()
        d = test_logs_reversed()

        results.append((a, b, c, d))

        if a and b and c and d:
            print("\n" + "="*50)
            print("🎉 所有测试通过!")
            print("="*50)
            return True

        print(f"\n⚠️ 第{i+1}轮未完全通过，继续...")

    # 统计
    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    for i, (a,b,c,d) in enumerate(results):
        print(f"第{i+1}轮: A={a}, B={b}, C={c}, D={d}")

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
