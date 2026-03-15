#!/usr/bin/env python3
"""
测试 OpenClaw-Tower 实时监控功能
"""
import sys
import os
import json
import time
import datetime
import urllib.request
import subprocess

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import get_latest_log, parse_status

API_URL = "http://localhost:5000/api/status"

def write_test_log(message="[thought] processing"):
    """写入测试日志"""
    log_file = get_latest_log()
    if not log_file:
        print("错误：无法找到日志文件")
        return False

    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')

    # 构建日志行（使用 [thought] 格式）
    log_line = f'{now.strftime("%Y-%m-%d %H:%M:%S")} [agent] {message}\n'

    with open(log_file, 'a') as f:
        f.write(log_line)

    print(f"✓ 写入测试日志: {message}")
    return True

def test_idle_to_busy():
    """测试从 idle 到 busy 的状态转换"""
    print("\n" + "="*50)
    print("测试: idle -> busy 状态转换")
    print("="*50)

    # 1. 写入一条 [thought] 日志
    print("\n[步骤1] 写入 [thought] 日志...")
    write_test_log("[thought] Searching for latest news")

    # 等待 1 秒让日志写入
    time.sleep(1)

    # 2. 调用 API 获取状态
    print("[步骤2] 调用 /api/status 接口...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        print(f"   返回结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

        # 3. 验证结果
        emotion = data.get('emotion')
        current_step = data.get('current_step')

        if emotion == 'busy' and 'thought' in current_step.lower():
            print("\n✓ 测试通过! 状态正确识别为 busy")
            return True
        else:
            print(f"\n✗ 测试失败! emotion={emotion}, current_step={current_step}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False

def test_busy_to_idle():
    """测试从 busy 到 idle 的状态转换（超时后）"""
    print("\n" + "="*50)
    print("测试: busy -> idle 状态转换（超时测试）")
    print("="*50)

    # 先写入一条新日志确认 busy 状态
    print("\n[步骤1] 先写入一条新日志确保 busy 状态...")
    write_test_log("[thought] Thinking about the answer")

    time.sleep(1)

    # 确认是 busy
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        current_emotion = data.get('emotion')
        print(f"   当前状态: {current_emotion}")
    except:
        pass

    # 等待 11 秒让日志过期
    print("\n[步骤2] 等待 11 秒让日志过期...")
    for i in range(11, 0, -1):
        print(f"   等待 {i} 秒...", end='\r')
        time.sleep(1)
    print("\n   完成等待!")

    # 调用 API
    print("[步骤3] 调用 /api/status 接口...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        emotion = data.get('emotion')

        if emotion == 'idle':
            print(f"\n✓ 测试通过! 状态正确回滚为 idle")
            return True
        else:
            print(f"\n✗ 测试失败! 状态应该是 idle，但实际是 {emotion}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False

def main():
    print("="*50)
    print("OpenClaw-Tower 实时监控测试")
    print("="*50)

    # 检查 backend 是否运行
    try:
        with urllib.request.urlopen("http://localhost:5000/api/health", timeout=2):
            print("✓ Backend 服务运行中")
    except:
        print("✗ Backend 服务未运行，请先启动: python3 backend/app.py")
        return

    # 运行测试
    results = []

    # 测试1: idle -> busy
    results.append(("idle -> busy", test_idle_to_busy()))

    # 测试2: busy -> idle (超时)
    results.append(("busy -> idle", test_busy_to_idle()))

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
