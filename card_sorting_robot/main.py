#!/usr/bin/env python3
"""
卡片自动化识别和分拣系统 - 主程序
基于机械臂的游戏王卡片自动扫描、识别和分拣系统
"""

import argparse
import sys
import os
import time
from datetime import datetime
from typing import Optional

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import get_config
from utils.logger import setup_logger_from_config
from utils.image_processing import create_image_processor
from modules.camera import create_camera_from_config
from modules.ocr_recognition import create_ocr_recognizer_from_config
from modules.database import create_database_from_config
from modules.robot_arm import create_robot_arm_from_config


class CardSortingRobot:
    """卡片分拣机器人主控制类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化卡片分拣机器人

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = get_config(config_path)

        # 初始化日志
        self.logger = setup_logger_from_config(self.config.config)

        self.logger.info("="*60)
        self.logger.info("卡片分拣机器人系统启动")
        self.logger.info("="*60)

        # 初始化各个模块
        self.logger.info("正在初始化系统模块...")

        try:
            # 图像处理器
            self.image_processor = create_image_processor(self.config.config)
            self.logger.info("✓ 图像处理器初始化成功")

            # 摄像头
            self.camera = create_camera_from_config(self.config.config)
            self.logger.info("✓ 摄像头模块初始化成功")

            # OCR识别器
            self.ocr = create_ocr_recognizer_from_config(self.config.config)
            self.logger.info("✓ OCR识别器初始化成功")

            # 数据库
            self.database = create_database_from_config(self.config.config)
            self.logger.info("✓ 数据库初始化成功")

            # 机械臂
            self.robot = create_robot_arm_from_config(self.config.config)
            self.logger.info("✓ 机械臂模块初始化成功")

        except Exception as e:
            self.logger.error(f"模块初始化失败: {e}")
            raise

        # 运行统计
        self.total_processed = 0
        self.success_count = 0
        self.failed_count = 0
        self.start_time = None

        # 获取配置参数
        self.max_cards = self.config.get('main_process.max_cards', 0)
        self.scan_interval = self.config.get('main_process.scan_interval', 0.5)
        self.auto_resume = self.config.get('main_process.auto_resume', True)
        self.stop_on_error = self.config.get('main_process.stop_on_error', False)
        self.stats_interval = self.config.get('main_process.statistics_interval', 10)

        # 图像保存配置
        self.save_original = self.config.get('image_processing.save_original', True)
        self.save_processed = self.config.get('image_processing.save_processed', True)
        self.image_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data/images'
        )

        # OCR ROI配置
        self.roi_config = self.config.get_section('ocr').get('roi', {})

    def initialize_hardware(self) -> bool:
        """
        初始化硬件设备

        Returns:
            是否成功
        """
        self.logger.info("正在初始化硬件设备...")

        # 连接摄像头
        if not self.camera.open():
            self.logger.error("无法打开摄像头")
            return False
        self.logger.info("✓ 摄像头已连接")

        # 连接机械臂
        if not self.robot.connect():
            self.logger.error("无法连接机械臂")
            return False
        self.logger.info("✓ 机械臂已连接")

        # 回到初始位置
        if not self.robot.home():
            self.logger.error("机械臂回零失败")
            return False
        self.logger.info("✓ 机械臂已回到初始位置")

        return True

    def process_single_card(self) -> bool:
        """
        处理单张卡片的完整流程

        Returns:
            是否成功完成处理
        """
        try:
            # 1. 抓取卡片
            self.logger.info(f"[{self.total_processed + 1}] 开始抓取卡片...")
            if not self.robot.pick_card():
                self.logger.error("抓取卡片失败")
                return False

            # 2. 移动到扫描位置
            self.logger.info("移动到扫描位置...")
            if not self.robot.move_to_scan_position():
                self.logger.error("移动到扫描位置失败")
                return False

            # 等待稳定
            time.sleep(self.scan_interval)

            # 3. 拍摄图像
            self.logger.info("拍摄卡片图像...")
            image = self.camera.capture_multiple_frames(num_frames=3)
            if image is None:
                self.logger.error("图像采集失败")
                return False

            # 保存原始图像
            original_path = None
            if self.save_original:
                original_path = self.camera.save_image(
                    image,
                    self.image_dir,
                    prefix="original"
                )
                self.logger.debug(f"原始图像已保存: {original_path}")

            # 4. 提取ROI并预处理
            self.logger.info("提取ROI区域...")
            roi_image = self.image_processor.extract_roi(image, self.roi_config)

            # 预处理图像
            self.logger.info("预处理图像...")
            processed_image = self.image_processor.preprocess(roi_image)

            # 保存处理后的图像
            processed_path = None
            if self.save_processed:
                processed_path = self.camera.save_image(
                    processed_image,
                    self.image_dir,
                    prefix="processed"
                )
                self.logger.debug(f"处理后图像已保存: {processed_path}")

            # 5. OCR识别
            self.logger.info("识别卡片番号...")
            card_number, confidence, recognition_success = self.ocr.recognize_card_number(
                processed_image,
                retry=True
            )

            # 6. 记录结果
            if recognition_success:
                self.logger.info(f"✓ 识别成功: {card_number} (置信度: {confidence:.2f})")
                status = 'success'
                self.success_count += 1
            else:
                self.logger.warning(f"✗ 识别失败: {card_number} (置信度: {confidence:.2f})")
                status = 'failed'
                self.failed_count += 1

            # 7. 保存到数据库
            self.database.insert_card(
                card_number=card_number,
                confidence=confidence,
                image_path=original_path,
                processed_image_path=processed_path,
                status=status
            )

            # 8. 放置卡片
            self.logger.info(f"放置卡片到{'成功' if recognition_success else '失败'}区...")
            if not self.robot.place_card(success=recognition_success):
                self.logger.error("放置卡片失败")
                return False

            # 9. 回到初始位置
            if not self.robot.home():
                self.logger.error("回到初始位置失败")
                return False

            self.total_processed += 1

            # 定期输出统计信息
            if self.total_processed % self.stats_interval == 0:
                self.print_statistics()

            return True

        except Exception as e:
            self.logger.exception(f"处理卡片时发生错误: {e}")
            return False

    def run(self):
        """运行主循环"""
        self.logger.info("开始运行主循环...")
        self.start_time = datetime.now()

        # 初始化硬件
        if not self.initialize_hardware():
            self.logger.error("硬件初始化失败，系统退出")
            return

        try:
            while True:
                # 检查是否达到最大卡片数
                if self.max_cards > 0 and self.total_processed >= self.max_cards:
                    self.logger.info(f"已达到最大处理数量: {self.max_cards}")
                    break

                # 处理单张卡片
                success = self.process_single_card()

                if not success:
                    if self.stop_on_error:
                        self.logger.error("发生错误，停止运行")
                        break
                    elif self.auto_resume:
                        self.logger.warning("发生错误，尝试继续...")
                        time.sleep(2)
                        continue
                    else:
                        self.logger.error("发生错误，等待用户处理...")
                        input("按Enter继续...")

        except KeyboardInterrupt:
            self.logger.info("用户中断程序")

        finally:
            self.cleanup()

    def print_statistics(self):
        """打印统计信息"""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        speed = self.total_processed / elapsed_time if elapsed_time > 0 else 0

        self.logger.info("="*60)
        self.logger.info("统计信息")
        self.logger.info("-"*60)
        self.logger.info(f"已处理: {self.total_processed} 张")
        self.logger.info(f"成功: {self.success_count} 张 ({self.success_count/self.total_processed*100:.1f}%)")
        self.logger.info(f"失败: {self.failed_count} 张 ({self.failed_count/self.total_processed*100:.1f}%)")
        self.logger.info(f"运行时间: {elapsed_time:.1f} 秒")
        self.logger.info(f"处理速度: {speed:.2f} 张/秒")
        self.logger.info("="*60)

        # 获取数据库统计
        db_stats = self.database.get_statistics()
        self.logger.info(f"数据库记录: {db_stats}")

    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理资源...")

        # 打印最终统计
        if self.total_processed > 0:
            self.print_statistics()

        # 关闭摄像头
        self.camera.close()
        self.logger.info("✓ 摄像头已关闭")

        # 断开机械臂
        self.robot.disconnect()
        self.logger.info("✓ 机械臂已断开")

        # 关闭数据库
        self.database.close()
        self.logger.info("✓ 数据库已关闭")

        self.logger.info("系统已安全关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='卡片自动化识别和分拣系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        help='配置文件路径',
        default=None
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='启用调试模式'
    )

    parser.add_argument(
        '-s', '--simulation',
        action='store_true',
        help='启用仿真模式（不连接实际硬件）'
    )

    parser.add_argument(
        '-n', '--num-cards',
        type=int,
        help='要处理的卡片数量（0表示无限制）',
        default=None
    )

    args = parser.parse_args()

    # 创建机器人实例
    try:
        robot = CardSortingRobot(config_path=args.config)

        # 应用命令行参数
        if args.num_cards is not None:
            robot.max_cards = args.num_cards

        if args.simulation:
            robot.robot.simulation_mode = True
            robot.logger.info("仿真模式已启用")

        # 运行
        robot.run()

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
