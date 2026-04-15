#!/usr/bin/env python3
"""
Y축 프라이밍 테스트 도구
SET_KINEMATIC_POSITION Y=0 → +방향 이동 테스트

Usage: python test_y_priming.py
"""

import sys
import time
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QGroupBox,
    QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

MOONRAKER_URL = "http://localhost:7125"


class GCodeThread(QThread):
    """G-code 실행 스레드 (M400 대기 포함)"""
    finished = Signal(bool, str)

    def __init__(self, gcode_command, wait_move=True):
        super().__init__()
        self.gcode = gcode_command
        self.wait_move = wait_move

    def run(self):
        try:
            url = f"{MOONRAKER_URL}/printer/gcode/script"

            # G-code 전송
            response = requests.post(
                url, json={"script": self.gcode}, timeout=120
            )
            if response.status_code != 200:
                self.finished.emit(False, f"HTTP {response.status_code}: {self.gcode}")
                return

            # M400으로 이동 완료 대기
            if self.wait_move:
                response = requests.post(
                    url, json={"script": "M400"}, timeout=120
                )
                if response.status_code != 200:
                    self.finished.emit(False, f"M400 실패: HTTP {response.status_code}")
                    return

            self.finished.emit(True, f"OK: {self.gcode}")

        except requests.exceptions.ConnectionError:
            self.finished.emit(False, f"Connection refused")
        except requests.exceptions.Timeout:
            self.finished.emit(False, f"Timeout")
        except Exception as e:
            self.finished.emit(False, f"Error: {e}")


