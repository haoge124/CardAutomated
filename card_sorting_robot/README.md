# 卡片自动化识别和分拣系统

基于机械臂的游戏王卡片自动扫描、识别和分拣的 Python 自动化系统。

## 项目简介

本项目实现了一个完整的卡片自动化处理流程：
1. 使用机械臂从卡堆抓取卡片
2. 将卡片移动到摄像头下方进行扫描
3. 使用 OCR 技术识别卡片番号
4. 将识别结果保存到数据库
5. 根据识别结果将卡片分拣到成功区或失败区

## 技术栈

- **编程语言**: Python 3.11+
- **机械臂控制**: 基于 SO-ARM100 (或兼容设备)
- **图像处理**: OpenCV
- **OCR 识别**: EasyOCR / Tesseract OCR
- **数据库**: SQLite
- **硬件接口**:
  - USB 高清摄像头
  - 串口控制的机械臂
  - 吸盘或夹爪式末端执行器

## 项目结构

```
card_sorting_robot/
├── main.py                      # 主程序入口
├── config/
│   └── settings.yaml            # 配置文件
├── modules/                     # 核心功能模块
│   ├── camera.py                # 摄像头控制
│   ├── ocr_recognition.py       # OCR 识别
│   ├── database.py              # 数据库操作
│   └── robot_arm.py             # 机械臂控制
├── utils/                       # 工具模块
│   ├── image_processing.py      # 图像预处理
│   ├── logger.py                # 日志工具
│   └── config_loader.py         # 配置加载
├── data/                        # 数据目录
│   ├── images/                  # 保存卡片图片
│   ├── logs/                    # 日志文件
│   └── cards.db                 # SQLite 数据库
├── requirements.txt             # 依赖包
└── README.md                    # 说明文档
```

## 安装步骤

### 1. 系统要求

- Python 3.11 或更高版本
- Linux (推荐 Ubuntu 20.04+) 或 Windows 10+
- 至少 4GB RAM
- USB 摄像头
- 兼容的机械臂（SO-ARM100 或类似设备）

### 2. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
sudo apt-get install -y libopencv-dev python3-opencv
```

**Windows:**
- 从 [Tesseract官网](https://github.com/tesseract-ocr/tesseract) 下载并安装 Tesseract OCR
- 确保 Tesseract 添加到系统 PATH

### 3. 安装 Python 依赖

```bash
cd card_sorting_robot
pip install -r requirements.txt
```

### 4. 配置硬件

#### 摄像头配置
1. 连接 USB 摄像头
2. 查看设备 ID：
   ```bash
   ls /dev/video*  # Linux
   ```
3. 在 `config/settings.yaml` 中设置 `camera.device_id`

#### 机械臂配置
1. 连接机械臂到串口
2. 查看串口设备：
   ```bash
   ls /dev/ttyUSB*  # Linux
   ls /dev/ttyACM*
   ```
3. 在 `config/settings.yaml` 中设置 `robot_arm.port`

### 5. 配置参数

编辑 `config/settings.yaml` 文件，调整以下关键参数：

```yaml
# 摄像头参数
camera:
  device_id: 0  # 摄像头设备 ID

# OCR 参数
ocr:
  engine: "easyocr"  # 或 "tesseract"
  confidence_threshold: 0.6
  roi:  # 卡片番号区域（相对坐标）
    x: 0.6
    y: 0.85
    width: 0.35
    height: 0.12

# 机械臂位置坐标（需要根据实际情况调整）
robot_arm:
  positions:
    home: {x: 0, y: 150, z: 200, ...}
    card_pile: {x: 200, y: 0, z: 50, ...}
    # ... 其他位置
```

## 使用方法

### 基本运行

```bash
# 使用默认配置运行
python main.py

# 使用自定义配置文件
python main.py -c /path/to/config.yaml

# 仿真模式（不连接实际硬件）
python main.py --simulation

# 处理指定数量的卡片
python main.py -n 100

# 启用调试模式
python main.py --debug
```

### 命令行参数

- `-c, --config`: 指定配置文件路径
- `-d, --debug`: 启用调试模式
- `-s, --simulation`: 仿真模式（用于测试）
- `-n, --num-cards`: 要处理的卡片数量

### 单独测试各模块

```bash
# 测试摄像头
python modules/camera.py

# 测试 OCR 识别
python modules/ocr_recognition.py

# 测试数据库
python modules/database.py

# 测试机械臂（仿真模式）
python modules/robot_arm.py
```

## 工作流程

```
1. 系统初始化
   ↓
2. 连接硬件设备
   ↓
3. 机械臂回到初始位置
   ↓
