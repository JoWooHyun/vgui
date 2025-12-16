"""
VERICOM DLP 3D Printer - ZIP Handler
ZIP 파일 처리 (썸네일 추출, 이미지 로드)
"""

import os
import zipfile
from typing import Optional, List, Tuple
from dataclasses import dataclass

from PySide6.QtGui import QPixmap, QImage


@dataclass
class ZipFileInfo:
    """ZIP 파일 정보"""
    path: str
    name: str
    size: int
    has_preview: bool
    layer_count: int


class ZipHandler:
    """
    프린트 ZIP 파일 처리 클래스

    ZIP 파일 구조:
    - preview_cropping.png: 미리보기 이미지
    - run.gcode: 프린트 파라미터
    - 0001.png ~ NNNN.png: 레이어 이미지
    """

    # 미리보기 이미지 우선순위
    PREVIEW_NAMES = [
        'preview_cropping.png',
        'preview.png',
        'thumbnail.png'
    ]

    @staticmethod
    def get_file_info(zip_path: str) -> Optional[ZipFileInfo]:
        """
        ZIP 파일 정보 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            ZipFileInfo 또는 None
        """
        try:
            if not os.path.exists(zip_path):
                return None

            with zipfile.ZipFile(zip_path, 'r') as z:
                namelist = z.namelist()

                # 미리보기 확인
                has_preview = any(
                    name in namelist
                    for name in ZipHandler.PREVIEW_NAMES
                )

                # 레이어 이미지 개수
                layer_count = sum(
                    1 for name in namelist
                    if name.endswith('.png') and name[:-4].isdigit()
                )

                return ZipFileInfo(
                    path=zip_path,
                    name=os.path.basename(zip_path),
                    size=os.path.getsize(zip_path),
                    has_preview=has_preview,
                    layer_count=layer_count
                )

        except Exception as e:
            print(f"[ZipHandler] 파일 정보 추출 오류: {e}")
            return None

    @staticmethod
    def extract_preview(zip_path: str) -> Optional[QPixmap]:
        """
        미리보기 이미지 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            QPixmap 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                namelist = z.namelist()

                # 미리보기 파일 찾기
                preview_name = None
                for name in ZipHandler.PREVIEW_NAMES:
                    if name in namelist:
                        preview_name = name
                        break

                # preview가 포함된 파일 찾기
                if not preview_name:
                    for name in namelist:
                        if 'preview' in name.lower() and name.endswith('.png'):
                            preview_name = name
                            break

                if preview_name:
                    data = z.read(preview_name)
                    qimage = QImage.fromData(data)

                    if not qimage.isNull():
                        return QPixmap.fromImage(qimage)

        except Exception as e:
            print(f"[ZipHandler] 미리보기 추출 오류: {e}")

        return None

    @staticmethod
    def extract_preview_bytes(zip_path: str) -> Optional[bytes]:
        """
        미리보기 이미지 바이트 데이터 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            이미지 바이트 데이터 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                namelist = z.namelist()

                for name in ZipHandler.PREVIEW_NAMES:
                    if name in namelist:
                        return z.read(name)

                for name in namelist:
                    if 'preview' in name.lower() and name.endswith('.png'):
                        return z.read(name)

        except Exception as e:
            print(f"[ZipHandler] 미리보기 추출 오류: {e}")

        return None

    @staticmethod
    def get_layer_image(zip_path: str, layer_index: int) -> Optional[QPixmap]:
        """
        특정 레이어 이미지 추출

        Args:
            zip_path: ZIP 파일 경로
            layer_index: 레이어 인덱스 (0부터 시작)

        Returns:
            QPixmap 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                namelist = z.namelist()

                # 다양한 파일명 형식 시도
                patterns = [
                    f"{layer_index:04d}.png",   # 0001.png
                    f"{layer_index:05d}.png",   # 00001.png
                    f"{layer_index + 1:04d}.png",  # 1-based
                    f"{layer_index}.png",        # 0.png
                ]

                for pattern in patterns:
                    if pattern in namelist:
                        data = z.read(pattern)
                        qimage = QImage.fromData(data)

                        if not qimage.isNull():
                            return QPixmap.fromImage(qimage)

        except Exception as e:
            print(f"[ZipHandler] 레이어 이미지 추출 오류: {e}")

        return None

    @staticmethod
    def get_layer_image_bytes(zip_path: str, layer_index: int) -> Optional[bytes]:
        """
        특정 레이어 이미지 바이트 데이터 추출

        Args:
            zip_path: ZIP 파일 경로
            layer_index: 레이어 인덱스

        Returns:
            이미지 바이트 데이터 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                namelist = z.namelist()

                patterns = [
                    f"{layer_index:04d}.png",
                    f"{layer_index:05d}.png",
                    f"{layer_index + 1:04d}.png",
                    f"{layer_index}.png",
                ]

                for pattern in patterns:
                    if pattern in namelist:
                        return z.read(pattern)

        except Exception as e:
            print(f"[ZipHandler] 레이어 이미지 추출 오류: {e}")

        return None

    @staticmethod
    def get_layer_list(zip_path: str) -> List[str]:
        """
        레이어 이미지 파일 목록 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            레이어 파일명 리스트 (정렬됨)
        """
        layers = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for name in z.namelist():
                    # 숫자.png 패턴 확인
                    base = name.replace('.png', '').replace('.PNG', '')
                    if name.lower().endswith('.png') and base.isdigit():
                        layers.append(name)

        except Exception as e:
            print(f"[ZipHandler] 레이어 목록 추출 오류: {e}")

        # 숫자순 정렬
        layers.sort(key=lambda x: int(x.replace('.png', '').replace('.PNG', '')))
        return layers

    @staticmethod
    def extract_gcode(zip_path: str) -> Optional[str]:
        """
        run.gcode 내용 추출

        Args:
            zip_path: ZIP 파일 경로

        Returns:
            G-code 문자열 또는 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for name in z.namelist():
                    if name.lower() == 'run.gcode':
                        return z.read(name).decode('utf-8', errors='ignore')

        except Exception as e:
            print(f"[ZipHandler] G-code 추출 오류: {e}")

        return None

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        파일 삭제

        Args:
            file_path: 삭제할 파일 경로

        Returns:
            성공 여부
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[ZipHandler] 파일 삭제됨: {file_path}")
                return True
        except Exception as e:
            print(f"[ZipHandler] 파일 삭제 오류: {e}")

        return False


# 테스트용
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        zip_path = sys.argv[1]

        # 파일 정보
        info = ZipHandler.get_file_info(zip_path)
        if info:
            print(f"파일: {info.name}")
            print(f"크기: {info.size / 1024:.1f} KB")
            print(f"미리보기: {'있음' if info.has_preview else '없음'}")
            print(f"레이어: {info.layer_count}개")

        # 레이어 목록
        layers = ZipHandler.get_layer_list(zip_path)
        print(f"\n레이어 파일: {len(layers)}개")
        if layers:
            print(f"  첫 번째: {layers[0]}")
            print(f"  마지막: {layers[-1]}")
    else:
        print("사용법: python zip_handler.py <zip_file>")
