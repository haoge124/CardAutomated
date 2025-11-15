#!/usr/bin/env python3
"""
摄像头测试脚本
用于测试摄像头连接和图像采集功能
"""

import sys
import os
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import get_config
from modules.camera import create_camera_from_config


def main():
    """主函数"""
    print("="*60)
    print("摄像头测试程序")
    print("="*60)

    # 加载配置
    config = get_config()
    camera = create_camera_from_config(config.config)

    # 打开摄像头
    print("\n正在打开摄像头...")
    if not camera.open():
        print("❌ 无法打开摄像头")
        print("\n可能的原因：")
        print("1. 摄像头未连接")
        print("2. 设备ID不正确（当前配置: {}）".format(config.get('camera.device_id')))
        print("3. 摄像头被其他程序占用")
        print("\n请检查配置文件 config/settings.yaml")
        return

    print("✓ 摄像头打开成功")

    # 显示摄像头信息
    info = camera.get_camera_info()
    print("\n摄像头信息：")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 测试图像采集
    print("\n正在采集图像...")
    frame = camera.capture_frame()

    if frame is None:
        print("❌ 图像采集失败")
        camera.close()
        return

    print(f"✓ 图像采集成功，尺寸: {frame.shape}")

    # 保存测试图像
    save_path = camera.save_image(frame, "data/images", "test_camera")
    print(f"✓ 测试图像已保存到: {save_path}")

    # 显示实时预览（可选）
    print("\n按 'q' 退出实时预览，按 's' 保存当前帧...")
    while True:
        frame = camera.capture_frame()
        if frame is None:
            break

        # 显示图像
        cv2.imshow("Camera Test - Press 'q' to quit, 's' to save", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            path = camera.save_image(frame, "data/images", "snapshot")
            print(f"图像已保存: {path}")

    cv2.destroyAllWindows()
    camera.close()
    print("\n摄像头已关闭")
    print("测试完成！")


if __name__ == "__main__":
    main()
