import cv2
import numpy as np


# 选用直方图方式做场景检测的原因在于其对于镜头抖动、放大等情况的鲁棒性较好
def frames_to_time(framerate, frames):      # 毫秒级
    """将帧数转换为毫秒数"""
    milliseconds = (frames / framerate) * 1000
    return int(milliseconds)


def calculate_histogram(frame):
    # 将BGR图像转换为HSV，以便于颜色直方图的计算
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # 计算HSV颜色空间下的直方图
    hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
    # 归一化直方图
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return hist


def compare_histograms(hist1, hist2):
    # 使用Bhattacharyya距离比较两个直方图
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)



