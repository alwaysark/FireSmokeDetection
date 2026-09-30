# -*coding=utf-8

import os
import threading
import time
from typing import Union

import cv2
import numpy


class YOLOv5(object):
    """使用yolo的.pt格式模型转换为.onnx格式模型进行目标检测"""
    # 定义输入类型表
    input_types_table = {'tensor(float)': numpy.float32, 'tensor(float16)': numpy.float16}

    def __init__(self, **kwargs):
        # 初始化配置
        self.initConfig(**kwargs)

    def initModel(self, path, t: str = None) -> None:
        """
        初始化模型
        :param path: model path
        :param t: onnxruntime or cv2.dnn, default: onnxruntime
        :return:
        """
        self.t = t
        if t == 'cv2.dnn':
            # 使用cv2.dnn读取模型
            self.net = cv2.dnn.readNet(path)
            # 获取未连接的输出层名称
            self.output_names = self.net.getUnconnectedOutLayersNames()
        else:
            import onnxruntime
            # 使用onnxruntime创建推理会话
            self.net = onnxruntime.InferenceSession(path)
            # 获取模型输入
            model_inputs = self.net.get_inputs()
            self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]
            self.input_types = [model_inputs[i].type for i in range(len(model_inputs))]
            # 获取模型输出
            model_outputs = self.net.get_outputs()
            self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]
        # 检查是否有后处理步骤
        self.has_postprocess = 'score' in self.output_names

    def initConfig(self, input_width=640, input_height=640, conf_thres=0.5, iou_thres=0.5, draw_box=True,
                   thickness=2, class_names: Union[tuple, list] = None, box_color=(255, 0, 0),
                   txt_color=(0, 255, 255), with_pos=False,
                   **kwargs) -> None:
        """
        初始化模型配置
        """
        assert 0 < conf_thres <= 1 and 0 < iou_thres <= 1
        self.input_width = input_width  # 输入图片宽
        self.input_height = input_height  # 输入图片高
        self.conf_threshold = conf_thres  # 置信度
        self.iou_threshold = iou_thres  # IOU
        self.draw_box = draw_box  # 是否画锚框
        self.thickness = thickness  # 锚框宽度
        self.class_names = class_names  # 类别
        self.box_color = box_color  # 锚框颜色 BGR
        self.txt_color = txt_color  # 文字颜色 BGR
        self.with_pos = with_pos  # 是否返回坐标
        self.__dict__.update(kwargs)

    def detect(self, image: numpy.ndarray) -> dict:
        # 进行推理
        outputs = self.__inference(image)
        # 后处理，获取边框，得分和类别ID
        boxes, scores, class_ids = self.__postProcess(outputs)
        # 格式化结果
        res_ = self.__formatResult(image, boxes, scores, class_ids)
        return res_

    def __inference(self, image: numpy.ndarray) -> list[numpy.ndarray]:
        """
        :param image: 待检测图像 RGB格式
        :return:
        """
        input_tensor = self.__prepareInput(image)
        # blob = cv2.dnn.blobFromImage(input_img, 1 / 255.0)
        # Perform inference on the image
        # 如果使用的是cv2.dnn，设置输入并进行前向传播
        if self.t == 'cv2.dnn':
            self.net.setInput(input_tensor)
            # Runs the forward pass to get output of the output layers
            outputs = self.net.forward(self.output_names)
        else:
            # 如果使用的是onnxruntime，运行模型并获取输出
            outputs = self.net.run(self.output_names, {self.input_names[0]: input_tensor})
        # print(outputs[0].shape)  # (1, 25200, 85)
        return outputs

    def __postProcess(self, outputs):
        # 如果有后处理步骤，解析处理后的输出
        if self.has_postprocess:
            res_ = self.__parseProcessedOutput(outputs)
        else:
            # 否则，处理输出数据
            res_ = self.__processOutput(outputs)
        return res_

    def __formatResult(self, image, boxes, scores, class_ids) -> dict:
        """
        格式化检测结果
        :param image: 输入图像
        :param boxes:
        :param scores:
        :param class_ids:
        :return: 检测结果
        """
        detection = {}
        if boxes is None:
            return detection
        for box, score, class_id in zip(boxes, scores, class_ids):
            x1, y1, w, h = box.astype(int)   # 框为 xywh（NMS 输出格式）
            x2, y2 = x1 + w, y1 + h
            label = self.class_names[class_id]
            if label == '_':
                continue
            # 如果标签已存在，增加数量，添加得分和位置
            if label in detection:
                detection[label]['num'] += 1
                detection[label]['score'].append(score)
                if self.with_pos: detection[label]['pos'].append((x1, y1, x2, y2))
            else:
                # 如果标签不存在，初始化数量，准确度和位置
                detection[label] = {'num': 1, 'score': [score, ], }
                if self.with_pos: detection[label].update({'pos': [(x1, y1, x2, y2), ]})
            # 如果需要画框，画出边框和标签
            if self.draw_box:
                # 创建一个标签，包含类别名和概率（百分比形式）
                label_p = f'{label} {int(score * 100)}%'
                # 计算线宽，取图像尺寸的一部分和设定的厚度中的较大值
                lw = max(round(sum(image.shape) / 2 * 0.003), self.thickness)  # line width
                # 在图像上画出边框
                cv2.rectangle(image, (x1, y1), (x2, y2), self.box_color, thickness=lw, lineType=cv2.LINE_AA)
                if label_p:
                    # 计算字体厚度，取线宽减1和1中的较大值
                    tf = max(lw - 1, 1)  # font thickness
                    # 获取标签的宽度和高度
                    w, h = cv2.getTextSize(label_p, 0, fontScale=lw / 3, thickness=tf)[0]  # text width, height
                    # 判断标签是否在边框外部
                    outside = y1 - h >= 3
                    # 计算标签的位置
                    p2 = x1 + w, y1 - h - 3 if outside else y1 + h + 3
                    # 在图像上画出填充的标签背景
                    cv2.rectangle(image, (x1, y1), p2, self.box_color, -1, cv2.LINE_AA)  # filled
                    # 在图像上画出标签
                    cv2.putText(image,
                                label_p, (x1, y1 - 2 if outside else y1 + h + 2),
                                0,
                                lw / 3,
                                self.txt_color,
                                thickness=tf,
                                lineType=cv2.LINE_AA)
        return detection

    def __prepareInput(self, image):
        # 获取图像的高和宽
        self.img_height, self.img_width = image.shape[:2]
        # 调整输入图像的大小
        input_img = cv2.resize(image, (self.input_width, self.input_height))
        # 将输入像素值缩放到0到1
        input_img = input_img / 255.0
        input_img = input_img.transpose(2, 0, 1)
        # 将输入图像转换为适当的类型
        input_tensor = input_img[numpy.newaxis, :, :, :].astype(YOLOv5.input_types_table[self.input_types[0]])
        # input_tensor = input_img[numpy.newaxis, :, :, :].astype(numpy.float32)
        return input_tensor

    def __processOutput(self, output) -> tuple:
        # 将输出压缩为一维数组
        predictions = numpy.squeeze(output[0])
        # 过滤出对象置信度分数低于阈值的预测
        obj_conf = predictions[:, 4]
        predictions = predictions[obj_conf > self.conf_threshold]
        obj_conf = obj_conf[obj_conf > self.conf_threshold]
        # 将类别置信度与边界框置信度相乘
        predictions[:, 5:] *= obj_conf[:, numpy.newaxis]
        # 获取得分
        scores = numpy.max(predictions[:, 5:], axis=1)
        # 过滤出得分低的对象
        valid_scores = scores > self.conf_threshold
        predictions = predictions[valid_scores]
        scores = scores[valid_scores]
        # 获取置信度最高的类别
        class_ids = numpy.argmax(predictions[:, 5:], axis=1)
        # 获取每个对象的边界框
        boxes = self.__extractBoxes(predictions)
        # 应用非极大值抑制来抑制弱的、重叠的边界框
        indices = numpy.array(cv2.dnn.NMSBoxes(boxes.tolist(),
                                               scores.tolist(),
                                               self.conf_threshold,
                                               self.iou_threshold)).flatten()
        # 如果有任何索引，返回对应的边界框、得分和类别ID，否则返回None
        if indices.any():
            return boxes[indices], scores[indices], class_ids[indices]
        else:
            return None, None, None

    def __parseProcessedOutput(self, outputs):
        # 从输出中提取得分
        scores = numpy.squeeze(outputs[self.output_names.index('score')])
        # 从输出中提取预测结果
        predictions = outputs[self.output_names.index('batchno_classid_x1y1x2y2')]
        # 过滤出得分低于阈值的对象
        valid_scores = scores > self.conf_threshold
        predictions = predictions[valid_scores, :]
        scores = scores[valid_scores]

        # 提取边界框和类别id
        # batch_number = predictions[:, 0]
        class_ids = predictions[:, 1]
        boxes = predictions[:, 2:]

        # 在后处理中，x,y是y,x
        boxes = boxes[:, [1, 0, 3, 2]]

        # 将边界框缩放到原始图像尺寸
        boxes = self.__rescaleBoxes(boxes)

        # xyxy → xywh，与 __extractBoxes 的输出格式保持一致
        boxes = numpy.stack([boxes[:, 0], boxes[:, 1],
                             boxes[:, 2] - boxes[:, 0], boxes[:, 3] - boxes[:, 1]], axis=1)

        return boxes, scores, class_ids

    def __extractBoxes(self, predictions):
        boxes = predictions[:, :4]   # 从预测中提取框（中心点格式 cx,cy,w,h）
        boxes = self.__rescaleBoxes(boxes)  # 将框缩放到原始图像尺寸
        # 中心格式 → xywh（左上角 + 宽高），NMSBoxes 要求此格式
        boxes_ = numpy.copy(boxes)
        boxes_[..., 0] = boxes[..., 0] - boxes[..., 2] * 0.5
        boxes_[..., 1] = boxes[..., 1] - boxes[..., 3] * 0.5
        return boxes_

    def __rescaleBoxes(self, boxes):
        """将框缩放到原始图像尺寸"""
        input_shape = numpy.array([self.input_width, self.input_height, self.input_width, self.input_height])
        boxes = numpy.divide(boxes, input_shape, dtype=numpy.float32) # 将框除以输入形状进行标准化
        boxes *= numpy.array([self.img_width, self.img_height, self.img_width, self.img_height]) # 将标准化后的框乘以原始图像尺寸进行缩放
        return boxes # 返回缩放后的框




