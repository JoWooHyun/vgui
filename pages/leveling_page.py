"""
VERICOM DLP 3D Printer GUI - Leveling Page
스테이지/블레이드 수평 맞추기 구분동작 시퀀스
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from styles.icons import Icons


# 단계 정의
STEPS = [
    {
        "icon": Icons.HOME_Z,
        "desc": "Z축에 Stage를 설치한 후\n고정하지 않고 두고 버튼을 누르세요.",
    },
    {
        "icon": Icons.HOME_X,
        "desc": "X축에 블레이드를 설치한 후\n고정 나사를 살짝 풀고 버튼을 누르세요.",
    },
    {
        "icon": Icons.X_MOVE,
        "desc": "블레이드가 가운데로 이동합니다.\n버튼을 누르세요.",
    },
]

DONE_DESC = "블레이드를 먼저 고정시키고\nZ축 Stage를 고정한 후 Done을 누르세요."


class LevelingPage(BasePage):
    """레벨링 페이지 (구분동작 시퀀스)"""

    # 모터 제어 시그널
    z_home = Signal()
    x_home = Signal()
    x_move = Signal(float, int)  # distance, speed

    def __init__(self, parent=None):
        super().__init__("Leveling", show_back=True, parent=parent)

        self._step = 0  # 0, 1, 2, 3(완료)
        self._busy = False
        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 10, 40, 20)

        main_layout.addStretch(2)

        # === 가운데 액션 버튼 ===
        btn_row = QHBoxLayout()
        self.btn_action = QPushButton()
        self.btn_action.setFixedSize(120, 120)
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_action_clicked)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_action)
        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        main_layout.addSpacing(10)

        # === 설명 텍스트 ===
        self.lbl_desc = QLabel()
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setFont(Fonts.body())
        self.lbl_desc.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background: transparent; border: none;
        """)
        main_layout.addWidget(self.lbl_desc)

        main_layout.addStretch(3)

        # === Done 버튼 ===
        done_row = QHBoxLayout()

        self.btn_done = QPushButton("Done")
        self.btn_done.setFixedSize(200, 60)
        self.btn_done.setCursor(Qt.PointingHandCursor)
        self.btn_done.setFont(Fonts.h2())
        self.btn_done.clicked.connect(self._on_done_clicked)

        done_row.addStretch()
        done_row.addWidget(self.btn_done)
        done_row.addStretch()

        main_layout.addLayout(done_row)

        self.content_layout.addLayout(main_layout)

        # 초기 UI
        self._update_ui()

    def _update_ui(self):
        """현재 step에 따라 UI 업데이트"""
        icon_size = 56

        if self._step < 3:
            step_info = STEPS[self._step]

            # 액션 버튼 아이콘
            pixmap = Icons.get_pixmap(step_info["icon"], icon_size, Colors.WHITE)
            self.btn_action.setIcon(Icons.get_icon(step_info["icon"], icon_size, Colors.WHITE))
            from PySide6.QtCore import QSize
            self.btn_action.setIconSize(QSize(icon_size, icon_size))

            # 액션 버튼 스타일 (활성)
            self.btn_action.setEnabled(True)
            self.btn_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.LG}px;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.CYAN_LIGHT};
                }}
                QPushButton:disabled {{
                    background-color: {Colors.BG_TERTIARY};
                    border-color: {Colors.BORDER};
                }}
            """)

            # 설명 텍스트
            self.lbl_desc.setText(step_info["desc"])

            # Done 버튼 비활성
            self.btn_done.setEnabled(False)
            self.btn_done.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_TERTIARY};
                    border: none;
                    border-radius: {Radius.LG}px;
                    color: {Colors.TEXT_DISABLED};
                }}
            """)
        else:
            # 완료 상태 (step 3)
            # 액션 버튼 비활성 (step 2 아이콘 유지)
            step_info = STEPS[2]
            self.btn_action.setIcon(Icons.get_icon(step_info["icon"], icon_size, Colors.TEXT_DISABLED))
            from PySide6.QtCore import QSize
            self.btn_action.setIconSize(QSize(icon_size, icon_size))
            self.btn_action.setEnabled(False)
            self.btn_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_TERTIARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: {Radius.LG}px;
                }}
            """)

            # 설명 텍스트
            self.lbl_desc.setText(DONE_DESC)

            # Done 버튼 활성
            self.btn_done.setEnabled(True)
            self.btn_done.setCursor(Qt.PointingHandCursor)
            self.btn_done.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.NAVY};
                    border: none;
                    border-radius: {Radius.LG}px;
                    color: {Colors.WHITE};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.NAVY_LIGHT};
                }}
            """)

    def _on_action_clicked(self):
        """액션 버튼 클릭"""
        if self._busy:
            return

        self._busy = True
        self.btn_action.setEnabled(False)

        if self._step == 0:
            self.z_home.emit()
        elif self._step == 1:
            self.x_home.emit()
        elif self._step == 2:
            self.x_move.emit(75.0, 10)

    def on_motor_finished(self):
        """모터 작업 완료 시 main.py에서 호출"""
        self._busy = False
        self._step += 1
        self._update_ui()

    def _on_done_clicked(self):
        """Done 버튼 클릭"""
        self.go_back.emit()

    def reset(self):
        """페이지 초기화 (진입 시 호출)"""
        self._step = 0
        self._busy = False
        self._update_ui()
