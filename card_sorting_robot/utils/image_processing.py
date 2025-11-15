"""
图像预处理模块
提供卡片图像的预处理功能，包括去噪、二值化、边缘检测等
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from PIL import Image


class ImageProcessor:
    """图像处理器类"""

    def __init__(self, config: dict = None):
        """
        初始化图像处理器

        Args:
            config: 图像处理配置字典
        """
        self.config = config or {}

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        对图像进行预处理

        Args:
            image: 输入图像(BGR格式)

        Returns:
            处理后的图像
        """
        processed = image.copy()

        # 转灰度图
        if self.config.get('grayscale', True):
            if len(processed.shape) == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # 去噪
        if self.config.get('denoise', True):
            strength = self.config.get('denoise_strength', 5)
            processed = cv2.fastNlMeansDenoising(processed, None, strength, 7, 21)

        # 自适应阈值二值化
        if self.config.get('adaptive_threshold', True):
            processed = cv2.adaptiveThreshold(
                processed,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )

        # 边缘检测
        if self.config.get('edge_detection', False):
            processed = cv2.Canny(processed, 50, 150)

        return processed

    def extract_roi(self,
                    image: np.ndarray,
                    roi: dict) -> np.ndarray:
        """
        提取感兴趣区域(ROI)

        Args:
            image: 输入图像
            roi: ROI配置字典，包含 x, y, width, height (相对坐标 0-1)

        Returns:
            ROI区域图像
        """
        h, w = image.shape[:2]

        # 计算实际像素坐标
        x = int(roi['x'] * w)
        y = int(roi['y'] * h)
        roi_w = int(roi['width'] * w)
        roi_h = int(roi['height'] * h)

        # 确保坐标在有效范围内
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        roi_w = min(roi_w, w - x)
        roi_h = min(roi_h, h - y)

        return image[y:y+roi_h, x:x+roi_w]

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        增强图像对比度

        Args:
            image: 输入图像

        Returns:
            对比度增强后的图像
        """
        # 使用CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(image.shape) == 2:  # 灰度图
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
        else:  # 彩色图
            # 转换到LAB色彩空间
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # 对L通道进行CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            # 合并通道并转回BGR
            lab = cv2.merge([l, a, b])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def remove_background(self, image: np.ndarray) -> np.ndarray:
        """
        去除背景（适用于卡片扫描）

        Args:
            image: 输入图像

        Returns:
            去除背景后的图像
        """
        # 转灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # 使用Otsu's阈值
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def detect_card(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        检测图像中的卡片边界

        Args:
            image: 输入图像

        Returns:
            卡片边界框 (x, y, w, h)，如果未检测到返回None
        """
        # 转灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)

        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # 找到最大的轮廓（假设为卡片）
        largest_contour = max(contours, key=cv2.contourArea)

        # 获取边界框
        x, y, w, h = cv2.boundingRect(largest_contour)

        # 验证边界框的合理性（卡片通常是矩形且有一定大小）
        image_area = image.shape[0] * image.shape[1]
        card_area = w * h
        if card_area < image_area * 0.1:  # 卡片至少占图像10%
            return None

        return (x, y, w, h)

    def rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        旋转图像

        Args:
            image: 输入图像
            angle: 旋转角度（度）

        Returns:
            旋转后的图像
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)

        # 获取旋转矩阵
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # 应用旋转
        rotated = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

        return rotated

    def resize_image(self,
                     image: np.ndarray,
                     width: Optional[int] = None,
                     height: Optional[int] = None,
                     keep_aspect_ratio: bool = True) -> np.ndarray:
        """
        调整图像大小

        Args:
            image: 输入图像
            width: 目标宽度
            height: 目标高度
            keep_aspect_ratio: 是否保持宽高比

        Returns:
            调整大小后的图像
        """
        h, w = image.shape[:2]

        if width is None and height is None:
            return image

        if keep_aspect_ratio:
            if width is not None:
                aspect_ratio = width / w
                height = int(h * aspect_ratio)
            elif height is not None:
                aspect_ratio = height / h
                width = int(w * aspect_ratio)
        else:
            if width is None:
                width = w
            if height is None:
                height = h

        resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        return resized

    def save_image(self,
                   image: np.ndarray,
                   filepath: str,
                   quality: int = 95):
        """
        保存图像到文件

        Args:
            image: 要保存的图像
            filepath: 保存路径
            quality: JPEG质量 (1-100)
        """
        if filepath.lower().endswith(('.jpg', '.jpeg')):
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        else:
            cv2.imwrite(filepath, image)

    @staticmethod
    def load_image(filepath: str) -> Optional[np.ndarray]:
        """
        从文件加载图像

        Args:
            filepath: 图像文件路径

        Returns:
            图像数组，如果加载失败返回None
        """
        image = cv2.imread(filepath)
        return image

    @staticmethod
    def show_image(image: np.ndarray, window_name: str = "Image", wait_key: bool = True):
        """
        显示图像（用于调试）

        Args:
            image: 要显示的图像
            window_name: 窗口名称
            wait_key: 是否等待按键
        """
        cv2.imshow(window_name, image)
        if wait_key:
            cv2.waitKey(0)
            cv2.destroyAllWindows()


def create_image_processor(config: dict) -> ImageProcessor:
    """
    从配置创建图像处理器

    Args:
        config: 完整配置字典

    Returns:
        ImageProcessor实例
    """
    image_config = config.get('image_processing', {})
    preprocessing_config = image_config.get('preprocessing', {})

    return ImageProcessor(preprocessing_config)


if __name__ == "__main__":
    # 测试代码
    processor = ImageProcessor({
        'grayscale': True,
        'denoise': True,
        'denoise_strength': 5,
        'adaptive_threshold': False
    })

    # 创建测试图像
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255

    # 测试预处理
    processed = processor.preprocess(test_image)
    print(f"原始图像形状: {test_image.shape}")
    print(f"处理后图像形状: {processed.shape}")

    # 测试ROI提取
    roi_config = {'x': 0.5, 'y': 0.5, 'width': 0.2, 'height': 0.2}
    roi = processor.extract_roi(test_image, roi_config)
    print(f"ROI图像形状: {roi.shape}")
