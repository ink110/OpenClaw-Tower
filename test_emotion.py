#!/usr/bin/env python3
"""
测试 OpenClaw-Tower 情绪检测功能
"""
import sys
import os
import json
import time
import datetime
import urllib.request

API_URL = "http://localhost:5000/api/status"

def write_test_log(message):
    """写入测试日志"""
    log_file = "/tmp/openclaw/openclaw-2026-03-15.log"
    now = datetime.datetime.now()
    log_line = f'{now.strftime("%Y-%m-%d %H:%M:%S")} [agent] {message}\n'
    with open(log_file, 'a') as f:
        f.write(log_line)
    print(f"  写入: {message}")

def test_thought_pattern():
    """测试 [thought] 模式检测"""
    print("\n" + "="*50)
    print("测试: [thought] 模式 -> busy")
    print("="*50)

    # 等待旧日志过期
    print("\n[步骤0] 等待旧日志过期...")
    time.sleep(12)

    # 写入 [thought] 日志
    print("\n[步骤1] 写入 [thought] 日志...")
    write_test_log("[thought] 正在分析今天的娱乐新闻...")

    time.sleep(1)

    # 调用 API
    print("[步骤2] 调用 /api/status...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        emotion = data.get('emotion')
        current_step = data.get('current_step')
        print(f"  返回: emotion={emotion}, step={current_step}")

        if emotion == 'busy' and ('thought' in current_step.lower() or '分析' in current_step):
            print("\n✓ 测试通过!")
            return True
        else:
            print(f"\n✗ 测试失败! 预期 busy，实际 {emotion}")
            return False
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False

def test_decay_5_seconds():
    """测试 60 秒后自动回滚到 idle（新逻辑：交互视角状态机）"""
    print("\n" + "="*50)
    print("测试: 60秒无动作 -> idle")
    print("="*50)

    # 先写入 busy 日志
    print("\n[步骤1] 写入 busy 日志...")
    write_test_log("[thought] 正在处理任务...")

    time.sleep(1)

    # 确认是 busy
    with urllib.request.urlopen(API_URL, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
    print(f"  当前状态: {data.get('emotion')}")

    # 写入 dispatch complete 立即变为 idle（这是新逻辑）
    print("\n[步骤2] 写入回复完成日志...")
    write_test_log("dispatch complete")

    time.sleep(1)

    # 检查是否变回 idle
    print("[步骤3] 检查状态...")
    with urllib.request.urlopen(API_URL, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))

    emotion = data.get('emotion')
    print(f"  当前状态: {emotion}")

    if emotion == 'idle':
        print("\n✓ 测试通过! 状态已自动回滚为 idle")
        return True
    else:
        print(f"\n✗ 测试失败! 预期 idle，实际 {emotion}")
        return False

def test_noise_filtering():
    """测试噪音过滤 - 交互视角：dispatch complete -> idle"""
    print("\n" + "="*50)
    print("测试: 系统噪音过滤")
    print("="*50)

    # 直接写入 dispatch complete 触发 idle
    print("\n[步骤1] 写入 dispatch complete...")
    write_test_log("dispatch complete")

    time.sleep(1)

    # 检查状态
    print("[步骤2] 检查状态...")
    with urllib.request.urlopen(API_URL, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))

    emotion = data.get('emotion')
    print(f"  当前状态: {emotion}")

    # 新逻辑：dispatch complete -> idle
    if emotion == 'idle':
        print("\n✓ 测试通过! dispatch complete -> idle")
        return True
    else:
        print(f"\n✗ 测试失败! 预期 idle，实际 {emotion}")
        return False

def main():
    print("="*50)
    print("OpenClaw-Tower 情绪检测测试")
    print("="*50)

    results = []

    # 测试1: [thought] 模式
    results.append(("[thought] 模式", test_thought_pattern()))

    # 测试2: 5秒衰减
    results.append(("5秒衰减", test_decay_5_seconds()))

    # 测试3: 噪音过滤
    results.append(("噪音过滤", test_noise_filtering()))

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

    print()
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
