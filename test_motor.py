#!/usr/bin/env python3
"""
VERICOM DLP 3D Printer - Motor Test Tool
X/Y/Z 축 개별 테스트 (Moonraker API 직접 통신)

Usage: python test_motor.py
"""

import sys
import time
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QGroupBox,
    QTabWidget, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

# Moonraker API URL
MOONRAKER_URL = "http://localhost:7125"


# ======================= G-code 스레드 =======================
class GCodeThread(QThread):
    """G-code 실행 스레드"""
    finished = Signal(bool, str)

    def __init__(self, gcode_command):
        super().__init__()
        self.gcode = gcode_command

    def run(self):
        try:
            url = f"{MOONRAKER_URL}/printer/gcode/script"
            response = requests.post(
                url,
                json={"script": self.gcode},
                timeout=120
            )
            if response.status_code == 200:
                time.sleep(0.5)
                self.finished.emit(True, f"OK: {self.gcode}")
            else:
                self.finished.emit(False, f"HTTP {response.status_code}: {self.gcode}")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, f"Connection refused: {self.gcode}")
        except requests.exceptions.Timeout:
            self.finished.emit(False, f"Timeout: {self.gcode}")
        except Exception as e:
            self.finished.emit(False, f"Error: {e}")


# ======================= 축 제어 탭 =======================
class AxisTab(QWidget):
    """축 제어 탭 (X, Y, Z 공통)"""

    def __init__(self, axis_name):
        super().__init__()
        self.axis = axis_name
        self.gcode_thread = None
        self.selected_distance = 10
        self.dist_buttons = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 제목
        title = QLabel(f"{self.axis}축 모터 제어")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 메인 컨텐츠
        main_layout = QHBoxLayout()

        # ===== 좌측: 이동 제어 =====
        left_layout = QVBoxLayout()

        # 거리 선택
        dist_group = QGroupBox("이동 거리 (mm)")
        dist_layout = QHBoxLayout()

        for dist in [1, 10, 100]:
            btn = QPushButton(f"{dist}")
            btn.setFixedSize(60, 35)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, d=dist: self.select_distance(d))
            self.dist_buttons.append((dist, btn))
            dist_layout.addWidget(btn)

        dist_group.setLayout(dist_layout)
        left_layout.addWidget(dist_group)

        # 초기 선택 (10mm)
        self.select_distance(10)

        # 속도 설정
        speed_group = QGroupBox("속도 (mm/min)")
        speed_layout = QHBoxLayout()

        self.speed_input = QSpinBox()
        self.speed_input.setRange(1, 10000)
        self.speed_input.setValue(300)
        self.speed_input.setFixedWidth(100)
        speed_layout.addWidget(self.speed_input)
        speed_layout.addStretch()

        speed_group.setLayout(speed_layout)
        left_layout.addWidget(speed_group)

        # 이동 버튼
        move_group = QGroupBox("이동")
        move_layout = QHBoxLayout()

        btn_neg = QPushButton(f"- {self.axis}")
        btn_neg.setFixedHeight(40)
        btn_neg.setStyleSheet(
            "background-color: #e74c3c; color: white; "
            "font-weight: bold; font-size: 13px;"
        )
        btn_neg.clicked.connect(lambda: self.move_axis(-1))
        self.btn_neg = btn_neg

        btn_home = QPushButton("HOME")
        btn_home.setFixedHeight(40)
        btn_home.setStyleSheet(
            "background-color: #f39c12; color: white; "
            "font-weight: bold; font-size: 13px;"
        )
        btn_home.clicked.connect(self.home_axis)
        self.btn_home = btn_home

        btn_pos = QPushButton(f"+ {self.axis}")
        btn_pos.setFixedHeight(40)
        btn_pos.setStyleSheet(
            "background-color: #2ecc71; color: white; "
            "font-weight: bold; font-size: 13px;"
        )
        btn_pos.clicked.connect(lambda: self.move_axis(1))
        self.btn_pos = btn_pos

        move_layout.addWidget(btn_neg)
        move_layout.addWidget(btn_home)
        move_layout.addWidget(btn_pos)

        move_group.setLayout(move_layout)
        left_layout.addWidget(move_group)

        # 직접 G-code 입력
        direct_group = QGroupBox("직접 G-code 입력")
        direct_layout = QHBoxLayout()

        self.gcode_input = QLineEdit()
        self.gcode_input.setPlaceholderText(f"예: G0 {self.axis}10 F300")
        self.gcode_input.returnPressed.connect(self.send_custom_gcode)
        direct_layout.addWidget(self.gcode_input)

        btn_send = QPushButton("전송")
        btn_send.setFixedSize(60, 28)
        btn_send.clicked.connect(self.send_custom_gcode)
        self.btn_send = btn_send
        direct_layout.addWidget(btn_send)

        direct_group.setLayout(direct_layout)
        left_layout.addWidget(direct_group)

        left_layout.addStretch()
        main_layout.addLayout(left_layout)

        layout.addLayout(main_layout)

        # 로그
        self.log = QTextEdit()
        self.log.setMaximumHeight(150)
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.append(f"{self.axis}축 제어 준비 완료")
        layout.addWidget(self.log)

        self.setLayout(layout)

    def select_distance(self, dist):
        """거리 선택"""
        self.selected_distance = dist
        for d, btn in self.dist_buttons:
            if d == dist:
                btn.setChecked(True)
                btn.setStyleSheet(
                    "background-color: #00BCD4; color: white; "
                    "font-weight: bold; font-size: 12px; border: none;"
                )
            else:
                btn.setChecked(False)
                btn.setStyleSheet(
                    "background-color: #ecf0f1; color: #333; "
                    "font-size: 12px; border: 1px solid #bdc3c7;"
                )

    def move_axis(self, direction):
        """축 상대 이동"""
        dist = self.selected_distance * direction
        speed = self.speed_input.value()
        gcode = f"G91\nG0 {self.axis}{dist} F{speed}\nG90"
        self.send_gcode(gcode)

    def home_axis(self):
        """축 홈"""
        self.send_gcode(f"G28 {self.axis}")

    def send_custom_gcode(self):
        """직접 입력 G-code 전송"""
        gcode = self.gcode_input.text().strip()
        if gcode:
            self.send_gcode(gcode)
            self.gcode_input.clear()

    def send_gcode(self, gcode):
        """G-code 전송 (스레드)"""
        if self.gcode_thread and self.gcode_thread.isRunning():
            self.log.append("이전 명령 실행 중...")
            return

        display = gcode.replace("\n", " | ")
        self.log.append(f">> {display}")
        self.set_buttons_enabled(False)

        self.gcode_thread = GCodeThread(gcode)
        self.gcode_thread.finished.connect(self.on_gcode_finished)
        self.gcode_thread.start()

    def on_gcode_finished(self, success, message):
        """G-code 완료"""
        if success:
            self.log.append(f"   OK")
        else:
            self.log.append(f"   FAIL: {message}")
        self.set_buttons_enabled(True)

    def set_buttons_enabled(self, enabled):
        """버튼 활성/비활성"""
        self.btn_neg.setEnabled(enabled)
        self.btn_home.setEnabled(enabled)
        self.btn_pos.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        for _, btn in self.dist_buttons:
            btn.setEnabled(enabled)
        self.speed_input.setEnabled(enabled)