class DataLoader(object):
    """逐帧加载图像，返回RGB格式"""
    VIDEO_TYPE = ('asf', 'avi', 'gif', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ts', 'wmv') # 定义支持的视频文件类型
    IMAGE_TYPE = ('bmp', 'dng', 'jpeg', 'jpg', 'mpo', 'png', 'tif', 'tiff', 'webp', 'pfm')  # 定义支持的图像文件类型

    def __init__(self, source: Union[int, str], flip=None, rotate=None):
        """
        :param source: 输入源
        :param flip: 翻转参数
        :param rotate: 旋转参数
        """
        self.source, *self.params = str(source).split()  # 解析输入源和参数
        self.flip = flip  # 设置翻转参数
        self.rotate = rotate  # 设置旋转参数
        self.is_webcam = self.source.isnumeric()  # 判断是否为摄像头
        self.is_video = self.source.lower().endswith(DataLoader.VIDEO_TYPE)  # 判断是否为视频文件
        self.is_image = self.source.lower().endswith(DataLoader.IMAGE_TYPE)  # 判断是否为图像文件
        self.is_screen = self.source.startswith('screen')  # 判断是否为屏幕捕捉
        assert self.is_webcam or self.is_video or self.is_image or self.is_screen, \
            f'Invalid or unsupported file format: {self.source}'  # 断言输入源有效性

        if self.is_webcam:
            self.cap = cv2.VideoCapture(int(self.source), cv2.CAP_DSHOW)  # 如果是摄像头，初始化摄像头捕获
            self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 获取帧宽度
            self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 获取帧高度
            assert self.cap.isOpened(), f'Failed to load: {self.source}'  # 确保摄像头已正确打开
        elif self.is_video or self.is_image:
            if self.is_video:
                class VideoFrameDraw(threading.Thread):
                    def __init__(self):
                        super(VideoFrameDraw, self).__init__(daemon=True)  # 创建一个守护线程
                        self.cap = cv2.VideoCapture(source)  # 初始化视频捕获
                        self.grab = self.cap.grab  # 获取视频帧
                        self.isOpened = self.cap.isOpened  # 检查视频是否打开
                        self.release = self.cap.release  # 释放视频资源
                        assert self.cap.isOpened(), f'Failed to load {source}'  # 确保视频已正确打开

                        self.fps = self.cap.get(cv2.CAP_PROP_FPS)  # 获取视频的FPS（解码线程按此节奏推进）
                        self.w, self.h = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) # 获取视频的宽度和高度
                        self.ret = self.cap.grab()  # 尝试抓取第一帧
                        if not self.ret:
                            return  # 如果抓取失败，返回
                        self.ret, self.img = self.cap.retrieve()  # 检索抓取的帧
                        if not self.ret or self.img is None:
                            return  # 如果检索失败或图像为空，返回
                        self.pause = threading.Event()  # 创建一个事件，用于暂停线程
                        self.read_frame = False  # 初始化读帧标志

                        self.start()  # 启动线程

                    def retrieve(self):
                        if not self.pause.isSet(): self.pause.set()  # 如果暂停事件未设置，则设置它
                        if self.ret:
                            self.read_frame = True  # 如果上一次抓取帧成功，则标记为已读取帧
                            return self.ret, self.img  # 返回抓取结果和图像
                        return False, None  # 如果抓取帧失败，则返回失败和None

                    def run(self) -> None:
                        while self.cap.isOpened():  # 当视频打开时持续运行
                            self.ret = self.cap.grab()  # 抓取下一帧
                            self.pause.wait()  # 等待暂停事件
                            if not self.ret:  # 如果抓取失败，则退出循环
                                break
                            time.sleep(self.fps / 1000)  # 根据视频FPS暂停一段时间
                            if not self.read_frame: # 如果未读取帧，则继续下一次循环
                                continue
                            self.ret, self.img = self.cap.retrieve()  # 检索抓取的帧
                            self.read_frame = False  # 重置读取帧标志
                            if not self.ret:  # 如果检索失败，则退出循环
                                break

                    def __del__(self):
                        self.release()  # 释放视频资源

                self.cap = VideoFrameDraw()  # 创建 VideoFrameDraw 实例
                self.w, self.h = int(self.cap.w), int(self.cap.h)  # 获取视频的宽度和高度
            else:  # 图片
                self.cap = cv2.VideoCapture(self.source)  # 创建视频捕获实例
                self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 获取视频的宽度
                self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 获取视频的高度
            assert self.cap.isOpened(), f'Failed to load: {self.source}'  # 确保视频已正确打开
        elif self.is_screen:
            import mss  # 导入 mss 模块
            screen, left, top, width, height = 0, None, None, None, None  # 默认设置为全屏捕捉 0
            if len(self.params) == 1:
                screen = int(self.params[0])  # 如果参数长度为1，设置屏幕编号
            elif len(self.params) == 4:
                left, top, width, height = (int(x) for x in self.params)  # 如果参数长度为4，设置捕捉区域的左上角坐标和宽高
            elif len(self.params) == 5:
                screen, left, top, width, height = (int(x) for x in self.params)  # 如果参数长度为5，设置屏幕编号和捕捉区域的左上角坐标和宽高
            self.sct = mss.mss()  # 创建 mss 实例

            # Parse monitor shape
            monitor = self.sct.monitors[screen]  # 获取指定屏幕的监视器信息
            top = monitor["top"] if top is None else (monitor["top"] + top)  # 计算捕捉区域的顶部位置
            left = monitor["left"] if left is None else (monitor["left"] + left)  # 计算捕捉区域的左侧位置
            width = width or monitor["width"]  # 设置捕捉区域的宽度
            height = height or monitor["height"]  # 设置捕捉区域的高度
            self.monitor = {"left": left, "top": top, "width": width, "height": height}  # 创建捕捉区域的字典

    def __next__(self) -> tuple[numpy.ndarray, str]:
        if self.is_webcam:
            ret, img = self.cap.read()  # 如果是网络摄像头，读取帧
            path = ''  # 设置路径为空字符串
        elif self.is_video or self.is_image:
            if self.is_video:
                # 视频的解码由 VideoFrameDraw 后台线程按视频帧率推进，这里只取最新一帧
                ret, img = self.cap.retrieve()
            else:
                # 图片用裸 VideoCapture：grab 推进一帧，retrieve 取出
                self.cap.grab()
                ret, img = self.cap.retrieve()
            path = self.source  # 设置路径为输入源
        elif self.is_screen:
            ret = True  # 如果是屏幕捕捉，设置返回值为True
            img = numpy.array(self.sct.grab(self.monitor))[:, :, :3]  # 捕捉屏幕区域并转换为numpy数组
            path = ''  # 设置路径为空字符串
        else:
            raise StopIteration  # 如果不是以上任何一种情况，抛出停止迭代异常

        if not ret or img is None:
            raise StopIteration  # 如果读取失败或图像为空，抛出停止迭代异常
        if self.flip is not None: img = cv2.flip(img, self.flip)  # 如果设置了翻转参数，翻转图像
        if self.rotate is not None: img = cv2.rotate(img, self.rotate)  # 如果设置了旋转参数，旋转图像
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 将图像从BGR转换为RGB格式
        return img, os.path.basename(path)  # 返回图像和路径的基本名称

    def __iter__(self):
        return self # 返回自身实例，使得类实例可以进行迭代

    def __del__(self):
        if 'cap' in self.__dict__:  # 如果实例字典中存在'cap'键
            self.cap.release()  # 释放视频捕获资源


if __name__ == '__main__':
    YOLOv5().initConfig(input_width=640,
                input_height=640,
                conf_thres=0.8,
                iou_thres=0.35,
                draw_box=True,
                thickness=2,
                class_names=['smoke','fire'],
                box_color=(255, 0, 0),
                txt_color=tuple(255 - x for x in (255, 0, 0)),
                with_pos=True,
                )