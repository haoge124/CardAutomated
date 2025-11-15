"""
配置文件加载模块
负责加载和管理YAML配置文件
"""

import os
import yaml
from typing import Any, Dict


class ConfigLoader:
    """配置加载器类"""

    def __init__(self, config_path: str = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            config_path = os.path.join(project_root, 'config', 'settings.yaml')

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载YAML配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML格式错误
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"配置文件格式错误: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项值（支持点号分隔的嵌套键）

        Args:
            key: 配置项键名，支持点号分隔的嵌套键，如 "camera.resolution.width"
            default: 默认值

        Returns:
            配置项的值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置文件的某个section

        Args:
            section: section名称

        Returns:
            section对应的字典
        """
        return self.config.get(section, {})

    def reload(self):
        """重新加载配置文件"""
        self.config = self._load_config()

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.get(key) is not None


# 全局配置实例
_global_config = None


def get_config(config_path: str = None) -> ConfigLoader:
    """
    获取全局配置实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader(config_path)
    return _global_config


if __name__ == "__main__":
    # 测试代码
    try:
        config = ConfigLoader()
        print("相机设备ID:", config.get('camera.device_id'))
        print("相机分辨率:", config.get('camera.resolution'))
        print("OCR引擎:", config.get('ocr.engine'))
        print("机械臂类型:", config.get('robot_arm.type'))
        print("不存在的配置:", config.get('not.exist.key', 'default_value'))

        # 测试section获取
        camera_config = config.get_section('camera')
        print("\n相机完整配置:", camera_config)

    except Exception as e:
        print(f"错误: {e}")
