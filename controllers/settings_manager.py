"""
VERICOM DLP 3D Printer - Settings Manager
사용자 설정 저장 및 로드 (JSON)
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


# 설정 파일 경로
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


@dataclass
class PrintSettings:
    """프린트 관련 설정"""
    led_power: int = 43         # LED 파워 (9-100%, 1023=100%, 440=43%)
    blade_speed: int = 30       # Blade 속도 (10-100 mm/s)


@dataclass
class AppSettings:
    """앱 전체 설정"""
    print_settings: PrintSettings = None
    language: str = "en"        # 언어 설정
    theme: str = "Light"        # 테마 설정

    def __post_init__(self):
        if self.print_settings is None:
            self.print_settings = PrintSettings()


class SettingsManager:
    """설정 관리 클래스"""

    _instance: Optional['SettingsManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._settings = AppSettings()
        self._load()

    def _ensure_dir(self):
        """설정 디렉토리 확인/생성"""
        if not os.path.exists(SETTINGS_DIR):
            os.makedirs(SETTINGS_DIR)
            print(f"[Settings] 설정 디렉토리 생성: {SETTINGS_DIR}")

    def _load(self):
        """설정 파일 로드"""
        if not os.path.exists(SETTINGS_FILE):
            print("[Settings] 설정 파일 없음, 기본값 사용")
            return

        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # PrintSettings 로드
            print_data = data.get('print_settings', {})
            self._settings.print_settings = PrintSettings(
                led_power=print_data.get('led_power', 100),
                blade_speed=print_data.get('blade_speed', 30)
            )

            # 기타 설정 로드
            self._settings.language = data.get('language', 'en')
            self._settings.theme = data.get('theme', 'Light')

            print(f"[Settings] 설정 로드 완료: {SETTINGS_FILE}")
            print(f"  - LED Power: {self._settings.print_settings.led_power}%")
            print(f"  - Blade Speed: {self._settings.print_settings.blade_speed}mm/s")

        except Exception as e:
            print(f"[Settings] 설정 로드 실패: {e}")

    def save(self):
        """설정 파일 저장"""
        self._ensure_dir()

        try:
            data = {
                'print_settings': asdict(self._settings.print_settings),
                'language': self._settings.language,
                'theme': self._settings.theme
            }

            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"[Settings] 설정 저장 완료: {SETTINGS_FILE}")

        except Exception as e:
            print(f"[Settings] 설정 저장 실패: {e}")

    # ==================== LED Power ====================

    def get_led_power(self) -> int:
        """LED 파워 값 반환"""
        return self._settings.print_settings.led_power

    def set_led_power(self, value: int):
        """LED 파워 값 설정 (9-100%, 1023=100%)"""
        value = max(9, min(100, value))
        self._settings.print_settings.led_power = value
        self.save()

    # ==================== Blade Speed ====================

    def get_blade_speed(self) -> int:
        """Blade 속도 반환"""
        return self._settings.print_settings.blade_speed

    def set_blade_speed(self, value: int):
        """Blade 속도 설정 (10-100 mm/s)"""
        value = max(10, min(100, value))
        self._settings.print_settings.blade_speed = value
        self.save()

    # ==================== Language ====================

    def get_language(self) -> str:
        """언어 설정 반환"""
        return self._settings.language

    def set_language(self, lang: str):
        """언어 설정"""
        self._settings.language = lang
        self.save()

    # ==================== Theme ====================

    def get_theme(self) -> str:
        """테마 설정 반환"""
        return self._settings.theme

    def set_theme(self, theme: str):
        """테마 설정"""
        self._settings.theme = theme
        self.save()

    # ==================== Generic get/set ====================

    def get(self, key: str, default=None):
        """일반적인 설정 값 반환"""
        if key == "theme":
            return self._settings.theme
        elif key == "language":
            return self._settings.language
        elif key == "led_power":
            return self._settings.print_settings.led_power
        elif key == "blade_speed":
            return self._settings.print_settings.blade_speed
        return default

    def set(self, key: str, value):
        """일반적인 설정 값 저장"""
        if key == "theme":
            self._settings.theme = value
        elif key == "language":
            self._settings.language = value
        elif key == "led_power":
            self._settings.print_settings.led_power = value
        elif key == "blade_speed":
            self._settings.print_settings.blade_speed = value
        self.save()


# 싱글톤 인스턴스 접근
def get_settings() -> SettingsManager:
    """SettingsManager 싱글톤 인스턴스 반환"""
    return SettingsManager()
