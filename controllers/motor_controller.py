"""
VERICOM DLP 3D Printer - Motor Controller
Moonraker API를 통한 Z축/X축 모터 제어
"""

import requests
import time
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class MotorConfig:
    """모터 설정"""
    z_speed: int = 300          # Z축 이동 속도 (mm/min)
    x_speed: int = 4500         # X축 이동 속도 (mm/min)
    z_home_speed: int = 300     # Z축 홈 속도
    x_home_speed: int = 4500    # X축 홈 속도
    x_max: float = 125.0        # X축 최대 위치 (mm)
    z_max: float = 150.0        # Z축 최대 위치 (mm)


class MotorController:
    """
    Moonraker API를 통한 모터 제어 클래스

    Z축: 빌드 플레이트 상하 이동
    X축: 블레이드 수평 이동 (Top-Down DLP 특징)
    """

    def __init__(self, moonraker_url: str = "http://localhost:7125"):
        self.moonraker_url = moonraker_url.rstrip('/')
        self.config = MotorConfig()
        self._is_connected = False

        # 현재 위치 캐시
        self._z_position: float = 0.0
        self._x_position: float = 0.0

    # ==================== 연결 관리 ====================

    def connect(self) -> bool:
        """Moonraker 연결 확인"""
        try:
            response = requests.get(
                f"{self.moonraker_url}/printer/info",
                timeout=5
            )
            if response.status_code == 200:
                self._is_connected = True
                print("[Motor] Moonraker 연결됨")
                return True
        except requests.exceptions.RequestException as e:
            print(f"[Motor] 연결 실패: {e}")

        self._is_connected = False
        return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    # ==================== G-code 전송 ====================

    def send_gcode(self, gcode: str, timeout: int = 5) -> bool:
        """
        G-code 명령 전송

        Args:
            gcode: G-code 문자열 (여러 줄 가능)
            timeout: 타임아웃 (초)

        Returns:
            성공 여부
        """
        try:
            url = f"{self.moonraker_url}/printer/gcode/script"
            response = requests.post(
                url,
                json={"script": gcode},
                timeout=timeout
            )

            if response.status_code == 200:
                print(f"[Motor] G-code 전송: {gcode.replace(chr(10), ' | ')}")
                return True
            else:
                print(f"[Motor] G-code 실패: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"[Motor] G-code 전송 오류: {e}")
            return False

    # ==================== Z축 제어 ====================

    def z_home(self) -> bool:
        """Z축 홈으로 이동"""
        print("[Motor] Z축 홈 이동")
        return self.send_gcode("G28 Z", timeout=60)

    def z_move_relative(self, distance: float, speed: Optional[int] = None) -> bool:
        """
        Z축 상대 이동

        Args:
            distance: 이동 거리 (양수: 위로, 음수: 아래로)
            speed: 이동 속도 (mm/min), None이면 기본값
        """
        speed = speed or self.config.z_speed
        gcode = f"G91\nG1 Z{distance} F{speed}\nG90"
        print(f"[Motor] Z축 상대 이동: {distance}mm @ {speed}mm/min")
        return self.send_gcode(gcode)

    def z_move_absolute(self, position: float, speed: Optional[int] = None) -> bool:
        """
        Z축 절대 위치로 이동

        Args:
            position: 목표 위치 (mm)
            speed: 이동 속도 (mm/min)
        """
        speed = speed or self.config.z_speed
        gcode = f"G90\nG0 Z{position} F{speed}"
        print(f"[Motor] Z축 절대 이동: {position}mm @ {speed}mm/min")
        return self.send_gcode(gcode)

    def z_up(self, distance: float) -> bool:
        """Z축 위로 이동 (빌드 플레이트 상승)"""
        return self.z_move_relative(abs(distance))

    def z_down(self, distance: float) -> bool:
        """Z축 아래로 이동 (빌드 플레이트 하강)"""
        return self.z_move_relative(-abs(distance))

    # ==================== X축 (블레이드) 제어 ====================

    def x_home(self) -> bool:
        """X축 홈으로 이동 (블레이드 원점)"""
        print("[Motor] X축 홈 이동")
        return self.send_gcode("G28 X", timeout=60)

    def x_move_relative(self, distance: float, speed: Optional[int] = None) -> bool:
        """
        X축 상대 이동

        Args:
            distance: 이동 거리 (양수: 오른쪽, 음수: 왼쪽)
            speed: 이동 속도 (mm/min)
        """
        speed = speed or self.config.x_speed
        gcode = f"G91\nG0 X{distance} F{speed}\nG90"
        print(f"[Motor] X축 상대 이동: {distance}mm @ {speed}mm/min")
        return self.send_gcode(gcode, timeout=300)  # X축은 긴 타임아웃

    def x_move_absolute(self, position: float, speed: Optional[int] = None) -> bool:
        """
        X축 절대 위치로 이동

        Args:
            position: 목표 위치 (mm), 0~125
            speed: 이동 속도 (mm/min)
        """
        speed = speed or self.config.x_speed
        position = max(0, min(position, self.config.x_max))
        gcode = f"G90\nG0 X{position} F{speed}"
        print(f"[Motor] X축 절대 이동: {position}mm @ {speed}mm/min")
        return self.send_gcode(gcode, timeout=300)

    def x_to_end(self, speed: Optional[int] = None) -> bool:
        """X축 끝점(125mm)으로 이동"""
        return self.x_move_absolute(self.config.x_max, speed)

    def x_to_home(self, speed: Optional[int] = None) -> bool:
        """X축 홈(0mm)으로 이동"""
        return self.x_move_absolute(0, speed)

    # ==================== 복합 동작 ====================

    def home_all(self) -> bool:
        """모든 축 홈으로 이동"""
        print("[Motor] 모든 축 홈 이동")
        return self.send_gcode("G28", timeout=120)

    def emergency_stop(self) -> bool:
        """비상 정지"""
        print("[Motor] 비상 정지!")
        try:
            response = requests.post(
                f"{self.moonraker_url}/printer/emergency_stop",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def leveling_cycle(self, cycles: int = 1, speed: Optional[int] = None) -> bool:
        """
        레진 평탄화 사이클

        Args:
            cycles: 왕복 횟수
            speed: 블레이드 속도

        Flow:
            1. Z축 0.1mm 이동
            2. X축 0 → 125 → 0 왕복 (N회)
            3. Z축 홈 복귀
        """
        if cycles <= 0:
            return True

        speed = speed or self.config.x_speed
        print(f"[Motor] 레진 평탄화 시작 ({cycles}회)")

        # Z축 약간 상승
        if not self.z_move_absolute(0.1):
            return False

        # X축 왕복
        for i in range(cycles):
            print(f"[Motor] 평탄화 {i+1}/{cycles}")
            if not self.x_to_end(speed):
                return False
            if not self.x_to_home(speed):
                return False

        # Z축 홈 복귀
        if not self.z_home():
            return False

        print("[Motor] 레진 평탄화 완료")
        return True

    # ==================== 상태 조회 ====================

    def get_position(self) -> Tuple[float, float]:
        """
        현재 위치 조회

        Returns:
            (z_position, x_position)
        """
        try:
            response = requests.get(
                f"{self.moonraker_url}/printer/objects/query",
                params={"toolhead": "position"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                pos = data.get('result', {}).get('status', {}).get('toolhead', {}).get('position', [0, 0, 0, 0])
                self._x_position = pos[0] if len(pos) > 0 else 0
                self._z_position = pos[2] if len(pos) > 2 else 0
        except:
            pass

        return (self._z_position, self._x_position)

    def get_printer_state(self) -> str:
        """프린터 상태 조회 (ready, printing, paused, error 등)"""
        try:
            response = requests.get(
                f"{self.moonraker_url}/printer/objects/query",
                params={"print_stats": "state"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('result', {}).get('status', {}).get('print_stats', {}).get('state', 'unknown')
        except:
            pass
        return 'unknown'


# 테스트용
if __name__ == "__main__":
    motor = MotorController("http://localhost:7125")

    if motor.connect():
        print("연결 성공!")
        z, x = motor.get_position()
        print(f"현재 위치: Z={z}mm, X={x}mm")
    else:
        print("연결 실패 - Moonraker가 실행 중인지 확인하세요")
