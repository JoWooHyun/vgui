"""
Mazic CERA DLP 3D Printer GUI - G-code Parser
run.gcode 파일에서 프린트 파라미터 및 이미지 정보 추출
"""

import os
import re
import zipfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PrintParameters:
    """프린트 파라미터 데이터 클래스"""
    
    # 레이어 정보
    total_layers: int = 0
    layer_height: float = 0.05  # mm
    
    # 노출 시간
    normal_exposure_time: float = 3.0      # 초
    bottom_exposure_time: float = 5.0      # 초
    bottom_layer_count: int = 5
    
    # 이동 파라미터
    lift_height: float = 5.0               # mm
    lift_speed: float = 60.0               # mm/min
    drop_speed: float = 150.0              # mm/min
    
    # 블레이드 속도 (내부값: mm/min)
    blade_speed: int = 1500                # mm/min (GUI 표시: 30 mm/s)
    
    # LED 파워 (내부값: 코드값)
    led_power: int = 440                   # (GUI 표시: 100%)
    
    # 추가 정보
    resin_type: str = ""
    estimated_volume: float = 0.0          # ml
    estimated_time: float = 0.0            # 분
    
    # 이미지 파일 목록
    image_files: List[str] = field(default_factory=list)


class GCodeParser:
    """G-code 및 ZIP 파일 파싱 클래스"""
    
    # 파라미터 패턴
    PARAM_PATTERNS = {
        'totalLayer': (r';totalLayer:(\d+)', int),
        'layerHeight': (r';layerHeight:([\d.]+)', float),
        'normalExposureTime': (r';normalExposureTime:([\d.]+)', float),
        'bottomLayerExposureTime': (r';bottomLayerExposureTime:([\d.]+)', float),
        'bottomLayerCount': (r';bottomLayerCount:(\d+)', int),
        'normalLayerLiftHeight': (r';normalLayerLiftHeight:([\d.]+)', float),
        'normalLayerLiftSpeed': (r';normalLayerLiftSpeed:([\d.]+)', float),
        'normalDropSpeed': (r';normalDropSpeed:([\d.]+)', float),
        'resinType': (r';resinType:(.+)', str),
        'estimatedPrintTime': (r';estimatedPrintTime:([\d.]+)', float),
        'machineX': (r';machineX:([\d.]+)', float),
        'machineY': (r';machineY:([\d.]+)', float),
        'machineZ': (r';machineZ:([\d.]+)', float),
    }
    
    # 이미지 확장자
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp')
    
    # 썸네일 파일명
    THUMBNAIL_NAMES = ['preview_cropping.png', 'preview.png', 'thumbnail.png']
    
    def __init__(self):
        """초기화"""
        pass
    
    def parse_zip_file(self, zip_path: str) -> PrintParameters:
        """ZIP 파일 파싱
        
        Args:
            zip_path: ZIP 파일 경로
            
        Returns:
            PrintParameters 객체
        """
        params = PrintParameters()
        
        if not os.path.exists(zip_path):
            print(f"[GCodeParser] 파일을 찾을 수 없음: {zip_path}")
            return params
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # run.gcode 파싱
                if 'run.gcode' in zf.namelist():
                    content = zf.read('run.gcode').decode('utf-8', errors='ignore')
                    params = self._parse_gcode_content(content)
                
                # 이미지 파일 목록 추출
                params.image_files = self._get_image_files(zf)
                
        except zipfile.BadZipFile:
            print(f"[GCodeParser] 잘못된 ZIP 파일: {zip_path}")
        except Exception as e:
            print(f"[GCodeParser] ZIP 파싱 오류: {e}")
        
        return params
    
    def _parse_gcode_content(self, content: str) -> PrintParameters:
        """G-code 내용 파싱
        
        Args:
            content: G-code 파일 내용
            
        Returns:
            PrintParameters 객체
        """
        params = PrintParameters()
        
        for param_name, (pattern, converter) in self.PARAM_PATTERNS.items():
            match = re.search(pattern, content)
            if match:
                try:
                    value = converter(match.group(1).strip())
                    
                    # 파라미터 매핑
                    if param_name == 'totalLayer':
                        params.total_layers = value
                    elif param_name == 'layerHeight':
                        params.layer_height = value
                    elif param_name == 'normalExposureTime':
                        params.normal_exposure_time = value
                    elif param_name == 'bottomLayerExposureTime':
                        params.bottom_exposure_time = value
                    elif param_name == 'bottomLayerCount':
                        params.bottom_layer_count = value
                    elif param_name == 'normalLayerLiftHeight':
                        params.lift_height = value
                    elif param_name == 'normalLayerLiftSpeed':
                        params.lift_speed = value
                    elif param_name == 'normalDropSpeed':
                        params.drop_speed = value
                    elif param_name == 'resinType':
                        params.resin_type = value
                    elif param_name == 'estimatedPrintTime':
                        params.estimated_time = value
                        
                except ValueError:
                    pass
        
        # 총 시간 계산 (없으면)
        if params.estimated_time == 0 and params.total_layers > 0:
            params.estimated_time = self._estimate_print_time(params)
        
        return params
    
    def _estimate_print_time(self, params: PrintParameters) -> float:
        """프린트 시간 추정 (분)"""
        # 바닥 레이어 시간
        bottom_time = params.bottom_layer_count * params.bottom_exposure_time
        
        # 일반 레이어 시간
        normal_layers = max(0, params.total_layers - params.bottom_layer_count)
        normal_time = normal_layers * params.normal_exposure_time
        
        # 이동 시간 (대략 레이어당 5초)
        move_time = params.total_layers * 5
        
        # 총 시간 (분)
        total_seconds = bottom_time + normal_time + move_time
        return total_seconds / 60
    
    def _get_image_files(self, zf: zipfile.ZipFile) -> List[str]:
        """ZIP 내 이미지 파일 목록 추출 (정렬됨)"""
        images = []
        
        for name in zf.namelist():
            if name.lower().endswith(self.IMAGE_EXTENSIONS):
                # 썸네일 제외
                if name.lower() not in [t.lower() for t in self.THUMBNAIL_NAMES]:
                    images.append(name)
        
        # 숫자 기준 정렬
        def sort_key(name):
            # 파일명에서 숫자 추출
            match = re.search(r'(\d+)', name)
            return int(match.group(1)) if match else 0
        
        return sorted(images, key=sort_key)
    
    def extract_thumbnail(self, zip_path: str) -> Optional[bytes]:
        """ZIP에서 썸네일 이미지 추출
        
        Args:
            zip_path: ZIP 파일 경로
            
        Returns:
            이미지 바이트 데이터 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for name in self.THUMBNAIL_NAMES:
                    if name in zf.namelist():
                        return zf.read(name)
                    
                    # 대소문자 무시 검색
                    for n in zf.namelist():
                        if n.lower() == name.lower():
                            return zf.read(n)
                            
        except Exception as e:
            print(f"[GCodeParser] 썸네일 추출 오류: {e}")
        
        return None
    
    def extract_layer_image(self, zip_path: str, layer_index: int) -> Optional[bytes]:
        """특정 레이어 이미지 추출
        
        Args:
            zip_path: ZIP 파일 경로
            layer_index: 레이어 인덱스 (0부터)
            
        Returns:
            이미지 바이트 데이터 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                images = self._get_image_files(zf)
                
                if 0 <= layer_index < len(images):
                    return zf.read(images[layer_index])
                    
        except Exception as e:
            print(f"[GCodeParser] 레이어 이미지 추출 오류: {e}")
        
        return None
    
    def get_layer_count(self, zip_path: str) -> int:
        """레이어 수 조회"""
        params = self.parse_zip_file(zip_path)
        return params.total_layers
    
    def get_image_count(self, zip_path: str) -> int:
        """이미지 파일 수 조회"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                return len(self._get_image_files(zf))
        except:
            return 0


# ==================== 단위 변환 유틸리티 ====================

def blade_speed_to_display(gcode_value: int) -> float:
    """블레이드 속도 변환: G-code(mm/min) → 표시(mm/s)"""
    return gcode_value / 50


def blade_speed_to_gcode(display_value: float) -> int:
    """블레이드 속도 변환: 표시(mm/s) → G-code(mm/min)"""
    return int(display_value * 50)


def led_power_to_display(code_value: int) -> float:
    """LED 파워 변환: 코드값 → 표시(%)"""
    return code_value / 4.4


def led_power_to_code(percent: float) -> int:
    """LED 파워 변환: 표시(%) → 코드값"""
    return int(percent * 4.4)


# ==================== 테스트 ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
        parser = GCodeParser()
        params = parser.parse_zip_file(zip_path)
        
        print(f"\n=== 파일: {zip_path} ===")
        print(f"총 레이어: {params.total_layers}")
        print(f"레이어 높이: {params.layer_height} mm")
        print(f"일반 노출: {params.normal_exposure_time} 초")
        print(f"바닥 노출: {params.bottom_exposure_time} 초")
        print(f"바닥 레이어: {params.bottom_layer_count}")
        print(f"리프트 높이: {params.lift_height} mm")
        print(f"예상 시간: {params.estimated_time:.1f} 분")
        print(f"이미지 수: {len(params.image_files)}")
    else:
        print("사용법: python gcode_parser.py <zip_file>")