4. [循环开始]
   ├─ 从卡堆抓取卡片
   ├─ 移动到扫描位置
   ├─ 摄像头拍摄图像
   ├─ 图像预处理
   ├─ OCR 识别卡片番号
   ├─ 保存结果到数据库
   ├─ 根据识别结果分拣卡片
   └─ 回到初始位置
5. [循环结束]
   ↓
6. 输出统计信息
   ↓
7. 清理资源并退出
```

## 核心功能说明

### 1. 摄像头图像采集

- 支持多帧采集选择最佳画质
- 自动对焦和曝光调整
- 保存原始和处理后的图像

### 2. 图像预处理

- 灰度转换
- 去噪处理
- 自适应阈值二值化
- ROI 区域提取
- 对比度增强

### 3. OCR 识别

- 支持 EasyOCR 和 Tesseract 两种引擎
- 多次识别取最优结果
- 置信度阈值过滤
- 正则表达式格式验证

### 4. 数据库管理

- 记录所有扫描的卡片信息
- 统计成功率和平均置信度
- 支持按日期、番号等条件查询
- 自动备份功能

### 5. 机械臂控制

- 串口通信控制
- 预设位置管理
- 工作空间安全限制
- 运动速度和加速度控制
- 夹爪/吸盘开合控制

## 配置说明

### 关键位置标定

使用机械臂前需要标定以下关键位置：

1. **HOME（初始位置）**: 待机位置
2. **CARD_PILE（卡堆位置）**: 抓取卡片的位置
3. **SCAN_POSITION（扫描位置）**: 摄像头下方
4. **SUCCESS_PILE（成功区）**: 识别成功的卡片放置位置
5. **FAILED_PILE（失败区）**: 识别失败的卡片放置位置

### ROI 区域调整

卡片番号通常位于右下角，需要根据实际情况调整 ROI 坐标：

```yaml
ocr:
  roi:
    x: 0.6      # 左上角 X 坐标（相对值 0-1）
    y: 0.85     # 左上角 Y 坐标
    width: 0.35 # 宽度
    height: 0.12 # 高度
```

### OCR 引擎选择

- **EasyOCR**: 识别率高，支持多语言，但速度较慢
- **Tesseract**: 速度快，但识别率可能略低

## 故障排除

### 摄像头无法打开

- 检查设备 ID 是否正确
- 确认摄像头权限：`sudo chmod 666 /dev/video0`
- 检查是否被其他程序占用

### 机械臂无法连接

- 检查串口设备路径
- 确认串口权限：`sudo chmod 666 /dev/ttyUSB0`
- 检查波特率设置是否匹配

### OCR 识别率低

- 调整摄像头位置和角度
- 改善光线条件
- 调整 ROI 区域
- 尝试不同的 OCR 引擎
- 降低置信度阈值

### 数据库错误

- 检查数据目录权限
- 确保磁盘空间充足
- 定期备份数据库

## 性能优化

1. **提高识别速度**
   - 使用 Tesseract 替代 EasyOCR
   - 减少多帧采集数量
   - 降低图像分辨率

2. **提高识别率**
   - 使用 EasyOCR
   - 增加多帧采集数量
   - 优化光线条件
   - 精确调整 ROI 区域

3. **提高运动速度**
   - 增加机械臂运动速度参数
   - 优化位置坐标减少移动距离
   - 减少等待延迟时间

## 安全注意事项

⚠️ **重要安全提示**：

1. 首次运行时使用仿真模式测试
2. 确保机械臂工作空间内无障碍物
3. 设置合理的工作空间限制
4. 保持紧急停止按钮可触及
5. 不要在机械臂运动时触碰
6. 定期检查机械连接是否牢固

## 开发和调试

### 调试模式

```bash
python main.py --debug --simulation
```

### 查看日志

```bash
tail -f data/logs/robot.log
```

### 数据库查询

```python
from modules.database import CardDatabase

db = CardDatabase()
stats = db.get_statistics()
print(stats)

recent_cards = db.get_recent_cards(limit=10)
for card in recent_cards:
    print(card)
```

## 贡献指南

欢迎贡献代码、报告 Bug 或提出新功能建议！

## 许可证

MIT License

## 参考资料

- [SO-ARM100 开源项目](https://github.com/TheRobotStudio/SO-ARM100)
- [OpenCV 文档](https://docs.opencv.org/)
- [EasyOCR 文档](https://github.com/JaidedAI/EasyOCR)
- [Tesseract OCR 文档](https://github.com/tesseract-ocr/tesseract)

## 联系方式

如有问题或建议，请提交 Issue。

---

**注意**: 本系统需要根据实际硬件进行参数调整和标定，首次使用建议在专业人员指导下进行。
