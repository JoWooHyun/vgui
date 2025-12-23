"""
VERICOM DLP 3D Printer - Projector Window
두 번째 모니터(프로젝터)에 이미지를 표시하는 전체화면 윈도우
"""

import os
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor

# 로고 이미지 경로
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "VERICOM_LOGO.png")
# 테스트 이미지 경로 (1.png)
TEST_IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "1.png")


class ProjectorWindow(QMainWindow):
    """
    프로젝터 출력용 전체화면 윈도우

    두 번째 모니터에 레이어 이미지를 투영
    """

    # 프로젝터 해상도
    PROJECTOR_WIDTH = 1920
    PROJECTOR_HEIGHT = 1080

    def __init__(self, screen_index: int = 1, parent=None):
        """
        Args:
            screen_index: 모니터 인덱스 (0: 메인, 1: 프로젝터)
            parent: 부모 위젯
        """
        super().__init__(parent)

        self.screen_index = screen_index
        self._current_pixmap: QPixmap = None

        self._setup_ui()
        self._setup_window()

    def _setup_ui(self):
        """UI 설정"""
        # 이미지 표시용 라벨
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")

        self.setCentralWidget(self.image_label)

    def _setup_window(self):
        """윈도우 설정"""
        self.setWindowTitle("Projector Output")

        # 프레임 없는 윈도우
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # 태스크바에 표시 안 함
        )

        # 검은 배경
        self.setStyleSheet("background-color: black;")

        # 커서 숨김
        self.setCursor(Qt.BlankCursor)

    def show_on_screen(self, screen_index: int = None):
        """
        지정된 스크린에 전체화면으로 표시

        Args:
            screen_index: 스크린 인덱스 (None이면 self.screen_index 사용)
        """
        if screen_index is not None:
            self.screen_index = screen_index

        screens = QApplication.screens()

        if self.screen_index < len(screens):
            screen = screens[self.screen_index]
            geometry = screen.geometry()

            # 해당 스크린으로 이동 및 전체화면
            self.setGeometry(geometry)
            self.showFullScreen()

            print(f"[Projector] 스크린 {self.screen_index}에 표시: {geometry.width()}x{geometry.height()}")
        else:
            print(f"[Projector] 스크린 {self.screen_index} 없음, 기본 스크린 사용")
            self.showFullScreen()

    def show_image(self, pixmap: QPixmap):
        """
        이미지 표시

        Args:
            pixmap: 표시할 QPixmap
        """
        if pixmap is None or pixmap.isNull():
            self.clear_screen()
            return

        self._current_pixmap = pixmap

        # 윈도우 크기에 맞게 스케일링
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)

    def show_image_data(self, image_data: bytes):
        """
        바이트 데이터로 이미지 표시

        Args:
            image_data: PNG/JPG 이미지 바이트 데이터
        """
        qimage = QImage.fromData(image_data)
        if not qimage.isNull():
            pixmap = QPixmap.fromImage(qimage)
            self.show_image(pixmap)

    def clear_screen(self):
        """화면 클리어 (검은색)"""
        self._current_pixmap = None
        self.image_label.clear()
        self.image_label.setStyleSheet("background-color: black;")

    def show_white_screen(self):
        """흰색 화면 표시 (트레이 청소용)"""
        pixmap = QPixmap(self.PROJECTOR_WIDTH, self.PROJECTOR_HEIGHT)
        pixmap.fill(QColor(255, 255, 255))
        self.show_image(pixmap)

    def show_test_image(self, image_path: str = None):
        """
        테스트 이미지 파일 표시 (Setting 페이지 LED ON용)

        Args:
            image_path: 이미지 파일 경로 (None이면 1.png 사용)
        """
        path = image_path or TEST_IMAGE_PATH

        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.show_image(pixmap)
                print(f"[Projector] 테스트 이미지 표시: {path}")
            else:
                print(f"[Projector] 이미지 로드 실패: {path}")
                self.show_white_screen()
        else:
            print(f"[Projector] 이미지 파일 없음: {path}")
            self.show_white_screen()

    def show_test_pattern(self, pattern_type: str = "checker"):
        """
        테스트 패턴 표시

        Args:
            pattern_type: "checker", "ramp", "grid", "logo"
        """
        pixmap = self._create_test_pattern(pattern_type)
        self.show_image(pixmap)

    def _create_test_pattern(self, pattern_type: str) -> QPixmap:
        """테스트 패턴 생성"""
        width = self.PROJECTOR_WIDTH
        height = self.PROJECTOR_HEIGHT

        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)

        if pattern_type == "checker":
            # 체커보드 패턴
            cell_size = 100
            for y in range(0, height, cell_size):
                for x in range(0, width, cell_size):
                    if (x // cell_size + y // cell_size) % 2 == 0:
                        painter.fillRect(x, y, cell_size, cell_size, QColor(255, 255, 255))
                    else:
                        painter.fillRect(x, y, cell_size, cell_size, QColor(0, 0, 0))

        elif pattern_type == "ramp":
            # 그라데이션 패턴 (좌측에서 우측으로 어두워짐)
            for x in range(width):
                gray = 255 - int((x / width) * 255)  # 왼쪽 밝음 → 오른쪽 어두움
                painter.setPen(QColor(gray, gray, gray))
                painter.drawLine(x, 0, x, height)

        elif pattern_type == "grid":
            # 그리드 패턴
            pixmap.fill(QColor(0, 0, 0))
            painter.setPen(QColor(255, 255, 255))
            grid_size = 50
            for x in range(0, width, grid_size):
                painter.drawLine(x, 0, x, height)
            for y in range(0, height, grid_size):
                painter.drawLine(0, y, width, y)

        elif pattern_type == "logo":
            # 로고 패턴 (검은 배경 + 로고 200% 크기)
            pixmap.fill(QColor(0, 0, 0))
            if os.path.exists(LOGO_PATH):
                logo = QPixmap(LOGO_PATH)
                # 200% 크기로 스케일
                scaled_logo = logo.scaled(
                    logo.width() * 2,
                    logo.height() * 2,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                # 중앙 배치
                x = (width - scaled_logo.width()) // 2
                y = (height - scaled_logo.height()) // 2
                painter.drawPixmap(x, y, scaled_logo)

        else:
            # 기본: 흰색
            pixmap.fill(QColor(255, 255, 255))

        painter.end()
        return pixmap

    def resizeEvent(self, event):
        """리사이즈 시 이미지 재스케일링"""
        super().resizeEvent(event)

        if self._current_pixmap and not self._current_pixmap.isNull():
            self.show_image(self._current_pixmap)

    def keyPressEvent(self, event):
        """ESC 키로 닫기"""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


# 테스트용
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # 프로젝터 윈도우 생성
    projector = ProjectorWindow(screen_index=0)  # 테스트용으로 메인 스크린 사용
    projector.show_on_screen(0)

    # 테스트 패턴 표시
    projector.show_test_pattern("checker")

    # 3초 후 램프 패턴으로 변경
    QTimer.singleShot(3000, lambda: projector.show_test_pattern("ramp"))

    # 6초 후 흰색 화면
    QTimer.singleShot(6000, projector.show_white_screen)

    # 9초 후 종료
    QTimer.singleShot(9000, app.quit)

    sys.exit(app.exec())
