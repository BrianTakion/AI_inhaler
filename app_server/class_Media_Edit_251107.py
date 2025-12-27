import cv2
import os
import numpy as np
from pathlib import Path

class MediaEdit:
    def __init__(self):
        pass
    

    def _open_video(self, video_path):
        """비디오 파일을 열고, 비디오 캡처 객체를 반환합니다."""
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            print("비디오를 열 수 없습니다.")
            return None
        return capture
    
    
    # 파일명에 한글 포함되었을 때
    def cv2_imread(self, image_path):  
        image_path_temp = 'temporary_cv2_imread'
        os.replace(image_path, image_path_temp)
        image = cv2.imread(image_path_temp)  # 파일에 한글명 포함되어 있을 때 처리 못 함
        os.replace(image_path_temp, image_path)
        return image
 

    # 파일명에 한글 포함되었을 때
    def cv2_imwrite(self, output_file, output_image):
        output_file_temp = 'temporary_cv2_imwrite.png'
        cv2.imwrite(output_file_temp, output_image)  # 중요: cv2.imwrite()에서는 파일명에 한글 있으면 파일로 저장안됨
        os.replace(output_file_temp, output_file)
    

    def query_videoInfo(self, video_path):
        """비디오 파일의 실행 시간, 프레임 수 및 해상도를 계산하여 반환합니다."""
        video_name = os.path.splitext(os.path.basename(video_path))[0]  # 파일명
        capture = self._open_video(video_path)
        if capture is None:
            return None, None, None, None, None, None
        
        fps = capture.get(cv2.CAP_PROP_FPS)  # 프레임 속도 (FPS)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))  # 전체 프레임 수
        play_time = round(total_frames / fps, 2)  # 총 실행 시간 (초)
        
        # 해상도 정보 추가
        video_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        capture.release()
        file_size = os.path.getsize(video_path)  # 파일 크기 (바이트 단위)

        return video_name, play_time, total_frames, video_width, video_height, file_size


    def query_imageInfo(self, image_path):
        """비디오 또는 이미지 파일의 실행 시간, 프레임 수, 해상도 및 파일 크기를 계산하여 반환합니다."""
        
        image_name = os.path.splitext(os.path.basename(image_path))[0]
    
        image = self.cv2_imread(image_path)
        if image is None:
            return None, None, None, None
        image_height, image_width, _ = image.shape
        file_size = os.path.getsize(image_path)  # 파일 크기 (바이트 단위)
        return image_name, image_width, image_height, file_size


    def extract_frames_to_video(self, option, interval, video_path, output_dir):
        """비디오를 주어진 간격으로 추출하여 output_dir에 저장합니다. 생성된 비디오 파일의 경로를 반환합니다."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        capture = self._open_video(video_path)
        if capture is None:
            return None, None, None

        fps = capture.get(cv2.CAP_PROP_FPS)  # 프레임 속도 (FPS)
        video_name = os.path.splitext(os.path.basename(video_path))[0]  # 파일명
        output_file = os.path.join(output_dir, f"{video_name}_extracted.mp4")
        out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        if option == 'time':
            interval = int(interval * fps)  # interval을 프레임 단위로 변환

        print("비디오 처리를 시작합니다.")
        count = 0
        frame_index = 0
        success, frame = capture.read()
        total_frames = 0
        while success:
            if count == frame_index * interval:
                out.write(frame)
                frame_index += 1
                total_frames += 1

            success, frame = capture.read()
            count += 1

        out.release()
        capture.release()

        # 총 재생 시간 계산
        play_time = round(total_frames / fps, 2)
        
        # 결과 출력
        print(f"{video_name} 비디오가 {option}({interval}) 간격으로 추출되어 {output_dir}에 저장되었습니다.")
        print(f"재생 시간: {play_time} 초, 총 프레임 수: {total_frames} 프레임")
        
        return output_file, play_time, total_frames

    # 핵심 함수
    def extract_frames_to_MxN_image(self, option, start, end, MxN, video_path, output_dir=None, gridSize=(1920, 1080), padSize=(10, 10)):
        """
        비디오의 지정된 구간에서 MxN 개의 프레임을 추출하여 지정된 크기의 그리드에 맞추어 하나의 PNG 이미지로 저장합니다.
        output_dir가 존재하면 출력 파일 경로를 반환하며, None이면 이미지 배열을 반환합니다.
        Args:
            option (str): 'time' 또는 'frame' 중 하나
            start (float): 시작 시간 또는 프레임 번호
            end (float): 종료 시간 또는 프레임 번호
            MxN (tuple): 프레임을 배열할 행과 열의 수
            video_path (str): 비디오 파일 경로
            output_dir (str): 출력 파일 경로 (기본값: None)
            gridSize (tuple): 그리드의 크기 (기본값: (1920, 1080))
            padSize (tuple): 그리드 간격 (기본값: (10, 10))
        Returns:
            str/array: output_dir가 존재하면 출력 파일 경로, None이면 이미지 배열을 반환
            int: 그리드의 너비
            int: 그리드의 높이
        """
        
        capture = self._open_video(video_path)
        if capture is None:
            return None, gridSize[0], gridSize[1]

        fps = capture.get(cv2.CAP_PROP_FPS)
        #total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        if option == 'time':
            start_frame = int(start * fps)
            end_frame = int(end * fps)
        elif option == 'frame':
            start_frame = start
            end_frame = end
        else:
            print("잘못된 옵션입니다. 'time' 또는 'frame'을 선택하세요.")
            capture.release()
            return None, gridSize[0], gridSize[1]
        
        #print("비디오 처리를 시작합니다.")
        num_frames = MxN[0] * MxN[1]
        frame_interval = max((end_frame - start_frame) // num_frames, 1)
        
        selected_frames = []
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for i in range(num_frames):
            capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame + i * frame_interval)
            success, frame = capture.read()
            if not success:
                print(f"프레임 {start_frame + i * frame_interval}을 읽을 수 없습니다.")
                break
            if frame is None:
                print(f"프레임 {start_frame + i * frame_interval}이 None입니다.")
                break
            selected_frames.append(frame)
        
        if len(selected_frames) != num_frames:
            print(f"선택한 프레임 수가 기대한 것보다 적습니다. (기대: {num_frames}, 실제: {len(selected_frames)})")
            capture.release()
            return None, gridSize[0], gridSize[1]
        
        # 프레임 유효성 검사
        if not selected_frames or selected_frames[0] is None:
            print("유효한 프레임이 없습니다.")
            capture.release()
            return None, gridSize[0], gridSize[1]
        
        #frame_height, frame_width = selected_frames[0].shape[:2]
        cell_width = (gridSize[0] - (MxN[1] - 1) * padSize[0]) // MxN[1]
        cell_height = (gridSize[1] - (MxN[0] - 1) * padSize[1]) // MxN[0]
        
        # 셀 크기 유효성 검사
        if cell_width <= 0 or cell_height <= 0:
            print(f"셀 크기가 유효하지 않습니다: {cell_width}x{cell_height}")
            capture.release()
            return None, gridSize[0], gridSize[1]

        output_image = np.zeros((gridSize[1], gridSize[0], 3), dtype=np.uint8)

        for idx, frame in enumerate(selected_frames):
            if frame is None:
                print(f"프레임 {idx}가 None입니다.")
                continue
                
            row = idx // MxN[1]
            col = idx % MxN[1]
            start_x = col * (cell_width + padSize[0])
            start_y = row * (cell_height + padSize[1])
            
            try:
                resized_frame = cv2.resize(frame, (cell_width, cell_height))
                output_image[start_y:start_y + cell_height, start_x:start_x + cell_width, :] = resized_frame
            except Exception as e:
                print(f"프레임 {idx} 리사이즈 중 오류 발생: {e}")
                continue

        if output_dir is not None: # 출력 파일을 생성하고 경로를 반환
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_file = os.path.join(output_dir, f"{video_name}_{start}-{end}{option}_{MxN[0]}x{MxN[1]}grid.png")
            self.cv2_imwrite(output_file, output_image)
            print(f"{output_file} 파일이 생성되었습니다. 크기: {gridSize[0]}x{gridSize[1]} px")
            capture.release()
            return output_file, gridSize[0], gridSize[1]
        else: # 출력 파일을 생성하지 않고 이미지 배열만 반환
            capture.release()
            return output_image, gridSize[0], gridSize[1]

    
    def trim_video_segment(self, option, start, end, video_path, output_dir):
        """비디오를 주어진 시작과 종료 지점에서 잘라 output_dir에 저장합니다. 생성된 비디오 파일의 경로와 재생 시간, 총 프레임 수를 반환합니다."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        capture = self._open_video(video_path)
        if capture is None:
            return None, None, None

        fps = capture.get(cv2.CAP_PROP_FPS)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_file = os.path.join(output_dir, f"{video_name}_trimmed.mp4")
        out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))

        print("비디오 처리를 시작합니다.")
        success, frame = capture.read()
        count = 0

        if option == 'time':
            start_frame = int(start * fps)
            end_frame = int(end * fps)
        elif option == 'frame':
            start_frame = start
            end_frame = end
        else:
            print("잘못된 옵션입니다. 'time' 또는 'frame'을 선택하세요.")
            out.release()
            capture.release()
            return None

        total_frames = 0
        while success and count < end_frame:
            if count >= start_frame:
                out.write(frame)
                total_frames += 1
            success, frame = capture.read()
            count += 1

        out.release()
        capture.release()

        # 자른 비디오의 재생 시간 계산
        play_time = round(total_frames / fps, 2)

        print(f"{video_name} 비디오가 {start} sec 에서 {end} sec까지 잘라서 {output_dir}에 저장되었습니다.")
        print(f"재생 시간: {play_time} 초, 총 프레임 수: {total_frames} 프레임")

        return output_file, play_time, total_frames


    def split_video_into_segments(self, option, interval, video_path, output_dir):
        """비디오를 시간 또는 프레임 간격으로 잘라서 output_dir에 저장합니다."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        capture = self._open_video(video_path)
        if capture is None:
            return None, None, None

        fps = capture.get(cv2.CAP_PROP_FPS)  # 프레임 속도 (FPS)
        video_name = os.path.splitext(os.path.basename(video_path))[0]  # 파일명
        if option == 'time':
            interval = int(interval * fps)  # interval을 프레임 단위로 변환

        print("비디오 처리를 시작합니다.")
        count = 0
        part_count = 0
        success, frame = capture.read()
        first_segment_frames = 0  # 첫 번째 세그먼트의 프레임 수를 저장
        play_time = 0  # 첫 번째 세그먼트의 재생 시간을 저장
        while success:
            output_file = os.path.join(output_dir, f"{video_name}_part_{part_count:03d}.mp4")
            out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame.shape[1], frame.shape[0]))
            part_count += 1

            segment_frame_count = 0  # 현재 세그먼트의 프레임 수를 저장
            while success:
                if option == 'time':
                    if count >= part_count * interval:
                        break
                elif option == 'frame':
                    if count >= part_count * interval:
                        break
                else:
                    print("잘못된 옵션입니다. 'time' 또는 'frame'을 선택하세요.")
                    out.release()
                    capture.release()
                    return None, None, None
                
                out.write(frame)
                segment_frame_count += 1
                count += 1
                success, frame = capture.read()

            if part_count == 1:
                # 첫 번째 세그먼트의 정보를 저장
                firstSegment_total_frames = segment_frame_count
                firstSegment_play_time = round(firstSegment_total_frames / fps, 2)

            out.release()
            print('.', end='')

        capture.release()
        num_videos = part_count  # 생성된 비디오 세그먼트의 수
        print(f"\n{video_name} 비디오가 {option}({interval}) 간격으로 {output_dir}에 저장되었습니다.")
        print(f"비디오 수: {num_videos}, 첫번째 비디오 재생 시간: {firstSegment_play_time} 초, 첫번째 비디오 총 프레임 수: {firstSegment_total_frames} 프레임")

        return num_videos, play_time, first_segment_frames