class YPrimingTestWindow(QMainWindow):
    """Y축 프라이밍 테스트"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Y축 프라이밍 테스트")
        self.setFixedSize(500, 550)
        self.gcode_thread = None
        self.y_position = 0.0
        self.selected_distance = 10
        self.dist_buttons = []
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # 타이틀
        title = QLabel("Y축 프라이밍 테스트")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("background-color: #2c3e50; color: white; padding: 8px;")
        layout.addWidget(title)

        # 현재 위치 표시
        self.pos_label = QLabel(f"소프트웨어 위치: {self.y_position:.1f} mm")
        self.pos_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.pos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pos_label.setStyleSheet("color: #2ecc71; padding: 5px;")
        layout.addWidget(self.pos_label)

        # 1단계: 위치 리셋
        reset_group = QGroupBox("1단계: 위치 리셋")
        reset_layout = QHBoxLayout()

        btn_set_kin = QPushButton("SET_KINEMATIC_POSITION Y=0")
        btn_set_kin.setFixedHeight(40)
        btn_set_kin.setStyleSheet(
            "background-color: #9b59b6; color: white; font-weight: bold; font-size: 12px;"
        )
        btn_set_kin.clicked.connect(self.reset_position)
        self.btn_set_kin = btn_set_kin
        reset_layout.addWidget(btn_set_kin)

        btn_home = QPushButton("G28 Y (HOME)")
        btn_home.setFixedHeight(40)
        btn_home.setStyleSheet(
            "background-color: #f39c12; color: white; font-weight: bold; font-size: 12px;"
        )
        btn_home.clicked.connect(self.home_y)
        self.btn_home = btn_home
        reset_layout.addWidget(btn_home)

        reset_group.setLayout(reset_layout)
        layout.addWidget(reset_group)

        # 2단계: 거리 선택
        dist_group = QGroupBox("2단계: 이동 거리 (mm)")
        dist_layout = QHBoxLayout()
        for dist in [0.1, 1, 10]:
            btn = QPushButton(f"{dist}")
            btn.setFixedSize(80, 35)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, d=dist: self.select_distance(d))
            self.dist_buttons.append((dist, btn))
            dist_layout.addWidget(btn)
        dist_group.setLayout(dist_layout)
        layout.addWidget(dist_group)
        self.select_distance(10)

        # 속도
        speed_group = QGroupBox("속도 (mm/min)")
        speed_layout = QHBoxLayout()
        self.speed_input = QSpinBox()
        self.speed_input.setRange(1, 10000)
        self.speed_input.setValue(300)
        self.speed_input.setFixedWidth(100)
        speed_layout.addWidget(self.speed_input)
        speed_layout.addStretch()
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # 3단계: 이동
        move_group = QGroupBox("3단계: 이동 (리셋 후 +방향만 가능)")
        move_layout = QHBoxLayout()

        btn_plus = QPushButton("+ Y (토출방향)")
        btn_plus.setFixedHeight(40)
        btn_plus.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; font-size: 13px;"
        )
        btn_plus.clicked.connect(lambda: self.move_y(1))
        self.btn_plus = btn_plus

        btn_minus = QPushButton("- Y (복귀방향)")
        btn_minus.setFixedHeight(40)
        btn_minus.setStyleSheet(
            "background-color: #e74c3c; color: white; font-weight: bold; font-size: 13px;"
        )
        btn_minus.clicked.connect(lambda: self.move_y(-1))
        self.btn_minus = btn_minus

        move_layout.addWidget(btn_plus)
        move_layout.addWidget(btn_minus)
        move_group.setLayout(move_layout)
        layout.addWidget(move_group)

        # 직접 G-code
        direct_group = QGroupBox("직접 G-code 입력")
        direct_layout = QHBoxLayout()
        self.gcode_input = QLineEdit()
        self.gcode_input.setPlaceholderText("예: G91\\nG1 Y10 F300\\nG90")
        self.gcode_input.returnPressed.connect(self.send_custom)
        direct_layout.addWidget(self.gcode_input)
        btn_send = QPushButton("전송")
        btn_send.setFixedSize(60, 28)
        btn_send.clicked.connect(self.send_custom)
        self.btn_send = btn_send
        direct_layout.addWidget(btn_send)
        direct_group.setLayout(direct_layout)
        layout.addWidget(direct_group)

        # 로그
        self.log = QTextEdit()
        self.log.setMaximumHeight(150)
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.append("Y축 프라이밍 테스트 준비")
        self.log.append("1) SET_KINEMATIC_POSITION Y=0 또는 HOME 실행")
        self.log.append("2) + Y 버튼으로 토출 방향 이동 테스트")
        layout.addWidget(self.log)

        central.setLayout(layout)

    def select_distance(self, dist):
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

    def reset_position(self):
        self.send_gcode("SET_KINEMATIC_POSITION Y=0", wait_move=False)
        self.y_position = 0.0
        self.update_pos_label()

    def home_y(self):
        self.send_gcode("G28 Y", wait_move=True)
        self.y_position = 0.0
        self.update_pos_label()

    def move_y(self, direction):
        dist = self.selected_distance * direction
        speed = self.speed_input.value()
        gcode = f"G91\nG1 Y{dist} F{speed}\nG90"
        self.send_gcode(gcode, wait_move=True)
        self.y_position += dist
        self.update_pos_label()

    def update_pos_label(self):
        self.pos_label.setText(f"소프트웨어 위치: {self.y_position:.1f} mm")

    def send_custom(self):
        gcode = self.gcode_input.text().strip().replace("\\n", "\n")
        if gcode:
            self.send_gcode(gcode, wait_move=True)
            self.gcode_input.clear()

    def send_gcode(self, gcode, wait_move=True):
        if self.gcode_thread and self.gcode_thread.isRunning():
            self.log.append("이전 명령 실행 중...")
            return

        display = gcode.replace("\n", " | ")
        self.log.append(f">> {display}")
        self.set_buttons_enabled(False)

        self.gcode_thread = GCodeThread(gcode, wait_move)
        self.gcode_thread.finished.connect(self.on_finished)
        self.gcode_thread.start()

    def on_finished(self, success, message):
        if success:
            self.log.append(f"   OK")
        else:
            self.log.append(f"   FAIL: {message}")
        self.set_buttons_enabled(True)

    def set_buttons_enabled(self, enabled):
        self.btn_set_kin.setEnabled(enabled)
        self.btn_home.setEnabled(enabled)
        self.btn_plus.setEnabled(enabled)
        self.btn_minus.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        self.speed_input.setEnabled(enabled)
        for _, btn in self.dist_buttons:
            btn.setEnabled(enabled)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = YPrimingTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
