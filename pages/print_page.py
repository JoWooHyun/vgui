"""
VERICOM DLP 3D Printer GUI - Print Page (File Selection)
"""

import os
import zipfile
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Signal, Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QIcon

from pages.base_page import BasePage
from components.icon_button import IconButton
from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons
from styles.stylesheets import (
    BUTTON_FILE_ITEM_STYLE, BUTTON_FILE_ITEM_SELECTED_STYLE,
    get_button_nav_style
)


class FileItem(QFrame):
    """파일 아이템 위젯 (썸네일 위 + 파일명 아래)"""
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._filename = ""
        self._filepath = ""
        self._is_selected = False
        
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(200, 160)
        self._setup_ui()
        self._update_style()
    
    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # 썸네일 이미지
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setFixedSize(100, 100)
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(f"""
            background-color: {Colors.BG_TERTIARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
        """)
        
        # 파일명
        self.lbl_filename = QLabel()
        self.lbl_filename.setAlignment(Qt.AlignCenter)
        self.lbl_filename.setFont(Fonts.body_small())
        self.lbl_filename.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background-color: {Colors.BG_SECONDARY};
            border: none;
        """)
        self.lbl_filename.setFixedWidth(180)
        
        layout.addWidget(self.lbl_thumbnail, alignment=Qt.AlignCenter)
        layout.addWidget(self.lbl_filename, alignment=Qt.AlignCenter)
    
    def _update_style(self):
        """선택 상태에 따른 스타일"""
        if self._is_selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 3px solid {Colors.CYAN};
                    border-radius: 12px;
                }}
            """)
            # 파일명 색상도 변경
            self.lbl_filename.setStyleSheet(f"""
                color: {Colors.CYAN};
                background-color: {Colors.BG_SECONDARY};
                border: none;
                font-weight: 600;
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: 12px;
                }}
            """)
            # 파일명 기본 색상
            self.lbl_filename.setStyleSheet(f"""
                color: {Colors.TEXT_PRIMARY};
                background-color: {Colors.BG_SECONDARY};
                border: none;
            """)
    
    def _update_content(self):
        """내용 업데이트"""
        if self._filename:
            # 파일명 표시 (긴 경우 축약)
            display_name = self._filename
            if len(display_name) > 18:
                display_name = display_name[:15] + "..."
            self.lbl_filename.setText(display_name)
            
            # 썸네일 로드 시도
            thumbnail = self._load_thumbnail()
            if thumbnail:
                self.lbl_thumbnail.setPixmap(thumbnail)
            else:
                # 기본 아이콘
                self.lbl_thumbnail.setPixmap(
                    Icons.get_pixmap(Icons.FILE_TEXT, 48, Colors.NAVY)
                )
        else:
            self.lbl_filename.setText("")
            self.lbl_thumbnail.setPixmap(
                Icons.get_pixmap(Icons.FILE, 48, Colors.TEXT_DISABLED)
            )
    
    def _load_thumbnail(self) -> QPixmap:
        """ZIP 파일에서 썸네일 로드"""
        if not self._filepath:
            return None
        
        ext = os.path.splitext(self._filepath)[1].lower()
        if ext != '.zip':
            return None
        
        try:
            with zipfile.ZipFile(self._filepath, 'r') as z:
                # 미리보기 이미지 찾기
                preview_names = ['preview_cropping.png', 'preview.png', 'thumbnail.png']
                for name in preview_names:
                    if name in z.namelist():
                        data = z.read(name)
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        # 썸네일 크기에 맞게 스케일
                        return pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except:
            pass
        
        return None
    
    def set_file(self, filepath: str):
        """파일 설정"""
        self._filepath = filepath
        self._filename = os.path.basename(filepath) if filepath else ""
        self._update_content()
    
    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self._is_selected = selected
        self._update_style()
    
    def get_filepath(self) -> str:
        """파일 경로 반환"""
        return self._filepath
    
    def mousePressEvent(self, event):
        """클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def setEnabled(self, enabled: bool):
        """활성화 상태 설정"""
        super().setEnabled(enabled)
        if not enabled:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BG_TERTIARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: 12px;
                }}
            """)


