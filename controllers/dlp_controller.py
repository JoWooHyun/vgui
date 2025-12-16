"""
VERICOM DLP 3D Printer - DLP Controller
NVR2+ 프로젝터 및 LED 제어 (CyUSBSerial I2C)
"""

import time
from typing import Optional, List
from dataclasses import dataclass
from enum import IntEnum


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
            import ctypes
            self.cy_lib = ctypes.CDLL("/usr/local/lib/libcyusbserial.so")

            # 장치 열기
            device_count = ctypes.c_int()
            self.cy_lib.CyGetListofDevices(ctypes.byref(device_count))

            if device_count.value > 0:
                self.handle = ctypes.c_void_p()
                result = self.cy_lib.CyOpen(0, 0, ctypes.byref(self.handle))

                if result == 0:
                    self._is_initialized = True
                    print("[DLP] NVR2+ 초기화 성공")
                    return True

            print("[DLP] 장치를 찾을 수 없음")
            return False

        except Exception as e:
            print(f"[DLP] 초기화 실패: {e}")
            print("[DLP] 시뮬레이션 모드로 전환")
            self.simulation = True
            self._is_initialized = True
            return True

    def close(self):
        """리소스 정리"""
        if self._led_on:
            self.led_off()
        if self._projector_on:
            self.projector_off()

        if self.handle and self.cy_lib:
            self.cy_lib.CyClose(self.handle)
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
            return False

        try:
            import ctypes

            # I2C 설정
            config = (ctypes.c_uint8 * 16)()
            config[0] = self.config.i2c_address
            config[1] = 0  # 7-bit address
            config[2] = 100  # 100kHz

            self.cy_lib.CySetI2cConfig(self.handle, ctypes.byref(config))

            # 데이터 준비
            write_data = [command] + data
            buffer = (ctypes.c_uint8 * len(write_data))(*write_data)

            # I2C 쓰기
            result = self.cy_lib.CyI2cWrite(
                self.handle,
                ctypes.byref(buffer),
                len(write_data),
                1000  # timeout ms
            )

            return result == 0

        except Exception as e:
            print(f"[DLP] I2C 전송 오류: {e}")
            return False

    def _set_gpio(self, pin: int, value: int) -> bool:
        """GPIO 설정 (프로젝터 ON/OFF용)"""
        if self.simulation:
            print(f"[DLP-SIM] GPIO 설정: pin={pin}, value={value}")
            return True

        if not self.handle or not self.cy_lib:
            return False

        try:
            result = self.cy_lib.CySetGpioValue(self.handle, pin, value)
            return result == 0
        except Exception as e:
            print(f"[DLP] GPIO 설정 오류: {e}")
            return False

    # ==================== 프로젝터 제어 ====================

    def projector_on(self) -> bool:
        """프로젝터 켜기"""
        if self._set_gpio(self.config.gpio_projector, 1):
            self._projector_on = True
            print("[DLP] 프로젝터 ON")
            time.sleep(0.1)  # 안정화 대기
            return True
        return False

    def projector_off(self) -> bool:
        """프로젝터 끄기"""
        if self._set_gpio(self.config.gpio_projector, 0):
            self._projector_on = False
            print("[DLP] 프로젝터 OFF")
            return True
        return False

    @property
    def is_projector_on(self) -> bool:
        return self._projector_on

    # ==================== LED 제어 ====================

    def led_on(self, brightness: Optional[int] = None) -> bool:
        """
        LED 켜기

        Args:
            brightness: 밝기 (91~1023), None이면 현재 설정값 사용
        """
        if brightness is not None:
            self.set_brightness(brightness)

        if self._send_i2c(NVRCommand.LED_CONTROL, [LEDState.ON]):
            self._led_on = True
            print(f"[DLP] LED ON (brightness={self._current_brightness})")
            return True
        return False

    def led_off(self) -> bool:
        """LED 끄기"""
        if self._send_i2c(NVRCommand.LED_CONTROL, [LEDState.OFF]):
            self._led_on = False
            print("[DLP] LED OFF")
            return True
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

        # NVR2+ 밝기 데이터 형식: [LSB, MSB] x 3 (RGB)
        lsb = brightness & 0xFF
        msb = (brightness >> 8) & 0xFF
        data = [lsb, msb, lsb, msb, lsb, msb]

        if self._send_i2c(NVRCommand.LED_BRIGHTNESS, data):
            self._current_brightness = brightness
            print(f"[DLP] LED 밝기 설정: {brightness}")
            return True
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
        mode = FlipMode.NONE
        if horizontal and vertical:
            mode = FlipMode.BOTH
        elif horizontal:
            mode = FlipMode.HORIZONTAL
        elif vertical:
            mode = FlipMode.VERTICAL

        if self._send_i2c(NVRCommand.FLIP_CONTROL, [mode]):
            self._flip_mode = mode
            print(f"[DLP] 반전 설정: H={horizontal}, V={vertical}")
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
            pattern: 패턴 코드 (0: Ramp, 1: Checker 등)
        """
        # 패턴 선택
        if not self._send_i2c(NVRCommand.PATTERN_SELECT, [pattern]):
            return False

        # 패턴 활성화
        if not self._send_i2c(NVRCommand.PATTERN_SET, [0x01]):
            return False

        print(f"[DLP] 테스트 패턴 설정: {pattern}")
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
            pattern: 테스트 패턴 (0: Ramp, 1: Checker)
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
    dlp = DLPController(simulation=True)

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
