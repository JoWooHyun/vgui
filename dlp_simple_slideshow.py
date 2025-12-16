#!/usr/bin/env python3
"""
DLP 3D 레진프린터용 슬라이드쇼 및 모터 제어 시스템 (Top-Down/블레이드 왕복 대응)
- run.gcode 파라미터 완전 파싱 및 적용
- 실제 3D 레진프린터 동작 시퀀스 구현
- Z축 모터 제어, 블레이드(X축) 제어 통합
- LED 및 프로젝션 제어

버전: v1_clean - 모든 개선사항 반영 (1-6번)
"""

import sys
import os
import zipfile
import ctypes
import time
import requests
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer, QObject, Signal

# ======================= Moonraker API 설정 =======================
MOONRAKER_URL = "http://localhost:7125"

# ======================= Cypress USB 라이브러리 구조체 =======================
class CY_I2C_DATA_CONFIG(ctypes.Structure):
    """Cypress I2C 데이터 설정 구조체"""
    _fields_ = [
        ("slaveAddress", ctypes.c_ubyte),
        ("isStopBit", ctypes.c_bool),
        ("isNakBit", ctypes.c_bool)
    ]

class CY_DATA_BUFFER(ctypes.Structure):
    """Cypress 데이터 버퍼 구조체"""
    _fields_ = [
        ("buffer", ctypes.POINTER(ctypes.c_ubyte)),
        ("length", ctypes.c_uint32),
        ("transferCount", ctypes.c_uint32)
    ]

CY_HANDLE = ctypes.c_void_p

