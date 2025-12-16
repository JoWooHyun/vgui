"""
VERICOM DLP 3D Printer - DLP Controller
NVR2+ 프로젝터 및 LED 제어 (CyUSBSerial I2C)

실제 하드웨어 동작 코드 (dlp_simple_slideshow.py 기반)
"""

import ctypes
import time
from typing import Optional, List
from dataclasses import dataclass
from enum import IntEnum


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


class NVRCommand(IntEnum):
    """NVR2+ I2C 명령 코드"""
    LED_CONTROL = 0x52      # LED ON/OFF
    LED_BRIGHTNESS = 0x54   # LED 밝기 설정
    PATTERN_SELECT = 0x05   # 테스트 패턴 선택
    PATTERN_SET = 0x0B      # 테스트 패턴 설정
    FLIP_CONTROL = 0x14     # 이미지 반전


class LEDState(IntEnum):
    """LED 상태"""
    OFF = 0x00
    ON = 0x07


class FlipMode(IntEnum):
    """이미지 반전 모드"""
    NONE = 0x00
    HORIZONTAL = 0x01
    VERTICAL = 0x02
    BOTH = 0x03


@dataclass
class DLPConfig:
    """DLP 설정"""
    i2c_address: int = 0x1B         # NVR2+ I2C 주소
    default_brightness: int = 440   # 기본 LED 밝기 (91~1023)
    min_brightness: int = 91
    max_brightness: int = 1023
    gpio_projector: int = 2         # 프로젝터 ON/OFF GPIO 핀