# ======================= 메인 윈도우 =======================
class MotorTestWindow(QMainWindow):
    """모터 테스트 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motor Test Tool - VERICOM DLP")
        self.setFixedSize(600, 500)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # 상단 타이틀
        header = QHBoxLayout()

        title = QLabel("Motor Test Tool")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet(
            "background-color: #2c3e50; color: white; padding: 8px;"
        )
        header.addWidget(title, stretch=1)

        # 연결 테스트 버튼
        btn_test = QPushButton("연결 테스트")
        btn_test.setFixedSize(100, 35)
        btn_test.setStyleSheet(
            "background-color: #3498db; color: white; "
            "font-weight: bold; border: none;"
        )
        btn_test.clicked.connect(self.test_connection)
        header.addWidget(btn_test)

        layout.addLayout(header)

        # 탭 위젯
        self.tabs = QTabWidget()

        self.x_tab = AxisTab("X")
        self.y_tab = AxisTab("Y")
        self.z_tab = AxisTab("Z")

        self.tabs.addTab(self.x_tab, "X축")
        self.tabs.addTab(self.y_tab, "Y축")
        self.tabs.addTab(self.z_tab, "Z축")

        layout.addWidget(self.tabs)

        # 하단 상태바
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Moonraker:"))
        status_label = QLabel(MOONRAKER_URL)
        status_label.setStyleSheet("color: blue;")
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        central.setLayout(layout)

        # 기본 스타일
        self.setStyleSheet(
            "QPushButton {"
            "  background-color: #3498db;"
            "  color: white;"
            "  border: none;"
            "  padding: 5px;"
            "  border-radius: 3px;"
            "  font-weight: bold;"
            "  font-size: 11px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #2980b9;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #21618c;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #bdc3c7;"
            "  color: #7f8c8d;"
            "}"
            "QGroupBox {"
            "  font-weight: bold;"
            "  border: 2px solid #bdc3c7;"
            "  border-radius: 5px;"
            "  margin-top: 10px;"
            "  padding-top: 10px;"
            "  font-size: 11px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  left: 10px;"
            "  padding: 0 5px;"
            "}"
            "QTextEdit {"
            "  background-color: #ecf0f1;"
            "  border: 1px solid #bdc3c7;"
            "  border-radius: 3px;"
            "  font-size: 10px;"
            "}"
            "QLabel { font-size: 11px; }"
            "QLineEdit { font-size: 11px; padding: 3px; }"
            "QSpinBox { font-size: 11px; padding: 2px; }"
        )

    def test_connection(self):
        """Moonraker 연결 테스트"""
        try:
            response = requests.get(
                f"{MOONRAKER_URL}/printer/info", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                state = data.get("result", {}).get("state", "unknown")
                QMessageBox.information(
                    self, "연결 테스트",
                    f"Moonraker 연결 성공!\nKlipper 상태: {state}"
                )
            else:
                QMessageBox.warning(
                    self, "연결 테스트",
                    f"연결 실패: HTTP {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self, "연결 테스트",
                "Moonraker에 연결할 수 없습니다.\n"
                "Klipper가 실행 중인지 확인하세요."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "연결 테스트",
                f"연결 테스트 오류:\n{e}"
            )


# ======================= 메인 실행 =======================
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))

    window = MotorTestWindow()
    window.show()

    print("Motor Test Tool 시작")
    print(f"Moonraker URL: {MOONRAKER_URL}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
