"""
机械臂控制模块
负责控制SO-ARM100或兼容机械臂进行卡片抓取和放置
"""

import serial
import time
from typing import Dict, Tuple, Optional, List
from enum import Enum


class Position(Enum):
    """位置枚举"""
    HOME = "home"
    CARD_PILE = "card_pile"
    SCAN = "scan_position"
    SUCCESS = "success_pile"
    FAILED = "failed_pile"


class RobotArm:
    """机械臂控制类"""

    def __init__(self,
                 port: str = "/dev/ttyUSB0",
                 baudrate: int = 115200,
                 timeout: float = 1.0,
                 positions: Dict = None,
                 motion_config: Dict = None,
                 safety_config: Dict = None,
                 simulation_mode: bool = False):
        """
        初始化机械臂

        Args:
            port: 串口设备路径
            baudrate: 波特率
            timeout: 超时时间
            positions: 位置配置字典
            motion_config: 运动参数配置
            safety_config: 安全配置
            simulation_mode: 仿真模式（不实际连接硬件）
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.simulation_mode = simulation_mode

        self.positions = positions or {}
        self.motion_config = motion_config or {}
        self.safety_config = safety_config or {}

        self.serial_conn = None
        self.is_connected = False
        self.current_position = None

        # 从配置中读取参数
        self.speed = self.motion_config.get('speed', 50)
        self.acceleration = self.motion_config.get('acceleration', 30)
        self.gripper_open_value = self.motion_config.get('gripper_open_value', 100)
        self.gripper_close_value = self.motion_config.get('gripper_close_value', 0)
        self.grip_delay = self.motion_config.get('grip_delay', 0.5)
        self.release_delay = self.motion_config.get('release_delay', 0.3)

        self.max_retries = self.safety_config.get('max_retries', 3)

    def connect(self) -> bool:
        """
        连接机械臂

        Returns:
            是否成功连接
        """
        if self.simulation_mode:
            print("[仿真模式] 模拟连接机械臂")
            self.is_connected = True
            return True

        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.is_connected = True
            time.sleep(2)  # 等待连接稳定
            return True

        except serial.SerialException as e:
            print(f"连接机械臂失败: {e}")
            return False

    def disconnect(self):
        """断开机械臂连接"""
        if self.simulation_mode:
            print("[仿真模式] 模拟断开机械臂")
            self.is_connected = False
            return

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False

    def send_command(self, command: str) -> bool:
        """
        发送命令到机械臂

        Args:
            command: 命令字符串

        Returns:
            是否发送成功
        """
        if self.simulation_mode:
            print(f"[仿真模式] 发送命令: {command}")
            return True

        if not self.is_connected:
            print("机械臂未连接")
            return False

        try:
            self.serial_conn.write(command.encode('utf-8'))
            self.serial_conn.write(b'\n')
            time.sleep(0.1)
            return True

        except Exception as e:
            print(f"发送命令失败: {e}")
            return False

    def read_response(self) -> Optional[str]:
        """
        读取机械臂响应

        Returns:
            响应字符串，如果失败返回None
        """
        if self.simulation_mode:
            return "OK"

        if not self.is_connected:
            return None

        try:
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode('utf-8').strip()
                return response
            return None

        except Exception as e:
            print(f"读取响应失败: {e}")
            return None

    def move_to_position(self, position: Position, wait: bool = True) -> bool:
        """
        移动到指定位置

        Args:
            position: 目标位置
            wait: 是否等待运动完成

        Returns:
            是否成功
        """
        pos_config = self.positions.get(position.value)
        if not pos_config:
            print(f"位置配置不存在: {position.value}")
            return False

        return self.move_to_coordinates(
            x=pos_config['x'],
            y=pos_config['y'],
            z=pos_config['z'],
            rx=pos_config.get('rx', 0),
            ry=pos_config.get('ry', 0),
            rz=pos_config.get('rz', 0),
            wait=wait
        )

    def move_to_coordinates(self,
                           x: float,
                           y: float,
                           z: float,
                           rx: float = 0,
                           ry: float = 0,
                           rz: float = 0,
                           wait: bool = True) -> bool:
        """
        移动到指定坐标

        Args:
            x, y, z: 位置坐标
            rx, ry, rz: 旋转角度
            wait: 是否等待运动完成

        Returns:
            是否成功
        """
        # 检查工作空间限制
        if not self._check_workspace_limits(x, y, z):
            print(f"超出工作空间限制: ({x}, {y}, {z})")
            return False

        # 构建G代码命令（根据实际机械臂协议调整）
        command = f"G0 X{x} Y{y} Z{z} A{rx} B{ry} C{rz} F{self.speed}"

        success = self.send_command(command)

        if success and wait:
            time.sleep(2)  # 等待运动完成（实际应该读取机械臂状态）

        return success

    def _check_workspace_limits(self, x: float, y: float, z: float) -> bool:
        """
        检查坐标是否在工作空间范围内

        Args:
            x, y, z: 坐标值

        Returns:
            是否在范围内
        """
        limits = self.safety_config.get('workspace_limits', {})

        x_min = limits.get('x_min', -300)
        x_max = limits.get('x_max', 300)
        y_min = limits.get('y_min', -200)
        y_max = limits.get('y_max', 200)
        z_min = limits.get('z_min', 0)
        z_max = limits.get('z_max', 300)

        if not (x_min <= x <= x_max):
            return False
        if not (y_min <= y <= y_max):
            return False
        if not (z_min <= z <= z_max):
            return False

        return True

    def open_gripper(self) -> bool:
        """
        打开夹爪/吸盘

        Returns:
            是否成功
        """
        command = f"M3 S{self.gripper_open_value}"
        success = self.send_command(command)

        if success:
            time.sleep(self.release_delay)

        return success

    def close_gripper(self) -> bool:
        """
        关闭夹爪/吸盘（抓取）

        Returns:
            是否成功
        """
        command = f"M3 S{self.gripper_close_value}"
        success = self.send_command(command)

        if success:
            time.sleep(self.grip_delay)

        return success

    def pick_card(self) -> bool:
        """
        从卡堆抓取卡片

        Returns:
            是否成功
        """
        print("开始抓取卡片...")

        # 1. 移动到卡堆上方
        if not self.move_to_position(Position.CARD_PILE):
            print("移动到卡堆位置失败")
            return False

        # 2. 打开夹爪
        if not self.open_gripper():
            print("打开夹爪失败")
            return False

        # 3. 下降到抓取位置（在Z轴上下降）
        # 这里简化处理，实际应该根据配置调整
        time.sleep(0.5)

        # 4. 关闭夹爪抓取
        if not self.close_gripper():
            print("关闭夹爪失败")
            return False

        # 5. 抬升
        time.sleep(0.5)

        print("卡片抓取成功")
        return True

    def place_card(self, success: bool = True) -> bool:
        """
        放置卡片到指定位置

        Args:
            success: True放到成功区，False放到失败区

        Returns:
            是否成功
        """
        position = Position.SUCCESS if success else Position.FAILED
        print(f"放置卡片到{'成功区' if success else '失败区'}...")

        # 1. 移动到目标位置
        if not self.move_to_position(position):
            print(f"移动到{'成功' if success else '失败'}位置失败")
            return False

        # 2. 下降
        time.sleep(0.5)

        # 3. 打开夹爪释放卡片
        if not self.open_gripper():
            print("打开夹爪失败")
            return False

        # 4. 抬升
        time.sleep(0.5)

        print("卡片放置成功")
        return True

    def move_to_scan_position(self) -> bool:
        """
        移动到扫描位置

        Returns:
            是否成功
        """
        print("移动到扫描位置...")
        return self.move_to_position(Position.SCAN)

    def home(self) -> bool:
        """
        回到初始位置

        Returns:
            是否成功
        """
        print("回到初始位置...")
        success = self.move_to_position(Position.HOME)

        if success:
            self.current_position = Position.HOME

        return success

    def emergency_stop(self):
        """紧急停止"""
        print("紧急停止！")
        if self.simulation_mode:
            return

        self.send_command("M112")  # G代码紧急停止命令

    def execute_card_sorting_cycle(self, recognition_success: bool) -> bool:
        """
        执行完整的卡片分拣循环

        Args:
            recognition_success: 识别是否成功

        Returns:
            是否成功完成循环
        """
        # 1. 抓取卡片
        if not self.pick_card():
            return False

        # 2. 移动到扫描位置
        if not self.move_to_scan_position():
            return False

        # 3. 等待扫描识别（由外部调用者完成）
        # ...

        # 4. 放置卡片
        if not self.place_card(success=recognition_success):
            return False

        # 5. 回到初始位置
        if not self.home():
            return False

        return True

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.home()  # 回到初始位置
        self.disconnect()

    def __del__(self):
        """析构函数"""
        self.disconnect()


def create_robot_arm_from_config(config: dict) -> RobotArm:
    """
    从配置创建机械臂实例

    Args:
        config: 完整配置字典

    Returns:
        RobotArm实例
    """
    robot_config = config.get('robot_arm', {})
    debug_config = config.get('debug', {})

    return RobotArm(
        port=robot_config.get('port', '/dev/ttyUSB0'),
        baudrate=robot_config.get('baudrate', 115200),
        timeout=robot_config.get('timeout', 1.0),
        positions=robot_config.get('positions', {}),
        motion_config=robot_config.get('motion', {}),
        safety_config=robot_config.get('safety', {}),
        simulation_mode=debug_config.get('simulation_mode', False)
    )


if __name__ == "__main__":
    # 测试代码（仿真模式）
    print("测试机械臂模块（仿真模式）...")

    positions = {
        'home': {'x': 0, 'y': 150, 'z': 200, 'rx': 0, 'ry': 0, 'rz': 0},
        'card_pile': {'x': 200, 'y': 0, 'z': 50, 'rx': 0, 'ry': 90, 'rz': 0},
        'scan_position': {'x': 0, 'y': -150, 'z': 80, 'rx': 0, 'ry': 0, 'rz': 0},
        'success_pile': {'x': -200, 'y': 0, 'z': 50, 'rx': 0, 'ry': 90, 'rz': 0},
        'failed_pile': {'x': -200, 'y': 100, 'z': 50, 'rx': 0, 'ry': 90, 'rz': 0}
    }

    with RobotArm(positions=positions, simulation_mode=True) as robot:
        print("机械臂连接成功")

        # 测试运动
        robot.home()
        robot.pick_card()
        robot.move_to_scan_position()
        robot.place_card(success=True)
        robot.home()

    print("测试完成")
