# 烟雾火焰检测系统（TinyYoloDetection）

基于 YOLOv5 ONNX 模型与 PyQt5 的桌面端烟雾/火焰实时检测工具。

本分支是原始毕业设计项目的**精简重构版**：移除了登录注册与脚本编辑器等功能，修复了多处原版缺陷，依赖从 107 个包精简到 6 个，代码按界面绑定顺序重新组织。

## 功能

- **四种输入源**：本地摄像头、视频/图片文件、屏幕捕获
- **实时检测**：检测线程独立于界面线程，画面与结果实时刷新
- **参数运行时可调**：置信度阈值、IOU 阈值、锚框开关、翻转/旋转——修改立即生效，无需重启检测
- **输出**：检测画面（带锚框与置信度标签）、检测录像（mp4）、截图、控制台日志（均可保存为文件）
- **火焰警报**：连续检出火焰时播放警报音（可开关）
- **配置持久化**：关闭时自动保存全部设置，下次启动恢复（含自动恢复上次的检测状态）
- **其他**：锚框颜色与字体调整、控制台锁定/清空、检测画面与控制台可保存

## 技术栈

- Python 3.9
- PyQt5（界面 + 多线程信号槽）
- OpenCV（视频 I/O 与图像处理）
- onnxruntime（ONNX 模型推理）
- pygame（警报音播放）
- mss（屏幕捕获）

## 运行

```bash
pip install -r requirements.txt
python app.py
```

模型与测试资源位于 `need/` 目录：模型 `need/models/m0.9.onnx`，类别 `need/m0.9.txt`（fire、smoke 两类）。

## 使用说明

1. **输入页**选择输入方式（摄像头 / 图片视频 / 屏幕），选文件源时点"..."选择文件，选好后画面区开始预览
2. 点击**开始**开始检测，**停止**停止推理（摄像头/屏幕源停止后预览画面仍在）
3. **输出页**可实时调整置信度、IOU、锚框显示、录制视频、警报开关
4. **保存路径**下自动生成截图（`ScreenShot_*`）、控制台日志（`log_*`）、检测录像（`video_*`），也可手动点按钮保存

## 项目结构

```
app.py                        程序入口
uicontroller/Main_Window.py   主窗口 + 检测线程（DetectThread）
UI/FireSmokeDetection.py      Qt Designer 生成的界面代码
utils/detect.py               DataLoader（输入源）+ YOLOv5（ONNX 推理）
utils/general.py              配置读写（config.cfg）
utils/utils.py                警报音播放
need/                         模型、类别、测试视频、警报音
```

## 相对原版的修复与变更

本项目基于 [xun-xh/yolov5-onnx-pyqt-exe](https://github.com/xun-xh/yolov5-onnx-pyqt-exe) 重构。本分支相对原版：

**移除**：登录注册系统、脚本编辑器、107 个依赖中的 101 个

**修复**：
- 主窗口依赖垃圾回收时机存活的隐患（入口重构，窗口与事件循环同作用域）
- NMS 输入框格式错误（xyxy → NMS 要求的 xywh）
- 模型-类别文件自动配对丢失点号的问题（splitext）
- saveConfig 悬空引用、参数热更新等若干缺陷

**重组**：函数按界面绑定顺序排列并标注触发来源；requirements 精简至运行必需

## 已知限制

- CPU 推理速度有限（数 FPS 到十几 FPS，视机型），可换 GPU 版 onnxruntime 提速
- 文件路径包含空格时无法打开（输入源按空格解析，历史设计）

## 分支说明

- `master`：原始毕业设计版本（含登录注册），仅存档
- `TinyYoloDetection`：本分支，精简重构版（当前主线）
