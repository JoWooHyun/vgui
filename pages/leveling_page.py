"""
VERICOM DLP 3D Printer GUI - Leveling Page
스테이지/블레이드 수평 맞추기 (레벨링)
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Signal, Qt, QSize

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from styles.icons import Icons


# ==================== 레벨링 단계 정의 ====================
LEVEL_STEPS = [
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
LEVEL_DONE_DESC = "블레이드를 먼저 고정시키고\nZ축 Stage를 고정한 후\nDone을 누르세요."


class StepPanel(QFrame):
    """단계별 가이드 패널 (레벨링/프라이밍 공통)"""

    action_clicked = Signal()
    done_clicked = Signal()

    def __init__(self, title: str, steps: list, done_desc: str, parent=None):
        super().__init__(parent)

        self._steps = steps
        self._done_desc = done_desc
        self._step = 0
        self._max_step = len(steps)

        self.setStyleSheet(f"""
            StepPanel {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: {Radius.LG}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 15, 20, 15)

        # 타이틀
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFont(Fonts.h3())
        lbl_title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background: transparent; border: none;
        """)
        layout.addWidget(lbl_title)

        layout.addStretch(2)

        # 액션 버튼
        btn_row = QHBoxLayout()
        self.btn_action = QPushButton()
        self.btn_action.setFixedSize(100, 100)
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.clicked.connect(self.action_clicked.emit)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_action)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addSpacing(10)

        # 설명 텍스트
        self.lbl_desc = QLabel()
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setFont(Fonts.body())
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background: transparent; border: none;
        """)
        layout.addWidget(self.lbl_desc)

        layout.addStretch(3)

        # Done 버튼
        done_row = QHBoxLayout()
        self.btn_done = QPushButton("Done")
        self.btn_done.setFixedSize(160, 50)
        self.btn_done.setCursor(Qt.PointingHandCursor)
        self.btn_done.setFont(Fonts.h3())
        self.btn_done.clicked.connect(self.done_clicked.emit)

        done_row.addStretch()
        done_row.addWidget(self.btn_done)
        done_row.addStretch()
        layout.addLayout(done_row)

        self.update_ui()

    def update_ui(self):
        """현재 step에 따라 UI 업데이트"""
        icon_size = 48

        if self._step < self._max_step:
            step_info = self._steps[self._step]

            # 액션 버튼
            self.btn_action.setIcon(Icons.get_icon(step_info["icon"], icon_size, Colors.WHITE))
            self.btn_action.setIconSize(QSize(icon_size, icon_size))
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

            self.lbl_desc.setText(step_info["desc"])

            # Done 비활성
            self.btn_done.setEnabled(False)
            self.btn_done.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_TERTIARY};
                    border: none;
                    border-radius: {Radius.MD}px;
                    color: {Colors.TEXT_DISABLED};
                }}
            """)
        else:
            # 완료 상태
            last_icon = self._steps[-1]["icon"]
            self.btn_action.setIcon(Icons.get_icon(last_icon, icon_size, Colors.TEXT_DISABLED))
            self.btn_action.setIconSize(QSize(icon_size, icon_size))
            self.btn_action.setEnabled(False)
            self.btn_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_TERTIARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: {Radius.LG}px;
                }}
            """)

            self.lbl_desc.setText(self._done_desc)

            # Done 활성
            self.btn_done.setEnabled(True)
            self.btn_done.setCursor(Qt.PointingHandCursor)
            self.btn_done.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.NAVY};
                    border: none;
                    border-radius: {Radius.MD}px;
                    color: {Colors.WHITE};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.NAVY_LIGHT};
                }}
            """)

    def advance_step(self):
        """다음 단계로 진행"""
        self._step += 1
        self.update_ui()

    def set_action_enabled(self, enabled: bool):
        """액션 버튼 활성화/비활성화 (완료 상태면 무시)"""
        if not self.is_done:
            self.btn_action.setEnabled(enabled)

    def reset(self):
        """초기화"""
        self._step = 0
        self.update_ui()

    @property
    def step(self) -> int:
        return self._step

    @property
    def is_done(self) -> bool:
        return self._step >= self._max_step


class LevelingPage(BasePage):
    """레벨링 페이지"""

    # 레벨링 시그널
    z_home = Signal()
    x_home = Signal()
    x_move = Signal(float, int)  # distance, speed

    def __init__(self, parent=None):
        super().__init__("Leveling", show_back=True, parent=parent)

        self._busy = False
        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        split_layout = QHBoxLayout()
        split_layout.setSpacing(16)
        split_layout.setContentsMargins(20, 10, 20, 10)

        # 레벨링 패널 (가운데 정렬)
        self.level_panel = StepPanel("Leveling", LEVEL_STEPS, LEVEL_DONE_DESC)
        self.level_panel.action_clicked.connect(self._on_level_action)
        self.level_panel.done_clicked.connect(self._on_done)

        split_layout.addStretch()
        split_layout.addWidget(self.level_panel)
        split_layout.addStretch()

        self.content_layout.addLayout(split_layout)

    def _on_level_action(self):
        """레벨링 액션 버튼 클릭"""
        if self._busy:
            return

        self._busy = True
        self.level_panel.set_action_enabled(False)

        step = self.level_panel.step
        if step == 0:
            self.z_home.emit()
        elif step == 1:
            self.x_home.emit()
        elif step == 2:
            self.x_move.emit(75.0, 600)  # 10mm/s = 600mm/min

    def on_motor_finished(self):
        """모터 작업 완료 시 main.py에서 호출"""
        self._busy = False
        self.level_panel.advance_step()
        self.level_panel.set_action_enabled(True)

    def _on_done(self):
        """Done 버튼 클릭"""
        self.go_back.emit()

    def reset(self):
        """페이지 초기화 (진입 시 호출)"""
        self._busy = False
        self.level_panel.reset()
