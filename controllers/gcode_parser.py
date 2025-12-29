"""
VERICOM DLP 3D Printer - G-code Parser
ZIP 파일 내 run.gcode에서 프린트 파라미터 추출
"""

import os
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
    estimatedPrintTime: float = 0.0  # 초 단위

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
        'estimatedPrintTime': r';estimatedPrintTime:([\d.]+)',
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
                namelist = z.namelist()

                # PNG 파일 개수 카운트 (레이어 수)
                # 썸네일 제외, 숫자 포함된 PNG만 카운트
                png_files = []
                thumbnail_names = ['preview_cropping.png', 'preview.png', 'thumbnail.png']

                for name in namelist:
                    if not name.lower().endswith('.png'):
                        continue

                    filename = os.path.basename(name)

                    # 썸네일 제외
                    if filename.lower() in [t.lower() for t in thumbnail_names]:
                        continue

                    # 숫자가 포함된 PNG 파일 (1.png, 001.png, layer_1.png 등)
                    if re.search(r'\d+', filename):
                        png_files.append(name)

                print(f"[Parser] ZIP 내 파일 목록: {namelist[:10]}...")
                print(f"[Parser] 레이어 이미지 후보: {png_files[:5]}...")

                if png_files:
                    params.totalLayer = len(png_files)
                    print(f"[Parser] PNG 파일 발견: {len(png_files)}개")

                # run.gcode 파일 찾기
                gcode_file = None
                for name in namelist:
                    if name.lower() == 'run.gcode':
                        gcode_file = name
                        break

                if gcode_file:
                    content = z.read(gcode_file).decode('utf-8', errors='ignore')
                    gcode_params = GCodeParser.parse_gcode_content(content)

                    # run.gcode에서 추출한 값으로 업데이트 (totalLayer는 PNG 카운트 우선)
                    png_count = params.totalLayer
                    params = gcode_params
                    if png_count > 0:
                        params.totalLayer = png_count  # PNG 카운트 우선

                    print(f"[Parser] run.gcode 파싱 완료: {zip_path}")
                else:
                    print(f"[Parser] run.gcode 파일 없음: {zip_path}")

        except zipfile.BadZipFile:
            print(f"[Parser] 잘못된 ZIP 파일: {zip_path}")
        except Exception as e:
            print(f"[Parser] 파싱 오류: {e}")

        print(f"[Parser] 최종 totalLayer: {params.totalLayer}")
        return params

    # 썸네일 파일명 (제외 대상)
    THUMBNAIL_NAMES = ['preview_cropping.png', 'preview.png', 'thumbnail.png']

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
                    if not name.lower().endswith('.png'):
                        continue

                    # 파일명만 추출
                    filename = os.path.basename(name)

                    # 썸네일 제외
                    if filename.lower() in [t.lower() for t in GCodeParser.THUMBNAIL_NAMES]:
                        continue

                    # 파일명에 숫자가 포함되어 있으면 레이어 이미지
                    if re.search(r'\d+', filename):
                        images.append(name)

        except Exception as e:
            print(f"[Parser] 이미지 목록 추출 오류: {e}")

        # 숫자 기준 정렬 (파일명에서 숫자 추출)
        def sort_key(name):
            filename = os.path.basename(name)
            match = re.search(r'(\d+)', filename)
            return int(match.group(1)) if match else 0

        images.sort(key=sort_key)
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
                # 이미지 목록 가져와서 인덱스로 접근 (참고 파일 방식)
                images = GCodeParser.get_layer_images(zip_path)

                if 0 <= layer_index < len(images):
                    image_name = images[layer_index]
                    print(f"[Parser] 레이어 {layer_index} 이미지: {image_name}")
                    return z.read(image_name)
                else:
                    print(f"[Parser] 레이어 인덱스 범위 초과: {layer_index} (총 {len(images)}개)")

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


@dataclass
class ZipValidationResult:
    """ZIP 파일 검증 결과"""
    is_valid: bool = False
    error_message: str = ""


def validate_zip_file(zip_path: str) -> ZipValidationResult:
    """
    ZIP 파일 유효성 검증

    검증 조건:
    1. run.gcode 파일 존재
    2. run.gcode 내용에 필수 머신 설정 일치
    3. preview_cropping.png, preview.png 존재
    4. 숫자.png 파일들이 연속 (중간에 빠지면 손상)

    Args:
        zip_path: ZIP 파일 경로

    Returns:
        ZipValidationResult 객체
    """
    # 필수 머신 설정
    REQUIRED_MACHINE_SETTINGS = [
        ";resolutionX:1920",
        ";resolutionY:1080",
        ";machineX:124.8",
        ";machineY:70.2",
        ";machineZ:80",
    ]

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            namelist = z.namelist()

            # 1. run.gcode 파일 존재 확인
            gcode_file = None
            for name in namelist:
                if name.lower() == 'run.gcode':
                    gcode_file = name
                    break

            if not gcode_file:
                return ZipValidationResult(False, "run.gcode 파일이 없습니다")

            # 2. run.gcode 내용에 필수 머신 설정 확인
            content = z.read(gcode_file).decode('utf-8', errors='ignore')

            for setting in REQUIRED_MACHINE_SETTINGS:
                if setting not in content:
                    return ZipValidationResult(False, "지원하지 않는 프린터 파일입니다")

            # 3. preview_cropping.png, preview.png 존재 확인
            namelist_lower = [name.lower() for name in namelist]
            if 'preview_cropping.png' not in namelist_lower:
                return ZipValidationResult(False, "미리보기 이미지가 없습니다")
            if 'preview.png' not in namelist_lower:
                return ZipValidationResult(False, "미리보기 이미지가 없습니다")

            # 4. 숫자.png 파일들 연속성 확인
            layer_numbers = []
            for name in namelist:
                filename = os.path.basename(name).lower()
                # 숫자.png 패턴 (예: 1.png, 2.png, 001.png)
                match = re.match(r'^(\d+)\.png$', filename)
                if match:
                    layer_numbers.append(int(match.group(1)))

            if not layer_numbers:
                return ZipValidationResult(False, "레이어 이미지가 손상되었습니다")

            # 정렬 후 연속성 확인
            layer_numbers.sort()
            expected_start = layer_numbers[0]
            for i, num in enumerate(layer_numbers):
                if num != expected_start + i:
                    return ZipValidationResult(False, "레이어 이미지가 손상되었습니다")

            # 모든 검증 통과
            return ZipValidationResult(True, "")

    except zipfile.BadZipFile:
        return ZipValidationResult(False, "ZIP 파일이 손상되었습니다")
    except Exception as e:
        print(f"[Parser] ZIP 검증 오류: {e}")
        return ZipValidationResult(False, "ZIP 파일을 읽을 수 없습니다")


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
