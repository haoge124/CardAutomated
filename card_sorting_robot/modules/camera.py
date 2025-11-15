"""
摄像头控制模块
负责控制摄像头进行图像采集
"""

import cv2
import numpy as np
import os
from datetime import datetime
from typing import Optional, Tuple
import time


class Camera:
    """摄像头控制类"""

    def __init__(self,
                 device_id: int = 0,
                 resolution: Tuple[int, int] = (1920, 1080),
                 fps: int = 30,
                 autofocus: bool = True,
                 exposure: int = -1,
                 brightness: int = 0,
                 contrast: int = 0):
        """
        初始化摄像头

        Args:
            device_id: 摄像头设备ID
            resolution: 分辨率 (宽, 高)
            fps: 帧率
            autofocus: 是否自动对焦
            exposure: 曝光值 (-1为自动)
            brightness: 亮度 (-100 到 100)
            contrast: 对比度
        """
        self.device_id = device_id
        self.resolution = resolution
        self.fps = fps
        self.cap = None
        self.is_opened = False

        # 摄像头参数
        self.autofocus = autofocus
        self.exposure = exposure
        self.brightness = brightness
        self.contrast = contrast

    def open(self) -> bool:
        """
        打开摄像头

        Returns:
            是否成功打开
        """
        if self.is_opened:
            return True

        self.cap = cv2.VideoCapture(self.device_id)

        if not self.cap.isOpened():
            return False

        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        # 设置帧率
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # 设置自动对焦
        if self.autofocus:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        else:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        # 设置曝光
        if self.exposure >= 0:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)  # 关闭自动曝光
            self.cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
        else:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 开启自动曝光

        # 设置亮度和对比度
        if self.brightness != 0:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)
        if self.contrast != 0:
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.contrast)

        self.is_opened = True
        return True

    def close(self):
        """关闭摄像头"""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        捕获一帧图像

        Returns:
            图像数组，如果失败返回None
        """
        if not self.is_opened:
            if not self.open():
                return None

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame

    def capture_multiple_frames(self, num_frames: int = 5) -> Optional[np.ndarray]:
        """
        捕获多帧图像并返回质量最好的一帧

        Args:
            num_frames: 要捕获的帧数

        Returns:
            质量最好的图像
        """
        frames = []
        scores = []

        for _ in range(num_frames):
            frame = self.capture_frame()
            if frame is not None:
                # 计算图像清晰度（使用Laplacian方差）
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                score = cv2.Laplacian(gray, cv2.CV_64F).var()
                frames.append(frame)
                scores.append(score)

            # 短暂延迟以获取不同的帧
            time.sleep(0.1)

        if not frames:
            return None

        # 返回清晰度最高的帧
        best_index = scores.index(max(scores))
        return frames[best_index]

    def save_image(self,
                   image: np.ndarray,
                   save_dir: str,
                   prefix: str = "card",
                   quality: int = 95) -> str:
        """
        保存图像到文件

        Args:
            image: 要保存的图像
            save_dir: 保存目录
            prefix: 文件名前缀
            quality: JPEG质量

        Returns:
            保存的文件路径
        """
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)

        # 保存图像
        cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, quality])

        return filepath

    def get_camera_info(self) -> dict:
        """
        获取摄像头信息

        Returns:
            摄像头参数字典
        """
        if not self.is_opened:
            return {}

        info = {
            'device_id': self.device_id,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'brightness': int(self.cap.get(cv2.CAP_PROP_BRIGHTNESS)),
            'contrast': int(self.cap.get(cv2.CAP_PROP_CONTRAST)),
            'exposure': int(self.cap.get(cv2.CAP_PROP_EXPOSURE)),
            'autofocus': bool(self.cap.get(cv2.CAP_PROP_AUTOFOCUS))
        }

        return info

    def set_parameter(self, param_name: str, value):
        """
        设置摄像头参数

        Args:
            param_name: 参数名称
            value: 参数值
        """
        if not self.is_opened:
            return

        param_map = {
            'brightness': cv2.CAP_PROP_BRIGHTNESS,
            'contrast': cv2.CAP_PROP_CONTRAST,
            'exposure': cv2.CAP_PROP_EXPOSURE,
            'autofocus': cv2.CAP_PROP_AUTOFOCUS,
            'width': cv2.CAP_PROP_FRAME_WIDTH,
            'height': cv2.CAP_PROP_FRAME_HEIGHT,
            'fps': cv2.CAP_PROP_FPS
        }

        if param_name in param_map:
            self.cap.set(param_map[param_name], value)

    def __enter__(self):
        """上下文管理器入口"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()


def create_camera_from_config(config: dict) -> Camera:
    """
    从配置创建摄像头实例

    Args:
        config: 完整配置字典

    Returns:
        Camera实例
    """
    camera_config = config.get('camera', {})
    resolution_config = camera_config.get('resolution', {})

    return Camera(
        device_id=camera_config.get('device_id', 0),
        resolution=(
            resolution_config.get('width', 1920),
            resolution_config.get('height', 1080)
        ),
        fps=camera_config.get('fps', 30),
        autofocus=camera_config.get('autofocus', True),
        exposure=camera_config.get('exposure', -1),
        brightness=camera_config.get('brightness', 0),
        contrast=camera_config.get('contrast', 0)
    )


if __name__ == "__main__":
    # 测试代码
    print("测试摄像头模块...")

    camera = Camera(device_id=0)

    if camera.open():
        print("摄像头打开成功")
        print("摄像头信息:", camera.get_camera_info())

        # 捕获图像
        frame = camera.capture_frame()
        if frame is not None:
            print(f"成功捕获图像，尺寸: {frame.shape}")

            # 保存测试图像
            filepath = camera.save_image(frame, "test_output", "test")
            print(f"图像已保存到: {filepath}")

        camera.close()
        print("摄像头已关闭")
    else:
        print("无法打开摄像头")