class DLPController:
    """
    NVR2+ DLP 프로젝터 및 LED 제어 클래스

    CyUSBSerial 라이브러리를 통해 I2C 통신
    라즈베리파이에서만 동작 (Windows에서는 시뮬레이션 모드)
    """

    def __init__(self, simulation: bool = False):
        """
        Args:
            simulation: True면 실제 하드웨어 없이 시뮬레이션
        """
        self.config = DLPConfig()
        self.simulation = simulation
        self._is_initialized = False
        self._projector_on = False
        self._led_on = False
        self._current_brightness = self.config.default_brightness
        self._flip_mode = FlipMode.NONE

        # CyUSBSerial 핸들 (실제 하드웨어용)
        self.handle = None
        self.cy_lib = None

    # ==================== 초기화 ====================

    def initialize(self) -> bool:
        """DLP 컨트롤러 초기화"""
        if self.simulation:
            print("[DLP] 시뮬레이션 모드로 초기화")
            self._is_initialized = True
            return True

        try:
            # CyUSBSerial 라이브러리 로드 (라즈베리파이)
            self.cy_lib = ctypes.CDLL("libcyusbserial.so")
            print("[DLP] CyUSBSerial 라이브러리 로드 성공")

            # 라이브러리 초기화
            self.cy_lib.CyLibraryInit.restype = ctypes.c_int
            result = self.cy_lib.CyLibraryInit()
            print(f"[DLP] 라이브러리 초기화 결과: {result}")

            if result != 0:
                print("[DLP] CyUSBSerial 라이브러리 초기화 실패")
                return False

            # 장치 개수 확인
            num_devices = ctypes.c_ubyte(0)
            self.cy_lib.CyGetListofDevices.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
            self.cy_lib.CyGetListofDevices.restype = ctypes.c_int
            result = self.cy_lib.CyGetListofDevices(ctypes.byref(num_devices))
            print(f"[DLP] 장치 개수 확인 결과: {result}, 장치 수: {num_devices.value}")

            if result != 0 or num_devices.value == 0:
                print("[DLP] NVR2+ 장치를 찾을 수 없습니다")
                return False

            # 장치 연결 (device_index=1, interface_num=0)
            device_index = 1
            interface_num = 0

            print(f"[DLP] 장치 {device_index}, 인터페이스 {interface_num} 연결 시도")
            handle = CY_HANDLE()
            self.cy_lib.CyOpen.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.POINTER(CY_HANDLE)]
            self.cy_lib.CyOpen.restype = ctypes.c_int
            result = self.cy_lib.CyOpen(device_index, interface_num, ctypes.byref(handle))
            print(f"[DLP] 장치 연결 결과: {result}")

            if result != 0:
                print(f"[DLP] NVR2+ 장치 연결 실패: {result}")
                return False

            self.handle = handle
            self._is_initialized = True
            print("[DLP] NVR2+ 초기화 성공")
            return True

        except Exception as e:
            print(f"[DLP] 초기화 실패: {e}")
            return False

    def close(self):
        """리소스 정리"""
        if self._led_on:
            self.led_off()
        if self._projector_on:
            self.projector_off()

        if self.handle and self.cy_lib:
            try:
                self.cy_lib.CyClose.argtypes = [CY_HANDLE]
                self.cy_lib.CyClose.restype = ctypes.c_int
                self.cy_lib.CyClose(self.handle)
                print("[DLP] 장치 연결 해제")

                self.cy_lib.CyLibraryExit()
                print("[DLP] 라이브러리 정리 완료")
            except Exception as e:
                print(f"[DLP] 정리 중 오류: {e}")

            self.handle = None

        self._is_initialized = False
        print("[DLP] 컨트롤러 종료")

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    # ==================== I2C 통신 ====================

    def _send_i2c(self, command: int, data: List[int]) -> bool:
        """
        I2C 명령 전송

        Args:
            command: 명령 코드
            data: 데이터 바이트 리스트
        """
        if self.simulation:
            print(f"[DLP-SIM] I2C 전송: cmd=0x{command:02X}, data={[hex(d) for d in data]}")
            return True

        if not self.handle or not self.cy_lib:
            print("[DLP] 장치가 초기화되지 않음")
            return False

        try:
            # I2C 설정
            i2c_config = CY_I2C_DATA_CONFIG()
            i2c_config.slaveAddress = self.config.i2c_address
            i2c_config.isStopBit = True
            i2c_config.isNakBit = False

            # 데이터 버퍼 준비 (command + data)
            buffer_size = len(data) + 1
            buffer = (ctypes.c_ubyte * buffer_size)()
            buffer[0] = command
            for i, d in enumerate(data):
                buffer[i + 1] = d

            # CY_DATA_BUFFER 설정
            data_buffer = CY_DATA_BUFFER()
            data_buffer.buffer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
            data_buffer.length = buffer_size
            data_buffer.transferCount = 0

            # I2C 쓰기
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
                1000  # timeout ms
            )

            if result == 0:
                return True
            else:
                print(f"[DLP] I2C 쓰기 실패: {result}")
                return False

        except Exception as e:
            print(f"[DLP] I2C 전송 오류: {e}")
            return False

    def _set_gpio(self, pin: int, value: int) -> bool:
        """GPIO 설정 (프로젝터 ON/OFF용)"""
        if self.simulation:
            print(f"[DLP-SIM] GPIO 설정: pin={pin}, value={value}")
            return True

        if not self.handle or not self.cy_lib:
            print("[DLP] 장치가 초기화되지 않음")
            return False

        try:
            self.cy_lib.CySetGpioValue.argtypes = [CY_HANDLE, ctypes.c_ubyte, ctypes.c_ubyte]
            self.cy_lib.CySetGpioValue.restype = ctypes.c_int
            result = self.cy_lib.CySetGpioValue(self.handle, pin, value)

            if result == 0:
                return True
            else:
                print(f"[DLP] GPIO 설정 실패: {result}")
                return False
        except Exception as e:
            print(f"[DLP] GPIO 설정 오류: {e}")
            return False

    # ==================== 프로젝터 제어 ====================

    def projector_on(self) -> bool:
        """프로젝터 켜기"""
        print("[DLP] 프로젝터 켜기 시도...")
        if self._set_gpio(self.config.gpio_projector, 1):
            self._projector_on = True
            print("[DLP] ✅ 프로젝터 ON 성공")
            time.sleep(1.0)  # 프로젝터 안정화 대기
            print("[DLP] 프로젝터 안정화 완료")
            return True
        print("[DLP] ❌ 프로젝터 ON 실패")
        return False

    def projector_off(self) -> bool:
        """프로젝터 끄기"""
        print("[DLP] 프로젝터 끄기 시도...")
        if self._set_gpio(self.config.gpio_projector, 0):
            self._projector_on = False
            print("[DLP] ✅ 프로젝터 OFF 성공")
            return True
        print("[DLP] ❌ 프로젝터 OFF 실패")
        return False

    @property
    def is_projector_on(self) -> bool:
        return self._projector_on

    # ==================== LED 제어 ====================

    def led_on(self, brightness: Optional[int] = None) -> bool:
        """
        LED 켜기 (UV 조사 시작)

        Args:
            brightness: 밝기 (91~1023), None이면 현재 설정값 사용
        """
        print("[DLP] UV LED 켜기 시도...")

        # 1단계: LED 밝기 설정 (0x54 명령)
        if brightness is not None:
            self.set_brightness(brightness)

        # 2단계: LED 켜기 (0x52 명령, 0x07 = ON)
        if self._send_i2c(NVRCommand.LED_CONTROL, [LEDState.ON]):
            self._led_on = True
            print(f"[DLP] ✅ UV LED ON 성공 (brightness={self._current_brightness})")
            return True

        print("[DLP] ❌ UV LED ON 실패")
        return False

    def led_off(self) -> bool:
        """LED 끄기 (UV 조사 중지)"""
        print("[DLP] UV LED 끄기 시도...")
        if self._send_i2c(NVRCommand.LED_CONTROL, [LEDState.OFF]):
            self._led_on = False
            print("[DLP] ✅ UV LED OFF 성공")
            return True
        print("[DLP] ❌ UV LED OFF 실패")
        return False

    @property
    def is_led_on(self) -> bool:
        return self._led_on

    def set_brightness(self, brightness: int) -> bool:
        """
        LED 밝기 설정

        Args:
            brightness: 91~1023
        """
        brightness = max(self.config.min_brightness,
                        min(brightness, self.config.max_brightness))

        print(f"[DLP] LED 밝기를 {brightness}(으)로 설정 중...")

        # NVR2+ 밝기 데이터 형식: [LSB, MSB] x 3 (RGB)
        lsb = brightness & 0xFF
        msb = (brightness >> 8) & 0xFF
        data = [lsb, msb, lsb, msb, lsb, msb]

        if self._send_i2c(NVRCommand.LED_BRIGHTNESS, data):
            self._current_brightness = brightness
            print(f"[DLP] ✅ LED 밝기 {brightness} 설정 성공")
            return True

        print(f"[DLP] ❌ LED 밝기 설정 실패")
        return False

    @property
    def current_brightness(self) -> int:
        return self._current_brightness

    # ==================== 이미지 반전 ====================

    def set_flip(self, horizontal: bool = False, vertical: bool = False) -> bool:
        """
        이미지 반전 설정

        Args:
            horizontal: 좌우 반전
            vertical: 상하 반전
        """
        # 반전 모드 계산 (비트 플래그)
        mode = 0x00
        if horizontal:
            mode |= 0x02
        if vertical:
            mode |= 0x04

        if self._send_i2c(NVRCommand.FLIP_CONTROL, [mode]):
            self._flip_mode = mode
            print(f"[DLP] 반전 설정: H={horizontal}, V={vertical} (0x{mode:02X})")
            return True
        return False

    def get_flip_value(self) -> int:
        """현재 반전 모드 값 반환"""
        return self._flip_mode

    # ==================== 테스트 패턴 ====================

    def set_test_pattern(self, pattern: int) -> bool:
        """
        테스트 패턴 설정

        Args:
            pattern: 패턴 코드 (0x01: Ramp, 0x07: Checker 등)
        """
        # 패턴 선택
        if not self._send_i2c(NVRCommand.PATTERN_SELECT, [pattern]):
            return False

        # 패턴 활성화
        if not self._send_i2c(NVRCommand.PATTERN_SET, [0x01]):
            return False

        print(f"[DLP] 테스트 패턴 설정: 0x{pattern:02X}")
        return True

    def clear_test_pattern(self) -> bool:
        """테스트 패턴 해제 (외부 입력으로 전환)"""
        if self._send_i2c(NVRCommand.PATTERN_SET, [0x00]):
            print("[DLP] 테스트 패턴 해제")
            return True
        return False

    # ==================== 복합 동작 ====================

    def expose(self, duration: float, brightness: Optional[int] = None) -> bool:
        """
        노광 실행

        Args:
            duration: 노광 시간 (초)
            brightness: LED 밝기
        """
        if not self.led_on(brightness):
            return False

        time.sleep(duration)

        return self.led_off()

    def start_exposure_test(self, pattern: int, h_flip: bool, v_flip: bool,
                           brightness: int = 440) -> bool:
        """
        노출 테스트 시작

        Args:
            pattern: 테스트 패턴 (0x01: Ramp, 0x07: Checker)
            h_flip: 좌우 반전
            v_flip: 상하 반전
            brightness: LED 밝기
        """
        # 프로젝터 켜기
        if not self.projector_on():
            return False

        # 반전 설정
        self.set_flip(h_flip, v_flip)

        # 패턴 설정
        self.set_test_pattern(pattern)

        # LED 켜기
        return self.led_on(brightness)

    def stop_exposure_test(self) -> bool:
        """노출 테스트 정지"""
        self.led_off()
        self.clear_test_pattern()
        self.projector_off()
        return True


# 테스트용
if __name__ == "__main__":
    import sys

    # 시뮬레이션 모드로 테스트
    simulation = "--sim" in sys.argv

    dlp = DLPController(simulation=simulation)

    if dlp.initialize():
        print("초기화 성공!")

        # 테스트
        dlp.projector_on()
        dlp.set_brightness(500)
        dlp.led_on()
        time.sleep(1)
        dlp.led_off()
        dlp.projector_off()

        dlp.close()
    else:
        print("초기화 실패")