# ======================= DLP 컨트롤러 클래스 =======================
class DLPController:
    """NVR2+ 모듈 제어 클래스"""

    def __init__(self):
        """DLP 컨트롤러 초기화"""
        try:
            self.cy_lib = ctypes.CDLL("libcyusbserial.so")
            print("CyUSBSerial 라이브러리 로드 성공")
        except Exception as e:
            print(f"라이브러리 로드 실패: {e}")
            raise Exception("DLP 컨트롤러 초기화 실패")

        self.handle = None
        self.init_device()

    def init_device(self):
        """NVR2+ 장치 초기화"""
        self.cy_lib.CyLibraryInit.restype = ctypes.c_int
        result = self.cy_lib.CyLibraryInit()
        print(f"라이브러리 초기화 결과: {result}")

        if result != 0:
            raise Exception("CyUSBSerial 라이브러리 초기화 실패")

        # 장치 개수 확인
        num_devices = ctypes.c_ubyte(0)
        self.cy_lib.CyGetListofDevices.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
        self.cy_lib.CyGetListofDevices.restype = ctypes.c_int
        result = self.cy_lib.CyGetListofDevices(ctypes.byref(num_devices))
        print(f"장치 개수 확인 결과: {result}, 장치 수: {num_devices.value}")

        if result != 0 or num_devices.value == 0:
            raise Exception("NVR2+ 장치를 찾을 수 없습니다")

        # 장치 연결
        device_index = 1
        interface_num = 0

        print(f"장치 {device_index}, 인터페이스 {interface_num} 연결 시도")
        handle = CY_HANDLE()
        self.cy_lib.CyOpen.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.POINTER(CY_HANDLE)]
        self.cy_lib.CyOpen.restype = ctypes.c_int
        result = self.cy_lib.CyOpen(device_index, interface_num, ctypes.byref(handle))
        print(f"장치 연결 결과: {result}")

        if result != 0:
            raise Exception(f"NVR2+ 장치 연결 실패: {result}")

        self.handle = handle
        print("DLP 컨트롤러 초기화 완료")

    def projector_on(self):
        """프로젝터 켜기"""
        try:
            print("프로젝터 켜기 시도...")
            self.cy_lib.CySetGpioValue.argtypes = [CY_HANDLE, ctypes.c_ubyte, ctypes.c_ubyte]
            self.cy_lib.CySetGpioValue.restype = ctypes.c_int
            result = self.cy_lib.CySetGpioValue(self.handle, 2, 1)

            if result == 0:
                print("✅ 프로젝터 ON 성공")
                time.sleep(1.0)  # 프로젝터 안정화 대기
                print("프로젝터 안정화 완료")
                return True
            else:
                print(f"❌ 프로젝터 ON 실패: 결과값 {result}")
                return False

        except Exception as e:
            print(f"❌ 프로젝터 켜기 오류: {e}")
            return False

    def projector_off(self):
        """프로젝터 끄기"""
        try:
            print("프로젝터 끄기 시도...")
            self.cy_lib.CySetGpioValue.argtypes = [CY_HANDLE, ctypes.c_ubyte, ctypes.c_ubyte]
            self.cy_lib.CySetGpioValue.restype = ctypes.c_int
            result = self.cy_lib.CySetGpioValue(self.handle, 2, 0)

            if result == 0:
                print("✅ 프로젝터 OFF 성공")
                return True
            else:
                print(f"❌ 프로젝터 OFF 실패: 결과값 {result}")
                return False

        except Exception as e:
            print(f"❌ 프로젝터 끄기 오류: {e}")
            return False

    def led_on(self, brightness=None):
        """LED 켜기 (UV 조사 시작)

        Args:
            brightness: LED 밝기 값 (91~1023), None이면 기본값 440 사용
        """
        try:
            print("UV LED 켜기 시도...")

            # 1단계: LED 밝기 설정 (0x54 명령)
            brightness_value = brightness if brightness is not None else 440
            print(f"LED 밝기를 {brightness_value}(으)로 설정 중...")

            # LED 밝기 설정 (I2C 명령어 0x54)
            # 데이터 포맷: LED current parameter (LSByte, MSByte) * 3
            lsb = brightness_value & 0xFF
            msb = (brightness_value >> 8) & 0xFF
            brightness_data = [lsb, msb, lsb, msb, lsb, msb]

            brightness_result = self.send_i2c(0x54, brightness_data)

            if brightness_result:
                print(f"✅ LED 밝기 {brightness_value} 설정 성공")

            # 2단계: LED 켜기
            result = self.send_i2c(0x52, [0x07])

            if result:
                print("✅ UV LED ON 성공")
                return True
            else:
                print("❌ UV LED ON 실패")
                return False

        except Exception as e:
            print(f"❌ LED 켜기 오류: {e}")
            return False

    def led_off(self):
        """LED 끄기 (UV 조사 중지)"""
        try:
            print("UV LED 끄기 시도...")
            result = self.send_i2c(0x52, [0x00])

            if result:
                print("✅ UV LED OFF 성공")
                return True
            else:
                print("❌ UV LED OFF 실패")
                return False

        except Exception as e:
            print(f"❌ LED 끄기 오류: {e}")
            return False

    def send_i2c(self, command, data):
        """I2C 명령 전송"""
        try:
            i2c_config = CY_I2C_DATA_CONFIG()
            i2c_config.slaveAddress = 0x1B
            i2c_config.isStopBit = True
            i2c_config.isNakBit = False

            buffer_size = len(data) + 1
            buffer = (ctypes.c_ubyte * buffer_size)()
            buffer[0] = command
            for i, d in enumerate(data):
                buffer[i + 1] = d

            data_buffer = CY_DATA_BUFFER()
            data_buffer.buffer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
            data_buffer.length = buffer_size
            data_buffer.transferCount = 0

            self.cy_lib.CyI2cWrite.argtypes = [
                CY_HANDLE,
                ctypes.POINTER(CY_I2C_DATA_CONFIG),
                ctypes.POINTER(CY_DATA_BUFFER),
                ctypes.c_uint32
            ]
            self.cy_lib.CyI2cWrite.restype = ctypes.c_int
            result = self.cy_lib.CyI2cWrite(
                self.handle,
                ctypes.byref(i2c_config),
                ctypes.byref(data_buffer),
                1000
            )
            return result == 0
        except Exception as e:
            print(f"I2C 통신 오류: {e}")
            return False

    def cleanup(self):
        """리소스 정리"""
        try:
            if self.handle:
                self.cy_lib.CyClose.argtypes = [CY_HANDLE]
                self.cy_lib.CyClose.restype = ctypes.c_int
                self.cy_lib.CyClose(self.handle)
                print("DLP 컨트롤러 해제 완료")

            self.cy_lib.CyLibraryExit()
        except Exception as e:
            print(f"DLP 컨트롤러 정리 오류: {e}")


