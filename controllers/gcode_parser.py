"""
VERICOM DLP 3D Printer - G-code Parser
ZIP 파일 내 run.gcode에서 프린트 파라미터 추출
"""

import re
import zipfile
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class PrintParameters:
    """프린트 파라미터"""
    # 레이어 정보
    totalLayer: int = 0
    layerHeight: float = 0.05

    # 바닥 레이어
    bottomLayerCount: int = 8
    bottomLayerExposureTime: float = 50.0
    bottomLayerLiftHeight: float = 5.0
    bottomLayerLiftSpeed: int = 65

    # 일반 레이어
    normalExposureTime: float = 6.0
    normalLayerLiftHeight: float = 5.0
    normalLayerLiftSpeed: int = 65
    normalDropSpeed: int = 150

    # 블레이드 설정
    blade_speed: int = 1500

    # 빌드 정보
    resolutionX: int = 1440
    resolutionY: int = 2560

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GCodeParser:
    """
    G-code 파서 클래스

    ZIP 파일 내 run.gcode 분석하여 프린트 파라미터 추출
    """

    # G-code 주석에서 파라미터 추출용 정규식 패턴
    PATTERNS = {
        'totalLayer': r';totalLayer:(\d+)',
        'layerHeight': r';layerHeight:([\d.]+)',
        'bottomLayerCount': r';bottomLayerCount:(\d+)',
        'bottomLayerExposureTime': r';bottomLayerExposureTime:([\d.]+)',
        'bottomLayerLiftHeight': r';bottomLayerLiftHeight:([\d.]+)',
        'bottomLayerLiftSpeed': r';bottomLayerLiftSpeed:([\d.]+)',
        'normalExposureTime': r';normalExposureTime:([\d.]+)',
        'normalLayerLiftHeight': r';normalLayerLiftHeight:([\d.]+)',
        'normalLayerLiftSpeed': r';normalLayerLiftSpeed:([\d.]+)',
        'normalDropSpeed': r';normalDropSpeed:([\d.]+)',
        'resolutionX': r';resolutionX:(\d+)',
        'resolutionY': r';resolutionY:(\d+)',
    }

    # 블레이드 속도 추출용 (G0 X... F{speed})
    BLADE_SPEED_PATTERN = r'G0\s+X[\d.]+\s+F(\d+)'

    @staticmethod
    def parse_gcode_content(content: str) -> PrintParameters:
        """
        G-code 내용에서 파라미터 추출

        Args:
            content: run.gcode 파일 내용

        Returns:
            PrintParameters 객체
        """
        params = PrintParameters()

        # 각 패턴으로 파라미터 추출
        for param_name, pattern in GCodeParser.PATTERNS.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1)

                # 타입에 맞게 변환
                current_value = getattr(params, param_name)
                if isinstance(current_value, int):
                    setattr(params, param_name, int(float(value)))
                elif isinstance(current_value, float):
                    setattr(params, param_name, float(value))

        # 블레이드 속도 추출 (G0 X... F{speed} 명령에서)
        blade_match = re.search(GCodeParser.BLADE_SPEED_PATTERN, content)
        if blade_match:
            params.blade_speed = int(blade_match.group(1))

        return params

    @staticmethod
    def parse_zip_file(zip_path: str) -> PrintParameters:
        """
        ZIP 파일에서 프린트 파라미터 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            PrintParameters 객체
        """
        params = PrintParameters()

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # run.gcode 파일 찾기
                gcode_file = None
                for name in z.namelist():
                    if name.lower() == 'run.gcode':
                        gcode_file = name
                        break

                if gcode_file:
                    content = z.read(gcode_file).decode('utf-8', errors='ignore')
                    params = GCodeParser.parse_gcode_content(content)
                    print(f"[Parser] run.gcode 파싱 완료: {zip_path}")
                else:
                    print(f"[Parser] run.gcode 파일 없음: {zip_path}")

        except zipfile.BadZipFile:
            print(f"[Parser] 잘못된 ZIP 파일: {zip_path}")
        except Exception as e:
            print(f"[Parser] 파싱 오류: {e}")

        return params

    @staticmethod
    def get_layer_images(zip_path: str) -> list:
        """
        ZIP 파일에서 레이어 이미지 목록 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            레이어 이미지 파일명 리스트 (정렬됨)
        """
        images = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for name in z.namelist():
                    # 레이어 이미지 패턴: 숫자.png (예: 0001.png, 0002.png)
                    if re.match(r'^\d+\.png$', name):
                        images.append(name)
        except Exception as e:
            print(f"[Parser] 이미지 목록 추출 오류: {e}")

        # 숫자 순으로 정렬
        images.sort(key=lambda x: int(x.replace('.png', '')))
        return images

    @staticmethod
    def get_preview_image(zip_path: str) -> Optional[bytes]:
        """
        ZIP 파일에서 미리보기 이미지 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            이미지 바이트 데이터 또는 None
        """
        preview_names = ['preview_cropping.png', 'preview.png', 'thumbnail.png']

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                namelist = z.namelist()

                for preview_name in preview_names:
                    if preview_name in namelist:
                        return z.read(preview_name)

                # 정확한 이름이 없으면 preview가 포함된 파일 찾기
                for name in namelist:
                    if 'preview' in name.lower() and name.endswith('.png'):
                        return z.read(name)

        except Exception as e:
            print(f"[Parser] 미리보기 추출 오류: {e}")

        return None

    @staticmethod
    def get_layer_image(zip_path: str, layer_index: int) -> Optional[bytes]:
        """
        특정 레이어 이미지 추출

        Args:
            zip_path: ZIP 파일 경로
            layer_index: 레이어 인덱스 (0부터 시작)

        Returns:
            이미지 바이트 데이터 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # 다양한 파일명 형식 시도
                patterns = [
                    f"{layer_index:04d}.png",  # 0001.png
                    f"{layer_index:05d}.png",  # 00001.png
                    f"{layer_index}.png",       # 1.png
                ]

                namelist = z.namelist()
                for pattern in patterns:
                    if pattern in namelist:
                        return z.read(pattern)

        except Exception as e:
            print(f"[Parser] 레이어 이미지 추출 오류: {e}")

        return None


def extract_print_parameters(zip_path: str) -> Dict[str, Any]:
    """
    편의 함수: ZIP 파일에서 프린트 파라미터 추출 (딕셔너리 반환)

    Args:
        zip_path: ZIP 파일 경로

    Returns:
        파라미터 딕셔너리
    """
    params = GCodeParser.parse_zip_file(zip_path)
    return params.to_dict()


# 테스트용
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        zip_path = sys.argv[1]

        # 파라미터 추출
        params = extract_print_parameters(zip_path)
        print("\n프린트 파라미터:")
        for key, value in params.items():
            print(f"  {key}: {value}")

        # 이미지 목록
        images = GCodeParser.get_layer_images(zip_path)
        print(f"\n레이어 이미지: {len(images)}개")
        if images:
            print(f"  첫 번째: {images[0]}")
            print(f"  마지막: {images[-1]}")
    else:
        print("사용법: python gcode_parser.py <zip_file>")
