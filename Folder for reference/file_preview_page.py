"""
Mazic CERA DLP 3D Printer GUI - File Preview Page
"""

import os
import zipfile
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap

from pages.base_page import BasePage
from components.info_row import InfoRow
from components.editable_row import EditableRow
from components.confirm_dialog import DeleteConfirmDialog
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import BTN_DANGER_OUTLINE, BTN_ACCENT


class FilePreviewPage(BasePage):
    """파일 미리보기 페이지 - 파라미터 확인 및 설정"""
    
    start_print = Signal(str, dict)  # (file_path, print_params)
    file_deleted = Signal(str)  # file_path
    
    def __init__(self, parent=None):
        super().__init__(title="File Preview", show_back=True, parent=parent)
        
        self._file_path = ""
        self._file_info = {}
        self._print_params = {}
    
    def _setup_content(self):
        """컨텐츠 영역 설정"""
        # 좌우 레이아웃
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        
        # 좌측: 썸네일 + 파일명
        left_widget = QWidget()
        left_widget.setFixedWidth(180)
        left_widget.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        # 썸네일
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(150, 120)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet(f"""
            background-color: {Colors.GRAY_100};
            border: 2px solid {Colors.GRAY_200};
            border-radius: 8px;
        """)
        left_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignCenter)
        
        # 파일명
        self.filename_label = QLabel("filename.zip")
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setWordWrap(True)
        self.filename_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY_SMALL}px;
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            background-color: transparent;
            border: none;
        """)
        left_layout.addWidget(self.filename_label)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget)
        
        # 우측: 파라미터 정보
        right_widget = QWidget()
        right_widget.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # 정보 행들
        self.row_total_time = InfoRow("Total Time", "-- min", label_width=110)
        right_layout.addWidget(self.row_total_time)
        
        self.row_normal_exp = InfoRow("Normal Exp.", "-- sec", label_width=110)
        right_layout.addWidget(self.row_normal_exp)
        
        self.row_bottom_exp = InfoRow("Bottom Exp.", "-- sec", label_width=110)
        right_layout.addWidget(self.row_bottom_exp)
        
        self.row_layers = InfoRow("Total Layers", "--", label_width=110)
        right_layout.addWidget(self.row_layers)
        
        right_layout.addSpacing(8)
        
        # 편집 가능 행들 (단위 변환 적용)
        # Blade Speed: 표시는 mm/s, 내부는 mm/min (×50)
        self.edit_blade_speed = EditableRow(
            label="Blade Speed",
            value=30,  # 30 mm/s = 1500 mm/min
            unit="mm/s",
            min_value=2,
            max_value=200,
            decimals=0,
            label_width=110
        )
        self.edit_blade_speed.value_changed.connect(self._on_blade_speed_changed)
        right_layout.addWidget(self.edit_blade_speed)
        
        # LED Power: 표시는 %, 내부는 코드값 (×4.4)
        self.edit_led_power = EditableRow(
            label="LED Power",
            value=100,  # 100% = 440
            unit="%",
            min_value=50,
            max_value=200,
            decimals=0,
            label_width=110
        )
        self.edit_led_power.value_changed.connect(self._on_led_power_changed)
        right_layout.addWidget(self.edit_led_power)
        
        right_layout.addStretch()
        main_layout.addWidget(right_widget, 1)
        
        self.content_layout.addLayout(main_layout, 1)
        
        # 하단 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        
        btn_delete = QPushButton("Delete")
        btn_delete.setFixedSize(120, 50)
        btn_delete.setStyleSheet(BTN_DANGER_OUTLINE)
        btn_delete.clicked.connect(self._on_delete)
        button_layout.addWidget(btn_delete)
        
        button_layout.addStretch()
        
        btn_start = QPushButton("Start")
        btn_start.setFixedSize(140, 50)
        btn_start.setStyleSheet(BTN_ACCENT)
        btn_start.clicked.connect(self._on_start)
        button_layout.addWidget(btn_start)
        
        self.content_layout.addLayout(button_layout)
    
    def load_file(self, file_path: str, file_info: dict):
        """파일 로드"""
        self._file_path = file_path
        self._file_info = file_info
        
        # 파일명 표시
        filename = file_info.get('filename', os.path.basename(file_path))
        self.filename_label.setText(filename)
        
        # 썸네일 표시
        thumbnail = file_info.get('thumbnail', QPixmap())
        if thumbnail and not thumbnail.isNull():
            scaled = thumbnail.scaled(
                140, 110,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled)
        else:
            self.thumbnail_label.clear()
            self.thumbnail_label.setText("No Preview")
        
        # 파라미터 추출
        self._print_params = self._extract_parameters(file_path)
        
        # 정보 업데이트
        self._update_info_display()
    
    def _extract_parameters(self, file_path: str) -> dict:
        """ZIP 파일에서 프린트 파라미터 추출"""
        params = {
            'totalLayer': 0,
            'layerHeight': 0.05,
            'normalExposureTime': 3.0,
            'bottomLayerExposureTime': 5.0,
            'bottomLayerCount': 5,
            'normalLayerLiftHeight': 5.0,
            'normalLayerLiftSpeed': 60,
            'normalDropSpeed': 150,
            'bladeSpeed': 1500,  # mm/min (내부값)
            'ledPower': 440,     # 코드값 (내부값)
        }
        
        if not file_path.lower().endswith('.zip'):
            return params
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if 'run.gcode' in zf.namelist():
                    content = zf.read('run.gcode').decode('utf-8', errors='ignore')
                    
                    # G-code에서 파라미터 추출
                    patterns = {
                        'totalLayer': r';totalLayer:(\d+)',
                        'layerHeight': r';layerHeight:([\d.]+)',
                        'normalExposureTime': r';normalExposureTime:([\d.]+)',
                        'bottomLayerExposureTime': r';bottomLayerExposureTime:([\d.]+)',
                        'bottomLayerCount': r';bottomLayerCount:(\d+)',
                        'normalLayerLiftHeight': r';normalLayerLiftHeight:([\d.]+)',
                        'normalLayerLiftSpeed': r';normalLayerLiftSpeed:([\d.]+)',
                        'normalDropSpeed': r';normalDropSpeed:([\d.]+)',
                    }
                    
                    for key, pattern in patterns.items():
                        match = re.search(pattern, content)
                        if match:
                            value = match.group(1)
                            if '.' in value:
                                params[key] = float(value)
                            else:
                                params[key] = int(value)
        
        except Exception as e:
            print(f"Parameter extraction error: {e}")
        
        return params
    
    def _update_info_display(self):
        """정보 표시 업데이트"""
        # 총 시간 계산 (대략적)
        total_layers = self._print_params.get('totalLayer', 0)
        normal_exp = self._print_params.get('normalExposureTime', 3.0)
        bottom_exp = self._print_params.get('bottomLayerExposureTime', 5.0)
        bottom_count = self._print_params.get('bottomLayerCount', 5)
        
        # 대략적인 총 시간 (노출시간 + 이동시간 약 5초)
        total_seconds = (bottom_count * bottom_exp) + \
                       ((total_layers - bottom_count) * normal_exp) + \
                       (total_layers * 5)
        total_minutes = total_seconds / 60
        
        self.row_total_time.set_value(f"{total_minutes:.1f} min")
        self.row_normal_exp.set_value(f"{normal_exp:.1f} sec")
        self.row_bottom_exp.set_value(f"{bottom_exp:.1f} sec")
        self.row_layers.set_value(str(total_layers))
        
        # 편집 가능 값은 표시 단위로 변환
        blade_display = self._print_params.get('bladeSpeed', 1500) / 50  # mm/min → mm/s
        led_display = self._print_params.get('ledPower', 440) / 4.4  # 코드값 → %
        
        self.edit_blade_speed.set_value(blade_display)
        self.edit_led_power.set_value(led_display)
    
    def _on_blade_speed_changed(self, value: float):
        """블레이드 속도 변경"""
        # 표시값(mm/s) → 내부값(mm/min)
        self._print_params['bladeSpeed'] = int(value * 50)
    
    def _on_led_power_changed(self, value: float):
        """LED 파워 변경"""
        # 표시값(%) → 내부값(코드값)
        self._print_params['ledPower'] = int(value * 4.4)
    
    def _on_delete(self):
        """파일 삭제"""
        filename = self._file_info.get('filename', '')
        dialog = DeleteConfirmDialog(filename, self)
        
        if dialog.exec():
            try:
                os.remove(self._file_path)
                self.file_deleted.emit(self._file_path)
                self.go_back.emit()
            except Exception as e:
                print(f"File delete error: {e}")
    
    def _on_start(self):
        """프린트 시작"""
        self.start_print.emit(self._file_path, self._print_params)
    
    def get_print_params(self) -> dict:
        """현재 프린트 파라미터 반환"""
        return self._print_params.copy()
