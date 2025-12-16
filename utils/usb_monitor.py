"""
VERICOM DLP 3D Printer - USB Monitor
USB 장치 감지 및 파일 스캔
"""

import os
import time
from typing import List, Optional, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer, Signal


@dataclass
class USBDevice:
    """USB 장치 정보"""
    path: str
    name: str
    files: List[str]


class USBMonitor(QObject):
    """
    USB 장치 모니터링 클래스

    /media 디렉토리를 폴링하여 USB 장치 감지
    지원 파일 형식: .zip, .dlp, .photon, .ctb
    """

    # 시그널
    devices_changed = Signal(list)  # List[USBDevice]
    device_connected = Signal(str)  # device path
    device_disconnected = Signal(str)  # device path

    # 지원 파일 확장자
    SUPPORTED_EXTENSIONS = ('.zip', '.dlp', '.photon', '.ctb')

    # Linux USB 마운트 경로
    MEDIA_PATH = "/media"

    def __init__(self, poll_interval: int = 2000, parent=None):
        """
        Args:
            poll_interval: 폴링 간격 (밀리초)
            parent: 부모 QObject
        """
        super().__init__(parent)

        self._poll_interval = poll_interval
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

        self._current_devices: dict = {}  # path -> USBDevice

        # Windows 테스트용 경로
        self._test_paths = []

    def start(self):
        """모니터링 시작"""
        self._timer.start(self._poll_interval)
        self._poll()  # 즉시 한 번 실행
        print(f"[USB] 모니터링 시작 (간격: {self._poll_interval}ms)")

    def stop(self):
        """모니터링 중지"""
        self._timer.stop()
        print("[USB] 모니터링 중지")

    def add_test_path(self, path: str):
        """테스트용 경로 추가 (Windows 개발용)"""
        if os.path.exists(path):
            self._test_paths.append(path)

    def get_devices(self) -> List[USBDevice]:
        """현재 감지된 장치 목록"""
        return list(self._current_devices.values())

    def get_all_files(self) -> List[str]:
        """모든 장치의 파일 목록"""
        files = []
        for device in self._current_devices.values():
            files.extend(device.files)
        return files

    def _poll(self):
        """USB 장치 폴링"""
        new_devices = self._scan_devices()

        # 변경 감지
        new_paths = set(new_devices.keys())
        old_paths = set(self._current_devices.keys())

        # 연결된 장치
        for path in new_paths - old_paths:
            print(f"[USB] 장치 연결됨: {path}")
            self.device_connected.emit(path)

        # 해제된 장치
        for path in old_paths - new_paths:
            print(f"[USB] 장치 해제됨: {path}")
            self.device_disconnected.emit(path)

        # 업데이트
        if new_devices != self._current_devices:
            self._current_devices = new_devices
            self.devices_changed.emit(list(new_devices.values()))

    def _scan_devices(self) -> dict:
        """USB 장치 스캔"""
        devices = {}

        # Linux /media 스캔
        if os.path.exists(self.MEDIA_PATH):
            devices.update(self._scan_media_path())

        # 테스트 경로 스캔
        for path in self._test_paths:
            if os.path.exists(path):
                files = self._scan_files(path)
                if files:
                    devices[path] = USBDevice(
                        path=path,
                        name=os.path.basename(path),
                        files=files
                    )

        return devices

    def _scan_media_path(self) -> dict:
        """
        /media 경로 스캔

        구조: /media/{user}/{device}/
        """
        devices = {}

        try:
            # /media 내 사용자 폴더
            for user in os.listdir(self.MEDIA_PATH):
                user_path = os.path.join(self.MEDIA_PATH, user)

                if not os.path.isdir(user_path):
                    continue

                # 사용자 폴더 내 장치 폴더
                for device in os.listdir(user_path):
                    device_path = os.path.join(user_path, device)

                    if not os.path.isdir(device_path):
                        continue

                    # 파일 스캔
                    files = self._scan_files(device_path)

                    if files:
                        devices[device_path] = USBDevice(
                            path=device_path,
                            name=device,
                            files=files
                        )

        except PermissionError:
            print("[USB] /media 접근 권한 없음")
        except Exception as e:
            print(f"[USB] 스캔 오류: {e}")

        return devices

    def _scan_files(self, directory: str) -> List[str]:
        """
        디렉토리 내 지원 파일 스캔

        Args:
            directory: 스캔할 디렉토리 경로

        Returns:
            파일 경로 리스트
        """
        files = []

        try:
            for entry in os.listdir(directory):
                entry_path = os.path.join(directory, entry)

                if os.path.isfile(entry_path):
                    # 확장자 확인
                    if entry.lower().endswith(self.SUPPORTED_EXTENSIONS):
                        files.append(entry_path)

        except PermissionError:
            pass
        except Exception as e:
            print(f"[USB] 파일 스캔 오류: {e}")

        # 이름순 정렬
        files.sort()
        return files


# 테스트용
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    monitor = USBMonitor(poll_interval=2000)

    # 시그널 연결
    monitor.devices_changed.connect(
        lambda devices: print(f"Devices: {[d.name for d in devices]}")
    )
    monitor.device_connected.connect(
        lambda path: print(f"Connected: {path}")
    )

    # Windows 테스트 경로 추가
    monitor.add_test_path("D:/test_prints")
    monitor.add_test_path(os.path.expanduser("~/Desktop"))

    monitor.start()

    # 10초 후 종료
    QTimer.singleShot(10000, app.quit)

    sys.exit(app.exec())