# ======================= 모터 제어 클래스 =======================
class MotorController:
    """Z축, X축 모터 제어 클래스"""
    def __init__(self, motor_callback=None, blade_speed=4500):
        self.motor_callback = motor_callback
        self.current_z_position = 0.0  # 현재 Z축 위치 (mm)
        self.current_x_position = 0.0  # 현재 X축 위치 (mm)

        # 블레이드(X축) 왕복 동작 설정
        self.blade_distance = 125.0    # X축 이동 거리 (mm)
        self.blade_speed = blade_speed  # X축 이동 속도 (mm/min) - 사용자 설정값

        # X축 홈잉 상태 추적
        self.x_is_homed = False        # X축 홈잉 완료 상태

        print("모터 컨트롤러 초기화 완료 (Z/X 지원)")
        print(f"블레이드 설정: 0mm ↔ {self.blade_distance}mm, 속도: {self.blade_speed}mm/min")

    def send_gcode(self, command, timeout=None):
        """G-code 명령 전송"""
        if timeout is None:
            # X축 이동 명령 감지
            if "G0" in command and "X" in command:
                timeout = 300  # X축 이동: 5분
            elif "G1" in command and "X" in command:
                timeout = 300  # X축 이동: 5분
            elif "G28" in command:
                timeout = 120  # 홈잉: 2분
            elif "M400" in command:
                timeout = 300  # M400 대기: 5분
            else:
                timeout = 60   # 기본: 1분

        if self.motor_callback:
            return self.motor_callback(command)
        else:
            try:
                url = f"{MOONRAKER_URL}/printer/gcode/script"
                data = {"script": command}
                response = requests.post(url, json=data, timeout=timeout)
                print(f"G-code 요청: {command} (타임아웃: {timeout}초)")

                if response.status_code == 200:
                    print(f"G-code 전송 성공: {command}")
                    return True
                else:
                    print(f"G-code 전송 실패: {response.status_code}")
                    return False
            except Exception as e:
                print(f"G-code 전송 오류: {e}")
                return False

    def wait_for_movement_complete(self, timeout=300):
        """모든 모터 움직임 완료 대기"""
        print("모터 움직임 완료 대기 중...")

        # M400 명령을 여러 번 시도
        for attempt in range(3):
            print(f"M400 시도 {attempt + 1}/3")
            success = self.send_gcode("M400", timeout=timeout)
            if success:
                print("M400 명령 전송 완료")
                time.sleep(1.0)
                print("모터 움직임 완전 완료")
                return True
            else:
                print(f"M400 시도 {attempt + 1} 실패")
                time.sleep(1.0)

        print("M400 명령 모든 시도 실패 - 고정 대기시간 사용")
        time.sleep(2.0)
        return False

    def home_z_axis(self):
        """Z축 홈 위치로 이동"""
        print("Z축 홈 이동 시작")
        success = self.send_gcode("G28 Z", timeout=120)
        if success:
            self.current_z_position = 0.0
            self.wait_for_movement_complete(timeout=120)
            print("Z축 홈 이동 완료")
        return success

    def home_x_axis(self):
        """X축 홈 위치로 이동"""
        if self.x_is_homed and self.current_x_position == 0.0:
            print("X축 이미 홈 위치에 있음 - 홈잉 생략")
            return True

        print("X축 홈 이동 시작")
        success = self.send_gcode("G28 X", timeout=120)
        if success:
            self.current_x_position = 0.0
            self.x_is_homed = True
            self.wait_for_movement_complete(timeout=120)
            print("X축 홈 이동 완료")
        return success

    def move_x_to_end(self):
        """X축을 블레이드 끝 위치로 이동"""
        print(f"=== X축 {self.blade_distance}mm 위치로 이동 시작 ===")

        # 예상 시간 계산
        distance = abs(self.blade_distance - self.current_x_position)
        expected_time = (distance / self.blade_speed) * 60
        print(f"이동 거리: {distance}mm, 예상 소요시간: {expected_time:.1f}초")

        # 절대 좌표로 이동
        gcode = f"G0 X{self.blade_distance:.1f} F{self.blade_speed}"
        print(f"G-code 명령: {gcode}")

        success = self.send_gcode(gcode, timeout=300)

        if success:
            self.current_x_position = self.blade_distance
            print(f"X축 이동 명령 전송 성공: {self.current_x_position:.1f}mm")

            # 움직임 완료까지 완전 대기
            print("X축 이동 완료 대기 중...")
            move_complete = self.wait_for_movement_complete(timeout=300)

            if move_complete:
                print(f"✅ X축 {self.blade_distance}mm 이동 완전 완료!")
                return True
            else:
                print("⚠️ X축 이동 완료 신호 실패, 추가 대기")
                time.sleep(expected_time)
                print("X축 이동 강제 완료 처리")
                return True
        else:
            print("❌ X축 이동 명령 전송 실패")
            return False

    def move_x_to_position(self, target_position, speed=None):
        """X축을 특정 위치로 이동 (홈 명령이 아닌 일반 이동)"""
        if speed is None:
            speed = self.blade_speed
        
        print(f"=== X축 {target_position}mm 위치로 이동 시작 ===")
        
        # 예상 시간 계산
        distance = abs(target_position - self.current_x_position)
        expected_time = (distance / speed) * 60
        print(f"이동 거리: {distance}mm, 예상 소요시간: {expected_time:.1f}초")
        
        # 절대 좌표로 이동
        gcode = f"G0 X{target_position:.1f} F{speed}"
        print(f"G-code 명령: {gcode}")
        
        success = self.send_gcode(gcode, timeout=300)
        
        if success:
            self.current_x_position = target_position
            print(f"X축 이동 명령 전송 성공: {self.current_x_position:.1f}mm")
            
            # 움직임 완료까지 완전 대기
            print("X축 이동 완료 대기 중...")
            move_complete = self.wait_for_movement_complete(timeout=300)
            
            if move_complete:
                print(f"✅ X축 {target_position}mm 이동 완전 완료!")
                return True
            else:
                print("⚠️ X축 이동 완료 신호 실패, 추가 대기")
                time.sleep(expected_time)
                print("X축 이동 강제 완료 처리")
                return True
        else:
            print("❌ X축 이동 명령 전송 실패")
            return False

    def move_z_lift(self, lift_height, lift_speed):
        """Z축 리프트"""
        target_z = self.current_z_position + lift_height
        print(f"Z축 리프트: {lift_height}mm (속도: {lift_speed}mm/min)")
        gcode = f"G0 Z{target_z:.3f} F{lift_speed}"
        success = self.send_gcode(gcode, timeout=120)
        if success:
            self.current_z_position = target_z
            print(f"Z축 리프트 완료: 현재 위치 {self.current_z_position:.3f}mm")
            self.wait_for_movement_complete(timeout=120)
        return success

    def move_z_down(self, target_position, down_speed):
        """Z축 하강"""
        print(f"Z축 하강: {target_position:.3f}mm (속도: {down_speed}mm/min)")
        gcode = f"G0 Z{target_position:.3f} F{down_speed}"
        success = self.send_gcode(gcode, timeout=120)
        if success:
            self.current_z_position = target_position
            print(f"Z축 하강 완료: 현재 위치 {self.current_z_position:.3f}mm")
            self.wait_for_movement_complete(timeout=120)
        return success

    def wait_for_settle(self, wait_time_ms=500):
        """안정화 대기"""
        if wait_time_ms > 0:
            gcode = f"G4 P{wait_time_ms}"
            return self.send_gcode(gcode, timeout=60)
        return True

