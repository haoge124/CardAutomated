#!/usr/bin/env python3
"""
OCR 识别测试脚本
用于测试 OCR 识别功能
"""

import sys
import os
import cv2
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import get_config
from utils.image_processing import create_image_processor
from modules.ocr_recognition import create_ocr_recognizer_from_config


def test_ocr_with_image(image_path: str):
    """
    使用指定图像测试OCR

    Args:
        image_path: 图像文件路径
    """
    print("="*60)
    print("OCR 识别测试程序")
    print("="*60)

    # 加载配置
    config = get_config()

    # 创建OCR识别器
    print(f"\n正在初始化 OCR 引擎: {config.get('ocr.engine')}...")
    try:
        ocr = create_ocr_recognizer_from_config(config.config)
        print("✓ OCR 引擎初始化成功")
    except Exception as e:
        print(f"❌ OCR 引擎初始化失败: {e}")
        print("\n请确保已安装必要的依赖：")
        print("  - EasyOCR: pip install easyocr")
        print("  - Tesseract: sudo apt-get install tesseract-ocr")
        return

    # 创建图像处理器
    image_processor = create_image_processor(config.config)

    # 加载图像
    print(f"\n正在加载图像: {image_path}...")
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ 无法加载图像: {image_path}")
        return

    print(f"✓ 图像加载成功，尺寸: {image.shape}")

    # 获取ROI配置
    roi_config = config.get_section('ocr').get('roi', {})

    # 提取ROI
    print("\n提取 ROI 区域...")
    roi_image = image_processor.extract_roi(image, roi_config)
    print(f"ROI 尺寸: {roi_image.shape}")

    # 保存ROI图像
    roi_path = "data/images/test_roi.jpg"
    cv2.imwrite(roi_path, roi_image)
    print(f"ROI 图像已保存: {roi_path}")

    # 预处理图像
    print("\n预处理图像...")
    processed = image_processor.preprocess(roi_image)

    # 保存处理后的图像
    processed_path = "data/images/test_processed.jpg"
    cv2.imwrite(processed_path, processed)
    print(f"处理后图像已保存: {processed_path}")

    # OCR 识别
    print("\n正在识别卡片番号...")
    card_number, confidence, success = ocr.recognize_card_number(processed, retry=True)

    print("\n识别结果：")
    print("-"*60)
    if success:
        print(f"✓ 识别成功")
        print(f"  卡片番号: {card_number}")
        print(f"  置信度: {confidence:.4f} ({confidence*100:.2f}%)")
    else:
        print(f"✗ 识别失败")
        print(f"  识别文本: {card_number}")
        print(f"  置信度: {confidence:.4f} ({confidence*100:.2f}%)")
        print(f"  阈值: {ocr.confidence_threshold:.4f}")

    print("-"*60)

    # 显示图像
    print("\n显示图像（按任意键关闭）...")
    cv2.imshow("Original", image)
    cv2.imshow("ROI", roi_image)
    cv2.imshow("Processed", processed)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def test_ocr_with_camera():
    """使用摄像头实时测试OCR"""
    print("="*60)
    print("OCR 实时识别测试程序")
    print("="*60)

    # 加载配置
    config = get_config()

    # 导入摄像头模块
    from modules.camera import create_camera_from_config

    # 创建摄像头
    camera = create_camera_from_config(config.config)
    if not camera.open():
        print("❌ 无法打开摄像头")
        return

    # 创建OCR识别器
    try:
        ocr = create_ocr_recognizer_from_config(config.config)
    except Exception as e:
        print(f"❌ OCR 引擎初始化失败: {e}")
        camera.close()
        return

    # 创建图像处理器
    image_processor = create_image_processor(config.config)
    roi_config = config.get_section('ocr').get('roi', {})

    print("\n按 'c' 进行识别，按 'q' 退出...")

    while True:
        frame = camera.capture_frame()
        if frame is None:
            break

        # 提取并显示ROI
        roi = image_processor.extract_roi(frame, roi_config)

        # 在原图上绘制ROI框
        h, w = frame.shape[:2]
        x = int(roi_config['x'] * w)
        y = int(roi_config['y'] * h)
        roi_w = int(roi_config['width'] * w)
        roi_h = int(roi_config['height'] * h)
        cv2.rectangle(frame, (x, y), (x+roi_w, y+roi_h), (0, 255, 0), 2)
        cv2.putText(frame, "ROI", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)

        cv2.imshow("Camera - Press 'c' to recognize, 'q' to quit", frame)
        cv2.imshow("ROI", roi)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            print("\n正在识别...")
            processed = image_processor.preprocess(roi)
            card_number, confidence, success = ocr.recognize_card_number(
                processed, retry=False
            )

            if success:
                print(f"✓ 识别成功: {card_number} (置信度: {confidence:.2f})")
            else:
                print(f"✗ 识别失败: {card_number} (置信度: {confidence:.2f})")

    cv2.destroyAllWindows()
    camera.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OCR 识别测试')
    parser.add_argument('-i', '--image', type=str, help='测试图像路径')
    parser.add_argument('-c', '--camera', action='store_true', help='使用摄像头实时测试')

    args = parser.parse_args()

    if args.camera:
        test_ocr_with_camera()
    elif args.image:
        test_ocr_with_image(args.image)
    else:
        print("请指定测试模式：")
        print("  使用图像测试: python test_ocr.py -i <image_path>")
        print("  使用摄像头测试: python test_ocr.py -c")


if __name__ == "__main__":
    main()
