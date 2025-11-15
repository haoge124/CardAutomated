# 快速入门指南

## 第一步：安装依赖

### 1. 安装系统依赖（Ubuntu/Debian）

```bash
# 更新软件包列表
sudo apt-get update

# 安装 Python 和基础工具
sudo apt-get install -y python3-pip python3-dev

# 安装 Tesseract OCR
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng

# 安装 OpenCV 依赖
sudo apt-get install -y libopencv-dev python3-opencv
```

### 2. 安装 Python 依赖

```bash
cd card_sorting_robot
pip install -r requirements.txt
```

注意：首次安装 EasyOCR 时会下载模型文件，可能需要较长时间。

## 第二步：测试各个模块

### 1. 测试摄像头

```bash
python test_camera.py
```

这将：
- 检测摄像头是否可以正常打开
- 显示摄像头信息
- 保存测试图像
- 提供实时预览窗口

如果遇到问题：
- 检查 `config/settings.yaml` 中的 `camera.device_id` 设置
- 确认摄像头权限：`sudo chmod 666 /dev/video0`

### 2. 测试 OCR 识别

**使用图像测试：**
```bash
python test_ocr.py -i /path/to/card_image.jpg
```

**使用摄像头实时测试：**
```bash
python test_ocr.py -c
```

按 'c' 键进行识别，按 'q' 退出。

### 3. 测试数据库

```bash
# 查看统计信息
python database_tool.py stats

# 查看最近的记录
python database_tool.py recent -n 10

# 备份数据库
python database_tool.py backup
```

## 第三步：配置参数

### 1. 编辑配置文件

```bash
nano config/settings.yaml
```

### 2. 重要配置项

#### 摄像头配置
```yaml
camera:
  device_id: 0  # 根据实际情况修改
  resolution:
    width: 1920
    height: 1080
```

#### OCR 配置
```yaml
ocr:
  engine: "easyocr"  # 或 "tesseract"
  confidence_threshold: 0.6  # 根据实际识别率调整
  roi:  # 卡片番号所在区域（需要根据实际卡片调整）
    x: 0.6      # 左上角 X 坐标（0-1）
    y: 0.85     # 左上角 Y 坐标（0-1）
    width: 0.35
    height: 0.12
```

#### 机械臂配置
```yaml
robot_arm:
  port: "/dev/ttyUSB0"  # 根据实际串口修改
  baudrate: 115200
```

## 第四步：标定机械臂位置

### 1. 启用仿真模式进行测试

修改 `config/settings.yaml`：
```yaml
debug:
  simulation_mode: true
```

### 2. 运行仿真测试

```bash
python main.py --simulation -n 1
```

### 3. 标定实际位置

使用机械臂控制软件或示教器，标定以下位置：

1. **HOME（初始位置）**: 待机位置
2. **CARD_PILE（卡堆位置）**: 抓取卡片的位置
3. **SCAN_POSITION（扫描位置）**: 摄像头下方
4. **SUCCESS_PILE（成功区）**: 识别成功的卡片放置位置
5. **FAILED_PILE（失败区）**: 识别失败的卡片放置位置

将坐标填入 `config/settings.yaml` 的 `robot_arm.positions` 部分。

## 第五步：ROI 区域调整

### 1. 拍摄测试图像

```bash
python test_camera.py
```

保存一张清晰的卡片图像。

### 2. 使用 ROI 测试工具

```bash
python test_ocr.py -i data/images/test_camera_YYYYMMDD_HHMMSS_ffffff.jpg
```

程序会：
- 显示原始图像
- 显示提取的 ROI 区域
- 显示预处理后的图像
- 输出识别结果

### 3. 调整 ROI 参数

根据显示的 ROI 区域，调整 `config/settings.yaml` 中的 `ocr.roi` 参数，直到 ROI 准确框选卡片番号区域。

参数说明：
- `x`: ROI 左上角 X 坐标（相对值，0-1）
- `y`: ROI 左上角 Y 坐标（相对值，0-1）
- `width`: ROI 宽度（相对值，0-1）
- `height`: ROI 高度（相对值，0-1）

## 第六步：正式运行

### 1. 仿真模式运行（不连接机械臂）

```bash
python main.py --simulation -n 10
```

这将处理 10 张卡片，但不实际控制机械臂。

### 2. 实际运行

```bash
# 禁用仿真模式
# 在 config/settings.yaml 中设置：
# debug:
#   simulation_mode: false

# 运行系统
python main.py
```

### 3. 其他运行选项

```bash
# 处理指定数量的卡片
python main.py -n 100

# 使用自定义配置文件
python main.py -c /path/to/config.yaml

# 启用调试模式
python main.py --debug
```

## 故障排除

### 摄像头问题

**问题：无法打开摄像头**
```bash
# 检查摄像头设备
ls /dev/video*

# 查看设备信息
v4l2-ctl --list-devices

# 修改权限
sudo chmod 666 /dev/video0
```

### OCR 识别率低

1. **调整光线**：确保照明充足且均匀
2. **调整摄像头位置**：保持垂直拍摄，避免倾斜
3. **调整 ROI 区域**：确保准确框选番号
4. **降低置信度阈值**：在 `config/settings.yaml` 中调整 `ocr.confidence_threshold`
5. **尝试不同引擎**：EasyOCR 识别率通常高于 Tesseract

### 机械臂问题

**问题：无法连接机械臂**
```bash
# 检查串口设备
ls /dev/ttyUSB* /dev/ttyACM*

# 查看串口权限
ls -l /dev/ttyUSB0

# 添加用户到 dialout 组
sudo usermod -a -G dialout $USER

# 重新登录后生效
```

## 数据库管理

### 查看统计信息

```bash
python database_tool.py stats
```

### 查看最近记录

```bash
python database_tool.py recent -n 20
```

### 搜索卡片

```bash
# 按番号搜索
python database_tool.py search -k "ABC-12345"

# 按日期搜索
python database_tool.py search -s "2024-01-01" -e "2024-12-31"

# 按置信度搜索
python database_tool.py search -c 0.8
```

### 导出数据

```bash
python database_tool.py export -o cards_export.csv
```

### 备份数据库

```bash
python database_tool.py backup
```

## 性能优化建议

### 提高识别速度

1. 使用 Tesseract 代替 EasyOCR
2. 减少 `camera.fps` 和多帧采集数量
3. 降低图像分辨率（在 `camera.resolution` 中设置）

### 提高识别准确率

1. 使用 EasyOCR 引擎
2. 优化光线条件
3. 精确调整 ROI 区域
4. 增加图像预处理步骤

### 提高运动速度

1. 增加 `robot_arm.motion.speed` 参数
2. 优化位置坐标，减少移动距离
3. 减少 `grip_delay` 和 `release_delay`

## 安全提示

⚠️ **运行前必读**：

1. 首次运行使用仿真模式
2. 确保工作空间内无障碍物
3. 设置合理的工作空间限制
4. 保持紧急停止按钮可触及
5. 运行中不要触碰机械臂
6. 定期检查机械连接

## 获取帮助

查看完整文档：
```bash
cat README.md
```

查看命令行帮助：
```bash
python main.py --help
python database_tool.py --help
```

## 下一步

- 优化 OCR 识别准确率
- 标定机械臂精确位置
- 调整运动速度和轨迹
- 根据实际卡片调整番号正则表达式
- 设置定期数据库备份