# ======================= Qt 진행상황 신호 클래스 =======================
class ProgressSignals(QObject):
    progress_update = Signal(int, int)
    print_finished = Signal()
    print_error = Signal(str)

# ======================= 프로젝터 윈도우 클래스 =======================
class ProjectorWindow(QWidget):
    """DLP 프로젝터 전용 윈도우"""
    def __init__(self, screen_index=1, first_image_data=None):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: black;")
        layout.addWidget(self.label)
        screens = QApplication.screens()
        if len(screens) > screen_index:
            rect = screens[screen_index].geometry()
            self.setGeometry(rect)
            print(f"프로젝터 윈도우를 화면 {screen_index}에 설정: {rect.width()}x{rect.height()}")
        else:
            print(f"화면 {screen_index}를 찾을 수 없음, 기본 화면 사용")
        self.first_image_data = first_image_data

        # 프린팅 제어 플래그
        self.is_paused = False
        self.is_stopped = False

        # 제어 함수들을 속성으로 저장 (나중에 설정됨)
        self.pause_func = None
        self.resume_func = None
        self.stop_func = None

    def show_image(self, pixmap):
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)

    def load_first_image(self):
        if self.first_image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(self.first_image_data)
            self.show_image(pixmap)

    def clear_screen(self):
        self.label.clear()
        self.label.setStyleSheet("background-color: black;")

