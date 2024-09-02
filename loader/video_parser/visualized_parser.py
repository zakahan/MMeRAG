import os
import cv2
from typing import List, Any, Dict
from rapidocr_onnxruntime import RapidOCR
# import easyocr
from loader.video_parser.scenes_detect import calculate_histogram, compare_histograms


class VisualizedParser:

    def __init__(
            self,
            space_second: int = 10,
            his_threshold: float = 0.4,
            sample_plan: str = 'half_change'
    ):
        '''
        现在的大致思路：
        先选出视频应该挑选的截图，
        对每张截图进行ocr，得到截图文本（如果没有就存个空字符串，如果有就存）
        然后截图和ocr的文本，时间片段，组合在一起作为一个集合保存到临时文件夹
        :param space_second:
        :param his_threshold:
        '''
        self.space = space_second
        self.his_threshold = his_threshold
        self.ocr_engine = RapidOCR()
        self.sample_plan = sample_plan
        # 再绑定一个ocr
        pass

    def ocr(self, image_path: str) -> str:
        r_list = []
        result, _ = self.ocr_engine(image_path)
        if result is None:
            return ' '
        for r in result:
            r_list.append(r[1])
            pass
        return ' '.join(r_list)

    def video_shot(self, input_video: str, save_dir: str) -> List[Dict[str, Any]]:
        # 这个是对标audio_split的，相当于是一个切割器
        cap = cv2.VideoCapture(input_video)
        if not cap.isOpened():
            raise Exception("Error opening video_parser file")
        frames_list = []
        # 检测画面变化帧数
        frame_shots = self.detect_scenes(cap=cap)
        video_fps = cap.get(cv2.CAP_PROP_FPS)

        for frame_ranges in frame_shots:
            # 得到待抽取帧
            interval_frames_range = self.sample_frame(frame_ranges, video_fps, )
            frames_list.extend(interval_frames_range)

        # 从视频中提取截图，并保存
        res_list = []
        for frame_number in frames_list:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
            # 读取一帧
            ret, frame = cap.read()
            # 检查是否成功读取帧
            if not ret:
                print(f"Error: Could not read frame {frame_number}.")
                continue
            save_path = os.path.join(save_dir, f"frame_{frame_number}.jpg")
            cv2.imwrite(save_path, frame)
            res_list.append(
                {
                    'shot_time': frame_number / video_fps * 1000,
                    'save_path': save_path
                })

        cap.release()
        return res_list

    def sample_frame(self, frame_range: List[int], fps: float) -> List[int]:
        # ['only_change', 'half_change', 'intervals']
        start_frame, end_frame = frame_range
        if self.sample_plan == 'only_change':
            return [start_frame]

            pass
        elif self.sample_plan == 'half_change':
            sample_set =  {start_frame, int((end_frame+start_frame) / 2)}
            return list(sample_set)

        elif self.sample_plan == 'intervals':
            interval_frames = []
            for i in range(start_frame, end_frame, int(self.space * fps)):
                interval_frames.append(i)
            return interval_frames

        else:
            raise Exception('sample_frame的参数sample_plan得到了一个错误的参数.')

    def detect_scenes(self, cap: cv2.VideoCapture) -> List[List]:

        prev_hist = None
        scene_changes = []
        frame_index = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            current_hist = calculate_histogram(frame)
            if prev_hist is not None:
                diff = compare_histograms(prev_hist, current_hist)
                if diff > self.his_threshold:
                    scene_changes.append(frame_index)
            prev_hist = current_hist
            frame_index += 1

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 获取视频的总帧数

        # 改成区间形式
        frame_shots = []
        frame_start = 0
        for i in range(0, len(scene_changes)):
            # 帧数转为区间
            frame_shots.append([frame_start, scene_changes[i] - 1])
            frame_start = scene_changes[i]
            pass
        # 最后的
        frame_shots.append([frame_start, total_frames])

        return frame_shots


if __name__ == '__main__':
    vparser = VisualizedParser()
    r = vparser.video_shot(
        input_video=r'E:\MyScripts\Indie\MMeRAG\DataSet\【中文字幕】YOASOBI不插电演唱会Acoustic Session小型现场たぶん & あの夢をなぞって【蓝光】@姐夫日剧字幕组.mp4',
        save_dir=r'C:\MyScripts\Indie\MMeRAG\kb\tmp\test'
    )
    print(r)
