"""
VERICOM DLP 3D Printer GUI - File Preview Page
파일 선택 후 미리보기 및 인쇄 시작
"""

import os
import zipfile
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QDialog, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap

from pages.base_page import BasePage
from components.numeric_keypad import NumericKeypad
from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons
from controllers.gcode_parser import extract_print_parameters
from controllers.settings_manager import get_settings, MaterialPreset


class InfoRow(QFrame):
    """정보 표시 행 (아이콘 + 값)"""

    def __init__(self, icon_svg: str, value: str = "-", parent=None):
        super().__init__(parent)

        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
                border-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 10, 0)
        layout.setSpacing(6)

        # 아이콘
        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(18, 18)
        self.lbl_icon.setPixmap(Icons.get_pixmap(icon_svg, 16, Colors.CYAN))
        self.lbl_icon.setStyleSheet(f"background: {Colors.BG_SECONDARY}; border: none;")

        # 값
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(Fonts.body_small())
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: {Colors.BG_SECONDARY};")

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_value, 1)

    def set_value(self, value: str):
        """값 설정"""
        self.lbl_value.setText(value)


class ReadOnlyRow(QFrame):
    """읽기 전용 정보 행 (라벨 + 값)"""

    def __init__(self, label: str, value: str = "-", parent=None):
        super().__init__(parent)

        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.lbl_label = QLabel(label)
        self.lbl_label.setFont(Fonts.body_small())
        self.lbl_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.lbl_label.setFixedWidth(110)

        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(Fonts.body_small())
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; border: none; font-weight: 600;")

        layout.addWidget(self.lbl_label)
        layout.addWidget(self.lbl_value, 1)

    def set_value(self, value: str):
        self.lbl_value.setText(value)


class MaterialSelectDialog(QDialog):
    """소재 선택 팝업 다이얼로그"""

    material_selected = Signal(str)  # 선택된 소재 이름

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected_name = ""

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(360, 340)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.CYAN};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # 제목
        lbl_title = QLabel("Select Material")
        lbl_title.setFont(Fonts.h3())
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(lbl_title)

        # 소재 버튼 리스트
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QWidget {{ background: transparent; }}
        """)
        list_widget = QWidget()
        self._list_layout = QVBoxLayout(list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)

        settings = get_settings()
        materials = settings.get_materials()
        selected = settings.get_selected_material()

        for mat in materials:
            btn = QPushButton(mat.name)
            btn.setFixedHeight(44)
            btn.setFont(Fonts.body())
            btn.setCursor(Qt.PointingHandCursor)

            if mat.name == selected:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.CYAN};
                        color: {Colors.WHITE};
                        border: none;
                        border-radius: 10px;
                        font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.BG_SECONDARY};
                        color: {Colors.TEXT_PRIMARY};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 10px;
                    }}
                    QPushButton:pressed {{ background-color: {Colors.BG_TERTIARY}; }}
                """)

            btn.clicked.connect(lambda checked, name=mat.name: self._on_select(name))
            self._list_layout.addWidget(btn)

        self._list_layout.addStretch()
        scroll.setWidget(list_widget)
        layout.addWidget(scroll, 1)

        # Cancel 버튼
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(44)
        btn_cancel.setFont(Fonts.body())
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
            QPushButton:pressed {{ background-color: {Colors.BG_TERTIARY}; }}
        """)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def _on_select(self, name: str):
        self._selected_name = name
        self.accept()

    def get_selected(self) -> str:
        return self._selected_name


class ConfirmDialog(QDialog):
    """확인 다이얼로그"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(350, 180)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 제목
        lbl_title = QLabel(title)
        lbl_title.setFont(Fonts.h3())
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")

        # 메시지
        lbl_message = QLabel(message)
        lbl_message.setFont(Fonts.body())
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setWordWrap(True)
        lbl_message.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")

        # 버튼들
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(120, 44)
        self.btn_cancel.setFont(Fonts.body())
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = QPushButton("Delete")
        self.btn_confirm.setFixedSize(120, 44)
        self.btn_confirm.setFont(Fonts.body())
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:pressed {{
                background-color: #D32F2F;
            }}
        """)
        self.btn_confirm.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_message)
        layout.addStretch()
        layout.addLayout(btn_layout)


class ZipErrorDialog(QDialog):
    """ZIP 파일 오류 다이얼로그"""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(360, 180)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.RED};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 에러 제목
        lbl_title = QLabel("파일 오류")
        lbl_title.setFont(Fonts.h2())
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"color: {Colors.RED}; background: transparent;")

        # 에러 메시지
        lbl_message = QLabel(message)
        lbl_message.setFont(Fonts.body())
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setWordWrap(True)
        lbl_message.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")

        # 확인 버튼
        btn_ok = QPushButton("확인")
        btn_ok.setFixedSize(120, 48)
        btn_ok.setFont(Fonts.body())
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: #B71C1C;
            }}
        """)
        btn_ok.clicked.connect(self.accept)

        # 버튼 중앙 정렬
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_message)
        layout.addStretch()
        layout.addLayout(btn_layout)