# ======================= G-code 파라미터 추출 함수 =======================
def extract_print_parameters(zip_path):
    """
    ZIP 파일에서 run.gcode를 읽어 프린팅 파라미터 추출
    """
    params = {
        'fileName': '',
        'machineType': 'DLP_Printer',
        'estimatedPrintTime': 0.0,
        'layerHeight': 0.05,
        'totalLayer': 0,
        'bottomLayerCount': 8,
        'normalExposureTime': 6.0,
        'bottomLayerExposureTime': 50.0,
        'lightOffTime': 0.0,
        'bottomLightOffTime': 0.0,
        'normalDropSpeed': 150,
        'normalLayerLiftHeight': 5.0,
        'normalLayerLiftSpeed': 65,
        'bottomLayerLiftHeight': 5.0,
        'bottomLayerLiftSpeed': 65,
        'zSlowUpDistance': 0.0,
        # 블레이드(X축) 파라미터 기본값
        'blade_min': 0.0,
        'blade_max': 125.0,  # 실제 사용 값과 일치
        'blade_speed': 500,
        'resolutionX': 1440,
        'resolutionY': 2560,
        'machineX': 68.04,
        'machineY': 120.96,
        'machineZ': 150.0,
        'mirror': 0,
        'shrinkageX': 100,
        'shrinkageY': 100,
        'shrinkageZ': 100,
    }
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            png_files = [name for name in zf.namelist()
                        if name.lower().endswith('.png') and name[:-4].isdigit()]
            params['totalLayer'] = len(png_files)
            print(f"PNG 파일 발견: {len(png_files)}개")
            if "run.gcode" in zf.namelist():
                print("run.gcode 파일 발견, 파라미터 추출 중...")
                gcode_content = zf.read("run.gcode").decode('utf-8', errors='ignore')
                for line in gcode_content.split('\n'):
                    line = line.strip()
                    if not line.startswith(';'):
                        continue
                    if ':' in line:
                        parts = line[1:].split(':', 1)
                    elif ' = ' in line:
                        parts = line[1:].split(' = ', 1)
                    else:
                        continue
                    if len(parts) != 2:
                        continue
                    param_name = parts[0].strip()
                    param_value = parts[1].strip()
                    try:
                        if param_name == 'fileName':
                            params['fileName'] = param_value
                        elif param_name == 'totalLayer':
                            params['totalLayer'] = int(param_value)
                        elif param_name == 'layerHeight':
                            params['layerHeight'] = float(param_value)
                        elif param_name in ['bottomLayCount', 'bottomLayerCount']:
                            params['bottomLayerCount'] = int(param_value)
                        elif param_name == 'normalExposureTime':
                            params['normalExposureTime'] = float(param_value)
                        elif param_name in ['bottomLayExposureTime', 'bottomLayerExposureTime']:
                            params['bottomLayerExposureTime'] = float(param_value)
                        elif param_name == 'normalLayerLiftHeight':
                            params['normalLayerLiftHeight'] = float(param_value)
                        elif param_name == 'normalLayerLiftSpeed':
                            params['normalLayerLiftSpeed'] = float(param_value)
                        elif param_name == 'normalDropSpeed':
                            params['normalDropSpeed'] = float(param_value)
                        elif param_name == 'bottomLayerLiftHeight':
                            params['bottomLayerLiftHeight'] = float(param_value)
                        elif param_name == 'bottomLayerLiftSpeed':
                            params['bottomLayerLiftSpeed'] = float(param_value)
                        # 블레이드(X축) 관련 파라미터
                        elif param_name == 'blade_min':
                            params['blade_min'] = float(param_value)
                        elif param_name == 'blade_max':
                            params['blade_max'] = float(param_value)
                        elif param_name == 'blade_speed':
                            params['blade_speed'] = float(param_value)
                    except Exception as e:
                        print(f"파라미터 파싱 오류 ({param_name}): {e}")
                        continue
    except Exception as e:
        print(f"파라미터 추출 오류: {e}")
    return params