class PrintPage(BasePage):
    """인쇄 파일 선택 페이지"""
    
    # 시그널
    file_selected = Signal(str)  # 파일 선택됨 (파일 경로)
    
    def __init__(self, parent=None):
        super().__init__("Print", show_back=True, parent=parent)
        
        self._file_paths = []       # 파일 경로 리스트
        self._current_page = 0      # 현재 페이지
        self._files_per_page = 6    # 페이지당 파일 수
        self._selected_index = None # 선택된 파일 인덱스
        
        self._setup_content()
        self._setup_polling()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        # 중앙 정렬을 위한 wrapper
        wrapper_layout = QVBoxLayout()
        wrapper_layout.addStretch()
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(16)
        
        # 파일 그리드 (3×2)
        file_grid = QGridLayout()
        file_grid.setSpacing(12)
        
        self._file_items = []
        for i in range(6):
            item = FileItem()
            item.clicked.connect(lambda idx=i: self._on_file_clicked(idx))
            self._file_items.append(item)
            
            row = i // 3
            col = i % 3
            file_grid.addWidget(item, row, col)
        
        # 네비게이션 버튼들
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(12)
        
        self.btn_up = QPushButton()
        self.btn_up.setFixedSize(80, 80)
        self.btn_up.setStyleSheet(get_button_nav_style())
        self.btn_up.setCursor(Qt.PointingHandCursor)
        self.btn_up.setIcon(Icons.get_icon(Icons.CHEVRON_UP, 32, Colors.NAVY))
        self.btn_up.setIconSize(QSize(32, 32))
        self.btn_up.clicked.connect(self._prev_page)
        
        self.btn_down = QPushButton()
        self.btn_down.setFixedSize(80, 80)
        self.btn_down.setStyleSheet(get_button_nav_style())
        self.btn_down.setCursor(Qt.PointingHandCursor)
        self.btn_down.setIcon(Icons.get_icon(Icons.CHEVRON_DOWN, 32, Colors.NAVY))
        self.btn_down.setIconSize(QSize(32, 32))
        self.btn_down.clicked.connect(self._next_page)
        
        self.btn_open = QPushButton()
        self.btn_open.setFixedSize(80, 80)
        self.btn_open.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: 12px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.NAVY_LIGHT};
            }}
            QPushButton:disabled {{
                background-color: {Colors.BG_TERTIARY};
                border: 2px solid {Colors.BORDER};
            }}
        """)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setIconSize(QSize(32, 32))
        self.btn_open.clicked.connect(self._on_open)
        self.btn_open.setEnabled(False)  # 초기에는 비활성화
        self._update_open_button()
        
        self.btn_home = QPushButton()
        self.btn_home.setFixedSize(80, 80)
        self.btn_home.setStyleSheet(get_button_nav_style())
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setIcon(Icons.get_icon(Icons.HOME, 32, Colors.NAVY))
        self.btn_home.setIconSize(QSize(32, 32))
        self.btn_home.clicked.connect(self.go_back.emit)
        
        nav_layout.addWidget(self.btn_up)
        nav_layout.addWidget(self.btn_down)
        nav_layout.addWidget(self.btn_open)
        nav_layout.addWidget(self.btn_home)
        
        main_layout.addLayout(file_grid, 1)
        main_layout.addLayout(nav_layout)
        
        wrapper_layout.addLayout(main_layout)
        wrapper_layout.addStretch()
        
        self.content_layout.addLayout(wrapper_layout)
    
    def _setup_polling(self):
        """USB 폴링 타이머 설정"""
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._scan_files)
        self._poll_timer.setInterval(2000)  # 2초마다
    
    def start_polling(self):
        """폴링 시작"""
        self._scan_files()
        self._poll_timer.start()
    
    def stop_polling(self):
        """폴링 중지"""
        self._poll_timer.stop()
    
    def _scan_files(self):
        """USB에서 파일 스캔"""
        self._file_paths = []
        
        # /media 디렉토리에서 마운트된 USB 찾기 (3단계 스캔)
        media_path = "/media"
        if os.path.exists(media_path):
            try:
                for user in os.listdir(media_path):
                    user_path = os.path.join(media_path, user)
                    if os.path.isdir(user_path):
                        try:
                            for device in os.listdir(user_path):
                                device_path = os.path.join(user_path, device)
                                if os.path.isdir(device_path):
                                    self._scan_directory(device_path)
                        except PermissionError:
                            continue
            except PermissionError:
                pass
        
        self._update_file_grid()
    
    def _scan_directory(self, path: str):
        """디렉토리 스캔 (DLP 프린터 파일 찾기)"""
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    # DLP 프린터 파일 확장자
                    if ext in ['.zip', '.dlp', '.photon', '.ctb']:
                        self._file_paths.append(item_path)
        except PermissionError:
            pass
    
    def _update_file_grid(self):
        """파일 그리드 업데이트"""
        start_idx = self._current_page * self._files_per_page
        
        for i, item in enumerate(self._file_items):
            file_idx = start_idx + i
            
            if file_idx < len(self._file_paths):
                item.set_file(self._file_paths[file_idx])
                item.setEnabled(True)
                item.set_selected(file_idx == self._selected_index)
            else:
                item.set_file("")
                item.setEnabled(False)
                item.set_selected(False)
        
        # 네비게이션 버튼 상태
        total_pages = max(1, (len(self._file_paths) + self._files_per_page - 1) // self._files_per_page)
        self.btn_up.setEnabled(self._current_page > 0)
        self.btn_down.setEnabled(self._current_page < total_pages - 1)
    
    def _on_file_clicked(self, grid_index: int):
        """파일 클릭 처리 - 선택만"""
        file_idx = self._current_page * self._files_per_page + grid_index
        
        if file_idx < len(self._file_paths):
            self._selected_index = file_idx
            self._update_file_grid()
            
            # Open 버튼 활성화
            self.btn_open.setEnabled(True)
            self._update_open_button()
    
    def _update_open_button(self):
        """Open 버튼 아이콘 업데이트"""
        if self.btn_open.isEnabled():
            self.btn_open.setIcon(Icons.get_icon(Icons.FOLDER_OPEN, 32, Colors.WHITE))
        else:
            self.btn_open.setIcon(Icons.get_icon(Icons.FOLDER_OPEN, 32, Colors.TEXT_DISABLED))
    
    def _on_open(self):
        """Open 버튼 클릭 - File Preview로 이동"""
        if self._selected_index is not None and self._selected_index < len(self._file_paths):
            self.file_selected.emit(self._file_paths[self._selected_index])
    
    def _prev_page(self):
        """이전 페이지"""
        if self._current_page > 0:
            self._current_page -= 1
            self._update_file_grid()
    
    def _next_page(self):
        """다음 페이지"""
        total_pages = max(1, (len(self._file_paths) + self._files_per_page - 1) // self._files_per_page)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._update_file_grid()
    
    def get_selected_file(self) -> str:
        """선택된 파일 경로 반환"""
        if self._selected_index is not None and self._selected_index < len(self._file_paths):
            return self._file_paths[self._selected_index]
        return None
    
    def showEvent(self, event):
        """페이지 표시 시"""
        super().showEvent(event)
        self.start_polling()
    
    def hideEvent(self, event):
        """페이지 숨김 시"""
        super().hideEvent(event)
        self.stop_polling()