class FilePreviewPage(BasePage):
    """파일 미리보기 페이지"""

    # 시그널
    start_print = Signal(str, dict)  # (파일 경로, 파라미터)
    file_deleted = Signal(str)  # 삭제된 파일 경로

    def __init__(self, parent=None):
        super().__init__("File Preview", show_back=True, parent=parent)

        self._file_path = ""
        self._print_params = {}
        self._selected_material_name = ""
        self._material_preset = None  # MaterialPreset

        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        # 중앙 정렬 wrapper
        wrapper = QHBoxLayout()
        wrapper.addStretch()

        # 메인 콘텐츠
        content = QHBoxLayout()
        content.setSpacing(32)

        # === 왼쪽: 썸네일 ===
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignCenter)

        # 썸네일 프레임
        self.thumbnail_frame = QFrame()
        self.thumbnail_frame.setFixedSize(280, 220)
        self.thumbnail_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)

        thumb_layout = QVBoxLayout(self.thumbnail_frame)
        thumb_layout.setContentsMargins(10, 10, 10, 10)
        thumb_layout.setAlignment(Qt.AlignCenter)

        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setFixedSize(260, 200)
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(f"background: {Colors.BG_SECONDARY};")

        thumb_layout.addWidget(self.lbl_thumbnail)

        # 파일명
        self.lbl_filename = QLabel()
        self.lbl_filename.setFont(Fonts.h3())
        self.lbl_filename.setAlignment(Qt.AlignCenter)
        self.lbl_filename.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.lbl_filename.setFixedWidth(280)
        self.lbl_filename.setWordWrap(True)

        left_layout.addWidget(self.thumbnail_frame)
        left_layout.addSpacing(12)
        left_layout.addWidget(self.lbl_filename)

        # === 오른쪽: 정보 + 버튼 ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)

        # 선택된 소재 이름 표시
        self.lbl_material = QLabel("Material: -")
        self.lbl_material.setFont(Fonts.body())
        self.lbl_material.setAlignment(Qt.AlignCenter)
        self.lbl_material.setFixedHeight(28)
        self.lbl_material.setStyleSheet(f"""
            color: {Colors.CYAN};
            background-color: {Colors.BG_SECONDARY};
            border-radius: 6px;
            font-weight: 600;
        """)
        right_layout.addWidget(self.lbl_material)

        right_layout.addSpacing(4)

        # 읽기 전용 정보 행들 (아이콘 + 값) - gcode 파라미터
        self.info_rows = {}

        info_items = [
            (Icons.STACK, "totalLayer"),
            (Icons.TIMER, "estimatedPrintTime"),
            (Icons.RULER, "layerHeight"),
            (Icons.EXPOSURE_BOTTOM, "bottomLayerExposureTime"),
            (Icons.EXPOSURE_NORMAL, "normalExposureTime"),
        ]

        for icon_svg, key in info_items:
            row = InfoRow(icon_svg)
            self.info_rows[key] = row
            right_layout.addWidget(row)

        right_layout.addSpacing(4)

        # 소재 프리셋 값 읽기 전용 표시
        self.preset_rows = {}
        preset_items = [
            ("Blade Speed", "blade_speed", "mm/s"),
            ("LED Power", "led_power", "%"),
            ("Blade Cycles", "blade_cycles", "회"),
            ("Y Dispense", "y_dispense_distance", "mm"),
            ("Y Speed", "y_dispense_speed", "mm/s"),
            ("Y Delay", "y_dispense_delay", "s"),
        ]

        for label, key, unit in preset_items:
            row = ReadOnlyRow(label, "-")
            self.preset_rows[key] = (row, unit)
            right_layout.addWidget(row)

        right_layout.addStretch()

        # 버튼들
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        # Delete 버튼
        self.btn_delete = QPushButton()
        self.btn_delete.setFixedSize(140, 56)
        self.btn_delete.setText("Delete")
        self.btn_delete.setFont(Fonts.body())
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.RED};
                border: 2px solid {Colors.RED};
                border-radius: 12px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
            }}
        """)
        self.btn_delete.clicked.connect(self._on_delete)

        # Start 버튼
        self.btn_start = QPushButton()
        self.btn_start.setFixedSize(140, 56)
        self.btn_start.setText("Start")
        self.btn_start.setFont(Fonts.body())
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: {Colors.WHITE};
                border: none;
                border-radius: 12px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.CYAN_DARK};
            }}
        """)
        self.btn_start.clicked.connect(self._on_start)

        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_start)

        right_layout.addLayout(btn_layout)

        # 조립
        content.addLayout(left_layout)
        content.addLayout(right_layout)

        wrapper.addLayout(content)
        wrapper.addStretch()

        self.content_layout.addStretch()
        self.content_layout.addLayout(wrapper)
        self.content_layout.addStretch()

    def apply_material(self, preset: MaterialPreset):
        """소재 프리셋 적용 (읽기 전용 표시)"""
        self._material_preset = preset
        self._selected_material_name = preset.name
        self.lbl_material.setText(f"Material: {preset.name}")

        # 프리셋 값 표시
        values = {
            'blade_speed': preset.blade_speed,
            'led_power': preset.led_power,
            'blade_cycles': preset.blade_cycles,
            'y_dispense_distance': preset.y_dispense_distance,
            'y_dispense_speed': preset.y_dispense_speed,
            'y_dispense_delay': preset.y_dispense_delay,
        }
        for key, (row, unit) in self.preset_rows.items():
            val = values.get(key, 0)
            if val == int(val):
                row.set_value(f"{int(val)} {unit}")
            else:
                row.set_value(f"{val:.1f} {unit}")

    def set_file(self, file_path: str):
        """파일 설정 및 정보 표시"""
        self._file_path = file_path

        # 파일명 표시
        filename = os.path.basename(file_path)
        self.lbl_filename.setText(filename)

        # 파일 형식 확인
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.zip':
            self._load_zip_info(file_path)
        else:
            self._clear_info()

    def _load_zip_info(self, file_path: str):
        """ZIP 파일에서 정보 로드 (검증은 main.py에서 완료됨)"""
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                # 썸네일 로드
                preview_names = ['preview_cropping.png', 'preview.png', 'thumbnail.png']
                thumbnail_loaded = False

                for name in preview_names:
                    if name in z.namelist():
                        data = z.read(name)
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        scaled = pixmap.scaled(260, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.lbl_thumbnail.setPixmap(scaled)
                        thumbnail_loaded = True
                        break

                if not thumbnail_loaded:
                    self.lbl_thumbnail.setPixmap(Icons.get_pixmap(Icons.FILE, 64, Colors.TEXT_DISABLED))

            # gcode_parser를 사용하여 전체 파라미터 추출 (totalLayer 포함)
            self._print_params = extract_print_parameters(file_path)
            print(f"[FilePreview] 파라미터 추출 완료: totalLayer={self._print_params.get('totalLayer', 0)}")
            self._update_info_display()

        except Exception as e:
            print(f"ZIP 파일 로드 오류: {e}")
            self._clear_info()
            self.lbl_thumbnail.setPixmap(Icons.get_pixmap(Icons.FILE, 64, Colors.TEXT_DISABLED))

    def _update_info_display(self):
        """정보 표시 업데이트"""
        p = self._print_params

        # Total Layer
        self.info_rows['totalLayer'].set_value(f"{p.get('totalLayer', 0)}")

        # 예상 시간 (초 -> 분, 소수점 버림)
        est_seconds = p.get('estimatedPrintTime', 0)
        est_minutes = int(est_seconds / 60)
        if est_minutes >= 60:
            hours = est_minutes // 60
            mins = est_minutes % 60
            self.info_rows['estimatedPrintTime'].set_value(f"{hours}h {mins}m")
        else:
            self.info_rows['estimatedPrintTime'].set_value(f"{est_minutes} min")

        # Layer Height
        layer_height = p.get('layerHeight', 0)
        self.info_rows['layerHeight'].set_value(f"{layer_height} mm")

        # 노출 시간
        self.info_rows['bottomLayerExposureTime'].set_value(f"{p.get('bottomLayerExposureTime', 0)} sec")
        self.info_rows['normalExposureTime'].set_value(f"{p.get('normalExposureTime', 0)} sec")

    def _clear_info(self):
        """정보 초기화"""
        self._print_params = {}
        for row in self.info_rows.values():
            row.set_value("-")

    def _on_delete(self):
        """Delete 버튼 클릭"""
        if not self._file_path:
            return

        filename = os.path.basename(self._file_path)
        dialog = ConfirmDialog(
            "Delete File",
            f"Are you sure you want to delete\n'{filename}'?",
            self
        )

        if dialog.exec() == QDialog.Accepted:
            try:
                os.remove(self._file_path)
                self.file_deleted.emit(self._file_path)
                self.go_back.emit()
            except Exception as e:
                print(f"파일 삭제 오류: {e}")

    def _on_start(self):
        """Start 버튼 클릭"""
        if not self._file_path or not self._material_preset:
            return

        preset = self._material_preset
        full_params = {
            **self._print_params,
            'bladeSpeed': preset.blade_speed * 60,  # mm/s → mm/min
            'ledPower': preset.led_power,
            'bladeCycles': preset.blade_cycles,
            'yDispenseDistance': preset.y_dispense_distance,
            'yDispenseSpeed': preset.y_dispense_speed * 60,  # mm/s → mm/min
            'yDispenseDelay': preset.y_dispense_delay,
            'levelingCycles': preset.leveling_cycles,
            'liftHeight': preset.lift_height,
            'dropSpeed': preset.drop_speed,
            'materialName': preset.name,
        }
        self.start_print.emit(self._file_path, full_params)

    def get_file_path(self) -> str:
        """현재 파일 경로 반환"""
        return self._file_path

    def get_print_params(self) -> dict:
        """프린트 파라미터 반환"""
        if not self._material_preset:
            return self._print_params
        preset = self._material_preset
        return {
            **self._print_params,
            'bladeSpeed': preset.blade_speed * 60,
            'ledPower': preset.led_power,
            'bladeCycles': preset.blade_cycles,
            'yDispenseDistance': preset.y_dispense_distance,
            'yDispenseSpeed': preset.y_dispense_speed * 60,
            'yDispenseDelay': preset.y_dispense_delay,
        }