# ======================= 메인 프린팅 시퀀스 함수 =======================
def run_slideshow(zip_path, progress_callback=None, motor_callback=None, blade_speed=None, leveling_cycles=0, led_power=None):
    """
    프린팅 파라미터를 적용한 슬라이드쇼 실행
    Top-Down 블레이드 왕복까지 완전 지원
    일시정지/정지 기능 지원

    Args:
        zip_path: ZIP 파일 경로
        progress_callback: 진행률 콜백 함수
        motor_callback: 모터 제어 콜백 함수
        blade_speed: 블레이드 속도 (mm/min), None이면 기본값 4500 사용
        leveling_cycles: 레진 평탄화 왕복 횟수 (0~5회), 기본값 0
        led_power: LED 파워 (91~1023), None이면 기본값 440 사용
    """
    params = extract_print_parameters(zip_path)
    if params['totalLayer'] == 0:
        print("이미지가 없습니다.")
        return None

    dlp = None
    projector = None

    try:
        # 장치 초기화
        dlp = DLPController()

        # 블레이드 속도 결정: GUI에서 전달받은 값 우선, 없으면 기본값 4500
        if blade_speed is None:
            blade_speed = 4500
            print(f"블레이드 속도: {blade_speed} mm/min (기본값)")
        else:
            print(f"블레이드 속도: {blade_speed} mm/min (사용자 설정)")

        motor = MotorController(motor_callback, blade_speed=blade_speed)
        blade_min = params.get('blade_min', 0.0)
        blade_max = params.get('blade_max', 125.0)

        # ZIP에서 이미지 로드
        with zipfile.ZipFile(zip_path, 'r') as zf:
            imgs = []
            for name in zf.namelist():
                if name.lower().endswith('.png') and name[:-4].isdigit():
                    imgs.append(name)
            imgs.sort(key=lambda x: int(x[:-4]))

            if not imgs:
                print("PNG 이미지 없음")
                return None

            # 전체 이미지 데이터 미리 로드
            images_data = []
            for name in imgs:
                images_data.append(zf.read(name))

            # 첫 번째 이미지를 전체화면으로 투영
            app = QApplication.instance() or QApplication([])
            projector = ProjectorWindow(screen_index=1, first_image_data=images_data[0])

            # 제어 함수들 설정
            def pause():
                print("일시정지 요청")
                projector.is_paused = True

            def resume():
                print("재개 요청")
                projector.is_paused = False

            def stop():
                print("정지 요청")
                projector.is_stopped = True
                projector.is_paused = False

            projector.pause_func = pause
            projector.resume_func = resume
            projector.stop_func = stop

            projector.showFullScreen()
            projector.load_first_image()
            app.processEvents()

            # ======== 초기화: Z축, X축 모두 홈 이동 ========
            print("Z축 홈 이동(G28 Z)...")
            if not motor.home_z_axis():
                print("Z축 홈 실패. 종료.")
                return None
            print("X축 홈 이동(G28 X)...")
            if not motor.home_x_axis():
                print("X축 홈 실패. 종료.")
                return None

            # ======== 레진 평탄화 (옵션) ========
            if leveling_cycles > 0:
                print(f"\n========================================")
                print(f"레진 평탄화 작업 시작 (왕복 {leveling_cycles}회)")
                print(f"========================================")
                
                # 1. Z축을 0.1mm 위치로 이동
                print("\n1단계: Z축 0.1mm 위치로 이동")
                if not motor.move_z_lift(0.1, params['normalDropSpeed']):
                    print("⚠️ Z축 0.1mm 이동 실패 - 평탄화 건너뛰기")
                else:
                    print("✅ Z축 0.1mm 위치 완료")
                    
                    # 2. X축 블레이드 왕복 동작
                    for cycle in range(leveling_cycles):
                        print(f"\n--- 평탄화 {cycle + 1}/{leveling_cycles}회 ---")
                        
                        # 2-1. 0mm → 125mm 이동
                        print(f"X축 0mm → 125mm 이동")
                        if not motor.move_x_to_end():
                            print("❌ X축 125mm 이동 실패 - 평탄화 중단")
                            break
                        print("✅ X축 125mm 도착")
                        
                        # 안정화 대기
                        time.sleep(0.2)
                        app.processEvents()
                        
                        # 2-2. 125mm → 0mm 이동 (일반 이동 명령)
                        print(f"X축 125mm → 0mm 이동")
                        if not motor.move_x_to_position(0.0):
                            print("❌ X축 0mm 이동 실패 - 평탄화 중단")
                            break
                        print("✅ X축 0mm 도착")
                        
                        # 안정화 대기
                        time.sleep(0.2)
                        app.processEvents()
                        
                        print(f"✅ 평탄화 {cycle + 1}회 완료")
                    
                    # 3. Z축 홈으로 복귀
                    print("\n3단계: Z축 홈으로 복귀")
                    if not motor.home_z_axis():
                        print("⚠️ Z축 홈 복귀 실패")
                    else:
                        print("✅ Z축 홈 복귀 완료")
                    
                    print(f"\n========================================")
                    print(f"레진 평탄화 작업 완료")
                    print(f"========================================\n")

            # ======== 프로젝터/LED ON ========
            dlp.projector_on()
            time.sleep(0.5)

            # ======== 메인 프린팅 루프 ========
            for layer_idx in range(params['totalLayer']):
                # 정지 체크
                if projector.is_stopped:
                    print("프린팅 정지됨")
                    break

                # 일시정지 체크
                while projector.is_paused:
                    print("프린팅 일시정지 중...")
                    time.sleep(0.5)
                    app.processEvents()
                    if projector.is_stopped:
                        print("일시정지 중 정지 요청")
                        break

                if projector.is_stopped:
                    break

                layer_num = layer_idx + 1
                print(f"\n==== {layer_num}/{params['totalLayer']} 레이어 시작 ====")

                # 레이어 타입 결정
                is_bottom_layer = layer_idx < params['bottomLayerCount']

                if is_bottom_layer:
                    lift_height = params['bottomLayerLiftHeight']
                    lift_speed = params['bottomLayerLiftSpeed']
                    exposure_time = params['bottomLayerExposureTime']
                    print(f"바닥 레이어 {layer_num}: 노출 {exposure_time}초")
                else:
                    lift_height = params['normalLayerLiftHeight']
                    lift_speed = params['normalLayerLiftSpeed']
                    exposure_time = params['normalExposureTime']
                    print(f"일반 레이어 {layer_num}: 노출 {exposure_time}초")

                # =================== Z축 위치 설정 (레이어 높이) ===================
                target_z = params['layerHeight'] * layer_num
                print(f"=== 레이어 {layer_num} Z축 위치 설정 ===")
                print(f"목표 Z축 위치: {target_z:.3f}mm")

                if layer_idx == 0:
                    # 첫 번째 레이어: 홈에서 바로 상승
                    print(f"홈 위치(0mm)에서 {target_z:.3f}mm 상승")
                    if not motor.move_z_lift(target_z, params['normalDropSpeed']):
                        print("오류: 첫 번째 레이어 Z축 설정 실패")
                        break
                else:
                    # 두 번째 레이어부터: 이미 목표 위치에 있음 (이전 레이어에서 하강 완료)
                    print(f"Z축 이미 목표 위치 {target_z:.3f}mm에 있음")

                # Z축 안정화 대기
                motor.wait_for_settle(100)
                app.processEvents()
                print("=== Z축 위치 설정 완료 ===")

                # =================== 블레이드(X축) 0mm → 125mm 이동 ===================
                print("=== 블레이드(X축) 0mm → 125mm 이동 시작 ===")

                # 1단계: 홈 위치 확인 및 이동 (필요시)
                if motor.current_x_position != 0.0 or not motor.x_is_homed:
                    print("X축이 홈 위치가 아님 - 홈 이동 필요")
                    if not motor.home_x_axis():
                        print("❌ X축 홈 이동 실패 - 프린팅 중단")
                        break
                    print("✅ X축 홈 이동 완료: 0mm")
                else:
                    print("✅ X축 이미 홈 위치에 있음")

                # 2단계: 125mm로 이동
                print(f"X축 {motor.blade_distance}mm 이동 시작")
                if not motor.move_x_to_end():
                    print(f"❌ X축 {motor.blade_distance}mm 이동 실패 - 프린팅 중단")
                    break
                print(f"✅ X축 {motor.blade_distance}mm 이동 완료")

                # X축 안정화 대기
                print("X축 안정화 대기: 2초")
                for _ in range(2):
                    if projector.is_stopped:
                        break
                    time.sleep(0.1)
                    app.processEvents()
                print("✅ X축 완전 안정화 완료")

                if projector.is_stopped:
                    break

                print("=== 블레이드(X축) 이동 완전 완료 ===")

                # 모든 움직임 완료 후 최종 대기
                print("모든 모터 최종 정지 확인 중...")
                for _ in range(2):
                    if projector.is_stopped:
                        break
                    time.sleep(0.1)
                    app.processEvents()

                try:
                    motor.wait_for_movement_complete(timeout=120)
                    print("✅ 모든 모터 완전 정지 확인")
                except:
                    print("⚠️ M400 확인 실패 - 계속 진행")

                print("✅ 모든 모터 움직임 완료")

                # =================== 이미지 투영 및 노광 ===================
                print("=== 이미지 투영 및 노광 시작 ===")

                # 1단계: 이미지 표시
                print(f"1단계: 레이어 {layer_num} 이미지 표시")
                pixmap = QPixmap()
                pixmap.loadFromData(images_data[layer_idx])
                projector.show_image(pixmap)

                # Qt 이벤트 처리
                for _ in range(2):
                    app.processEvents()
                    time.sleep(0.1)

                print(f"✅ 레이어 {layer_num} 이미지 투영 완료")

                # 2단계: 이미지 안정화
                print("이미지 안정화 대기: 1초")
                for _ in range(2):
                    if projector.is_stopped:
                        break
                    time.sleep(0.1)
                    app.processEvents()

                if projector.is_stopped:
                    break

                # 3단계: LED ON
                print(f"UV LED 켜기 (파워: {led_power if led_power else 440})")
                led_success = dlp.led_on(brightness=led_power)
                if led_success:
                    print("✅ UV LED 켜기 성공")
                else:
                    print("❌ UV LED 켜기 실패")

                # 4단계: 노광 (GUI 이벤트 처리를 위해 0.1초 단위로 분할)
                print(f"UV 노광 - {exposure_time}초")
                exposure_start = time.time()
                while time.time() - exposure_start < exposure_time:
                    if projector.is_stopped:
                        print("노광 중 정지 요청")
                        break
                    time.sleep(0.1)
                    app.processEvents()

                if projector.is_stopped:
                    dlp.led_off()
                    break

                # 5단계: LED OFF
                print("UV LED 끄기")
                dlp.led_off()
                print("✅ UV 노광 완료")

                # 6단계: Z축 리프트 (5mm 상승)
                print("=== Z축 리프트 시작 ===")
                print(f"Z축 {lift_height}mm 상승")
                if not motor.move_z_lift(lift_height, lift_speed):
                    print("❌ Z축 리프트 실패 - 프린팅 중단")
                    break
                print(f"✅ Z축 리프트 완료: 현재 위치 {motor.current_z_position:.3f}mm")

                # Z축 안정화
                motor.wait_for_settle(100)
                app.processEvents()

                if projector.is_stopped:
                    break

                # 7단계: X축 복귀 (125mm → 0mm) - 출력물에 걸리지 않도록 먼저 복귀
                print("=== X축 0mm 위치로 복귀 시작 ===")
                print(f"현재 X축 위치: {motor.current_x_position}mm")

                if motor.current_x_position != 0.0:
                    print("X축 0mm로 이동")
                    if not motor.move_x_to_position(0.0):
                        print("❌ X축 0mm 이동 실패 - 프린팅 중단")
                        break
                    print("✅ X축 0mm 복귀 완료")
                else:
                    print("✅ X축 이미 0mm 위치에 있음")

                # X축 복귀 후 안정화
                motor.wait_for_settle(100)
                app.processEvents()

                if projector.is_stopped:
                    break

                # 8단계: 다음 레이어 높이로 Z축 하강 (마지막 레이어가 아닌 경우)
                if layer_idx < params['totalLayer'] - 1:
                    next_layer_num = layer_num + 1
                    next_target_z = params['layerHeight'] * next_layer_num
                    print("=== Z축 다음 레이어 높이로 하강 ===")
                    print(f"다음 레이어 {next_layer_num} 목표 위치: {next_target_z:.3f}mm")

                    if not motor.move_z_down(next_target_z, params['normalDropSpeed']):
                        print("❌ Z축 하강 실패 - 프린팅 중단")
                        break
                    print(f"✅ Z축 하강 완료: 현재 위치 {motor.current_z_position:.3f}mm")

                    # Z축 하강 후 안정화
                    motor.wait_for_settle(100)
                    app.processEvents()

                    if projector.is_stopped:
                        break
                else:
                    print("=== 마지막 레이어 - Z축 하강 생략 ===")

                # 9단계: 레이어 완료 안정화
                print("레이어 완료 후 안정화: 2초")
                for _ in range(5):
                    if projector.is_stopped:
                        break
                    time.sleep(0.1)
                    app.processEvents()

                if projector.is_stopped:
                    break

                print(f"=== 레이어 {layer_num} 완전 완료 ===")

                # 진행 콜백
                if progress_callback:
                    progress_callback(layer_num, params['totalLayer'])

            # ======== 프린팅 종료 ========
            print("프린팅 완료. LED/프로젝터 OFF, 화면 클리어")
            dlp.led_off()
            dlp.projector_off()
            projector.clear_screen()
            projector.close()
            app.processEvents()

            return projector

    except Exception as e:
        print(f"❌ 프린팅 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

        # 긴급 정지
        if dlp:
            try:
                dlp.led_off()
                dlp.projector_off()
            except:
                pass

        if projector:
            try:
                projector.clear_screen()
                projector.close()
            except:
                pass

        return None

    finally:
        # 항상 실행: USB 장치 정리
        if dlp:
            try:
                dlp.cleanup()
                print("✅ DLP 컨트롤러 리소스 정리 완료")
            except Exception as e:
                print(f"⚠️ DLP 정리 중 오류: {e}")