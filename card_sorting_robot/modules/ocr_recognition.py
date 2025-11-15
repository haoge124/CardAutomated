"""
OCR识别模块
负责识别卡片上的番号信息
支持 EasyOCR 和 Tesseract 两种OCR引擎
"""

import re
import numpy as np
from typing import Optional, Tuple, List
import cv2


class OCRRecognizer:
    """OCR识别器基类"""

    def __init__(self,
                 engine: str = "easyocr",
                 languages: List[str] = None,
                 confidence_threshold: float = 0.6,
                 card_number_pattern: str = r"^[A-Z0-9\-]{5,15}$",
                 max_retry: int = 3):
        """
        初始化OCR识别器

        Args:
            engine: OCR引擎类型 ("easyocr" 或 "tesseract")
            languages: 支持的语言列表
            confidence_threshold: 置信度阈值
            card_number_pattern: 卡片番号的正则表达式模式
            max_retry: 最大重试次数
        """
        self.engine = engine.lower()
        self.languages = languages or ['en']
        self.confidence_threshold = confidence_threshold
        self.card_number_pattern = card_number_pattern
        self.max_retry = max_retry

        self.reader = None
        self._initialize_engine()

    def _initialize_engine(self):
        """初始化OCR引擎"""
        if self.engine == "easyocr":
            self._initialize_easyocr()
        elif self.engine == "tesseract":
            self._initialize_tesseract()
        else:
            raise ValueError(f"不支持的OCR引擎: {self.engine}")

    def _initialize_easyocr(self):
        """初始化EasyOCR引擎"""
        try:
            import easyocr
            self.reader = easyocr.Reader(self.languages, gpu=False)
        except ImportError:
            raise ImportError("请安装 easyocr: pip install easyocr")

    def _initialize_tesseract(self):
        """初始化Tesseract引擎"""
        try:
            import pytesseract
            self.tesseract = pytesseract
            # 测试tesseract是否可用
            self.tesseract.get_tesseract_version()
        except ImportError:
            raise ImportError("请安装 pytesseract: pip install pytesseract")
        except Exception:
            raise RuntimeError("Tesseract未正确安装，请运行: sudo apt-get install tesseract-ocr")

    def recognize(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        识别图像中的文本

        Args:
            image: 输入图像

        Returns:
            (识别的文本, 置信度)，如果识别失败返回(None, 0.0)
        """
        if self.engine == "easyocr":
            return self._recognize_easyocr(image)
        elif self.engine == "tesseract":
            return self._recognize_tesseract(image)
        else:
            return None, 0.0

    def _recognize_easyocr(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        使用EasyOCR识别

        Args:
            image: 输入图像

        Returns:
            (识别的文本, 置信度)
        """
        try:
            results = self.reader.readtext(image)

            if not results:
                return None, 0.0

            # 找到置信度最高的结果
            best_result = max(results, key=lambda x: x[2])
            text = best_result[1]
            confidence = best_result[2]

            # 清理文本
            text = self._clean_text(text)

            return text, confidence

        except Exception as e:
            print(f"EasyOCR识别错误: {e}")
            return None, 0.0

    def _recognize_tesseract(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        使用Tesseract识别

        Args:
            image: 输入图像

        Returns:
            (识别的文本, 置信度)
        """
        try:
            # 使用Tesseract识别
            data = self.tesseract.image_to_data(
                image,
                output_type=self.tesseract.Output.DICT,
                config='--psm 7'  # 单行文本模式
            )

            # 提取置信度最高的文本
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            texts = [text for text, conf in zip(data['text'], data['conf'])
                     if conf != '-1' and text.strip()]

            if not texts or not confidences:
                return None, 0.0

            # 组合文本
            text = ' '.join(texts)
            confidence = max(confidences) / 100.0  # 转换为0-1范围

            # 清理文本
            text = self._clean_text(text)

            return text, confidence

        except Exception as e:
            print(f"Tesseract识别错误: {e}")
            return None, 0.0

    def _clean_text(self, text: str) -> str:
        """
        清理识别的文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 去除空白字符
        text = text.strip()

        # 去除多余空格
        text = re.sub(r'\s+', '', text)

        # 转大写
        text = text.upper()

        return text

    def validate_card_number(self, text: str) -> bool:
        """
        验证卡片番号格式

        Args:
            text: 要验证的文本

        Returns:
            是否符合卡片番号格式
        """
        if not text:
            return False

        return bool(re.match(self.card_number_pattern, text))

    def recognize_card_number(self,
                              image: np.ndarray,
                              retry: bool = True) -> Tuple[Optional[str], float, bool]:
        """
        识别卡片番号

        Args:
            image: 输入图像
            retry: 是否在失败时重试

        Returns:
            (卡片番号, 置信度, 是否成功)
        """
        attempts = self.max_retry if retry else 1

        for attempt in range(attempts):
            text, confidence = self.recognize(image)

            # 检查置信度
            if confidence < self.confidence_threshold:
                if attempt < attempts - 1:
                    continue
                return text, confidence, False

            # 验证格式
            if not self.validate_card_number(text):
                if attempt < attempts - 1:
                    continue
                return text, confidence, False

            # 识别成功
            return text, confidence, True

        # 所有尝试都失败
        return None, 0.0, False

    def recognize_multiple_regions(self,
                                   image: np.ndarray,
                                   regions: List[dict]) -> List[Tuple[Optional[str], float]]:
        """
        识别图像中的多个区域

        Args:
            image: 输入图像
            regions: 区域列表，每个区域是一个包含 x, y, width, height 的字典

        Returns:
            识别结果列表 [(文本, 置信度), ...]
        """
        results = []

        for region in regions:
            # 提取ROI
            h, w = image.shape[:2]
            x = int(region['x'] * w)
            y = int(region['y'] * h)
            roi_w = int(region['width'] * w)
            roi_h = int(region['height'] * h)

            roi = image[y:y+roi_h, x:x+roi_w]

            # 识别
            text, confidence = self.recognize(roi)
            results.append((text, confidence))

        return results


def create_ocr_recognizer_from_config(config: dict) -> OCRRecognizer:
    """
    从配置创建OCR识别器

    Args:
        config: 完整配置字典

    Returns:
        OCRRecognizer实例
    """
    ocr_config = config.get('ocr', {})

    return OCRRecognizer(
        engine=ocr_config.get('engine', 'easyocr'),
        languages=ocr_config.get('languages', ['en']),
        confidence_threshold=ocr_config.get('confidence_threshold', 0.6),
        card_number_pattern=ocr_config.get('card_number_pattern', r"^[A-Z0-9\-]{5,15}$"),
        max_retry=ocr_config.get('max_retry', 3)
    )


if __name__ == "__main__":
    # 测试代码
    print("测试OCR识别模块...")

    # 创建测试图像（带文本）
    test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(test_image, "ABC12345", (50, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

    try:
        recognizer = OCRRecognizer(engine="tesseract", languages=['eng'])
        text, confidence = recognizer.recognize(test_image)
        print(f"识别结果: {text}, 置信度: {confidence:.2f}")

        is_valid = recognizer.validate_card_number(text)
        print(f"格式验证: {is_valid}")

    except Exception as e:
        print(f"测试失败: {e}")
        print("注意: 需要安装OCR引擎才能运行测试")
