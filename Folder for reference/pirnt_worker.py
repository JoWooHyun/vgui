"""
Mazic CERA DLP 3D Printer GUI - Print Worker
QThread 기반 프린팅 시퀀스 실행
"""

import os
import time
import zipfile
from typing import Optional, Callable
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

from controllers.motor_controller import MotorController
from controllers.dlp_controller import DLPController
from controllers.gcode_parser import GCodeParser, PrintParameters


class PrintState:
    """프린트 상태 상수"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    HOMING = "homing"
    PRINTING = "printing"
    EXPOSING = "exposing"
    LIFTING = "lifting"
    SWEEPING = "sweeping"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"


class PrintWorker(QThread):
    """프린팅 시퀀스 실행 워커"""
    
    # 시그널 정의
    progress_updated = Signal(int, int)         # (current_layer, total_layers)
    state_changed = Signal(str)                 # PrintState
    layer_started = Signal(int)                 # layer_index
    layer_completed = Signal(int)               # layer_index
    exposure_started = Signal(float)            # exposure_time
    print_completed = Signal()
    print_stopped = Signal()
    error_occurred = Signal(str)                # error_message
    image_ready = Signal(bytes)                 # 이미지 데이터 (프로젝터 윈도우로)
    clear_image = Signal()                      # 이미지 클리어
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 컨트롤러
        self.motor: Optional[MotorController] = None
        self.dlp: Optional[DLPController] = None
        self.parser = GCodeParser()
        
        # 프린트 작업 정보
        self.file_path = ""
        self.params: Optional[PrintParameters] = None
        self.print_params = {}  # GUI에서 수정된 파라미터
        
        # 상태 플래그
        self._state = PrintState.IDLE
        self._is_paused = False
        self._is_stopped = False
        self._current_layer = 0
        
        # 동기화
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
    
    # ==================== 설정 ====================
    
    def set_controllers(self, motor: MotorController, dlp: DLPController):
        """컨트롤러 설정"""
        self.motor = motor
        self.dlp = dlp
    
    def set_file(self, file_path: str, print_params: dict = None):
        """프린트 파일 설정
        
        Args:
            file_path: ZIP 파일 경로
            print_params: GUI에서 수정된 파라미터 (bladeSpeed, ledPower 등)
        """
        self.file_path = file_path
        self.print_params = print_params or {}
        
        # 파일 파싱
        self.params = self.parser.parse_zip_file(file_path)
        
        # GUI 파라미터 적용
        if 'bladeSpeed' in self.print_params:
            self.params.blade_speed = self.print_params['bladeSpeed']
        if 'ledPower' in self.print_params:
            self.params.led_power = self.print_params['ledPower']
    
    # ==================== 상태 관리 ====================
    
    def get_state(self) -> str:
        """현재 상태 반환"""
        return self._state
    
    def _set_state(self, state: str):
        """상태 변경 및 시그널 발생"""
        self._state = state
        self.state_changed.emit(state)
        print(f"[PrintWorker] 상태: {state}")
    
    def get_current_layer(self) -> int:
        """현재 레이어 반환"""
        return self._current_layer
    
    # ==================== 제어 ====================
    
    def pause(self):
        """일시정지"""
        print("[PrintWorker] 일시정지 요청")
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()
        self._set_state(PrintState.PAUSED)
    
    def resume(self):
        """재개"""
        print("[PrintWorker] 재개 요청")
        self._mutex.lock()
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self._set_state(PrintState.PRINTING)
    
    def stop(self):
        """정지"""
        print("[PrintWorker] 정지 요청")
        self._mutex.lock()
        self._is_stopped = True
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self._set_state(PrintState.STOPPING)
    
    def _check_pause(self):
        """일시정지 체크 (대기)"""
        self._mutex.lock()
        while self._is_paused and not self._is_stopped:
            self._pause_condition.wait(self._mutex)
        self._mutex.unlock()
    
    def _check_stop(self) -> bool:
        """정지 체크"""
        self._mutex.lock()
        stopped = self._is_stopped
        self._mutex.unlock()
        return stopped
    
    # ==================== 메인 실행 ====================
    
    def run(self):
        """프린팅 시퀀스 실행 (QThread.run)"""
        print("[PrintWorker] 프린팅 시작")
        
        # 초기화
        self._is_paused = False
        self._is_stopped = False
        self._current_layer = 0
        
        try:
            # 상태 검증
            if not self._validate():
                return
            
            # 초기화 단계
            self._set_state(PrintState.INITIALIZING)
            if not self._initialize():
                return
            
            # 홈잉
            self._set_state(PrintState.HOMING)
            if not self._do_homing():
                return
            
            # 프린팅 루프
            self._set_state(PrintState.PRINTING)
            if not self._print_layers():
                return
            
            # 완료
            self._finalize()
            self._set_state(PrintState.COMPLETED)
            self.print_completed.emit()
            print("[PrintWorker] 프린팅 완료")
            
        except Exception as e:
            print(f"[PrintWorker] 오류: {e}")
            self._set_state(PrintState.ERROR)
            self.error_occurred.emit(str(e))
            self._emergency_stop()
    
    def _validate(self) -> bool:
        """시작 전 검증"""
        if not self.motor:
            self.error_occurred.emit("모터 컨트롤러가 설정되지 않음")
            return False
        
        if not self.dlp:
            self.error_occurred.emit("DLP 컨트롤러가 설정되지 않음")
            return False
        
        if not self.params or self.params.total_layers == 0:
            self.error_occurred.emit("프린트 파일이 유효하지 않음")
            return False
        
        if not os.path.exists(self.file_path):
            self.error_occurred.emit("프린트 파일을 찾을 수 없음")
            return False
        
        return True
    
    def _initialize(self) -> bool:
        """초기화"""
        print("[PrintWorker] 초기화 중...")
        
        # 모터 연결 확인
        if not self.motor.check_connection():
            self.error_occurred.emit("Moonraker 연결 실패")
            return False
        
        # DLP 연결
        if not self.dlp.is_connected():
            if not self.dlp.connect():
                self.error_occurred.emit("NVR2+ 연결 실패")
                return False
        
        # 프로젝터 켜기
        if not self.dlp.projector_on():
            self.error_occurred.emit("프로젝터 켜기 실패")
            return False
        
        # 프로젝터 워밍업 대기
        time.sleep(1.0)
        
        # LED 밝기 설정
        self.dlp.set_led_brightness(self.params.led_power)
        
        return True
    
    def _do_homing(self) -> bool:
        """홈잉 시퀀스"""
        print("[PrintWorker] 홈잉 중...")
        
        if self._check_stop():
            return False
        
        # Z축 홈잉
        if not self.motor.home_z():
            self.error_occurred.emit("Z축 홈잉 실패")
            return False
        
        self.motor.wait_for_move_complete()
        
        if self._check_stop():
            return False
        
        # X축 홈잉
        if not self.motor.home_x():
            self.error_occurred.emit("X축 홈잉 실패")
            return False
        
        self.motor.wait_for_move_complete()
        
        # 초기 블레이드 스윕 (레진 평탄화)
        print("[PrintWorker] 초기 블레이드 스윕")
        self.motor.blade_sweep(self.params.blade_speed)
        
        return True
    
    def _print_layers(self) -> bool:
        """레이어별 프린팅"""
        total = self.params.total_layers
        
        try:
            with zipfile.ZipFile(self.file_path, 'r') as zf:
                image_files = self.parser._get_image_files(zf)
                
                for layer_idx in range(total):
                    # 정지 체크
                    if self._check_stop():
                        self._on_stopped()
                        return False
                    
                    # 일시정지 체크
                    self._check_pause()
                    
                    if self._check_stop():
                        self._on_stopped()
                        return False
                    
                    # 레이어 프린트
                    self._current_layer = layer_idx
                    self.layer_started.emit(layer_idx)
                    self.progress_updated.emit(layer_idx, total)
                    
                    # 이미지 로드
                    if layer_idx < len(image_files):
                        image_data = zf.read(image_files[layer_idx])
                    else:
                        print(f"[PrintWorker] 이미지 없음: 레이어 {layer_idx}")
                        continue
                    
                    # 레이어 실행
                    if not self._print_single_layer(layer_idx, image_data):
                        return False
                    
                    self.layer_completed.emit(layer_idx)
                    
        except Exception as e:
            print(f"[PrintWorker] 레이어 프린팅 오류: {e}")
            self.error_occurred.emit(str(e))
            return False
        
        return True
    
    def _print_single_layer(self, layer_idx: int, image_data: bytes) -> bool:
        """단일 레이어 프린팅
        
        시퀀스:
        1. Z축 레이어 높이로 이동
        2. X축 블레이드 스윕 (0 → 125 → 0)
        3. 이미지 투영
        4. LED ON (노출)
        5. LED OFF
        6. Z축 리프트
        """
        print(f"[PrintWorker] 레이어 {layer_idx + 1}/{self.params.total_layers}")
        
        # 노출 시간 결정
        if layer_idx < self.params.bottom_layer_count:
            exposure_time = self.params.bottom_exposure_time
        else:
            exposure_time = self.params.normal_exposure_time
        
        # 레이어 높이 계산
        layer_height = (layer_idx + 1) * self.params.layer_height
        
        # 1. Z축 레이어 높이로 이동
        self._set_state(PrintState.LIFTING)
        if not self.motor.move_z_absolute(layer_height, self.params.drop_speed):
            return False
        self.motor.wait_for_move_complete()
        
        if self._check_stop():
            return False
        
        # 2. 블레이드 스윕
        self._set_state(PrintState.SWEEPING)
        if not self.motor.blade_sweep(self.params.blade_speed):
            return False
        
        # 안정화 대기
        time.sleep(0.3)
        
        if self._check_stop():
            return False
        
        # 3. 이미지 투영
        self.image_ready.emit(image_data)
        time.sleep(0.1)  # 이미지 로딩 대기
        
        # 4. LED ON (노출)
        self._set_state(PrintState.EXPOSING)
        self.exposure_started.emit(exposure_time)
        
        if not self.dlp.led_on():
            return False
        
        # 노출 시간 대기 (중간에 정지 체크)
        start_time = time.time()
        while time.time() - start_time < exposure_time:
            if self._check_stop():
                self.dlp.led_off()
                return False
            time.sleep(0.05)
        
        # 5. LED OFF
        self.dlp.led_off()
        
        # 이미지 클리어
        self.clear_image.emit()
        
        # 6. Z축 리프트
        self._set_state(PrintState.LIFTING)
        if not self.motor.lift_z(self.params.lift_height, self.params.lift_speed):
            return False
        self.motor.wait_for_move_complete()
        
        self._set_state(PrintState.PRINTING)
        return True
    
    def _finalize(self):
        """프린팅 완료 후 정리"""
        print("[PrintWorker] 정리 중...")
        
        # LED 끄기
        if self.dlp:
            self.dlp.led_off()
        
        # 이미지 클리어
        self.clear_image.emit()
        
        # Z축 상승 (완료 위치)
        if self.motor:
            final_z = min(self.params.total_layers * self.params.layer_height + 20, 
                         self.motor.Z_MAX)
            self.motor.move_z_absolute(final_z, self.params.lift_speed)
            self.motor.wait_for_move_complete()
        
        # X축 홈
        if self.motor:
            self.motor.move_x_to_home()
        
        # 프로젝터는 계속 켜둠 (사용자가 결과물 확인)
    
    def _on_stopped(self):
        """정지 시 처리"""
        print("[PrintWorker] 프린팅 정지됨")
        self._emergency_stop()
        self._set_state(PrintState.IDLE)
        self.print_stopped.emit()
    
    def _emergency_stop(self):
        """비상 정지"""
        print("[PrintWorker] 비상 정지")
        
        # LED 끄기
        if self.dlp:
            self.dlp.led_off()
        
        # 이미지 클리어
        self.clear_image.emit()
        
        # 모터 정지
        if self.motor:
            self.motor.emergency_stop()


class CleanWorker(QThread):
    """트레이 청소 워커"""
    
    completed = Signal()
    progress = Signal(int)  # 남은 시간 (초)
    
    def __init__(self, dlp: DLPController, duration: float, parent=None):
        super().__init__(parent)
        self.dlp = dlp
        self.duration = duration
        self._is_stopped = False
    
    def stop(self):
        """정지"""
        self._is_stopped = True
    
    def run(self):
        """클리닝 실행"""
        print(f"[CleanWorker] 시작 ({self.duration}초)")
        
        # LED 켜기
        if self.dlp and self.dlp.is_connected():
            self.dlp.led_on()
        
        # 카운트다운
        remaining = int(self.duration)
        while remaining > 0 and not self._is_stopped:
            self.progress.emit(remaining)
            time.sleep(1)
            remaining -= 1
        
        # LED 끄기
        if self.dlp:
            self.dlp.led_off()
        
        if not self._is_stopped:
            self.completed.emit()
        
        print("[CleanWorker] 완료")


class ExposureWorker(QThread):
    """노출 테스트 워커"""
    
    completed = Signal()
    
    def __init__(self, dlp: DLPController, duration: float, parent=None):
        super().__init__(parent)
        self.dlp = dlp
        self.duration = duration
        self._is_stopped = False
    
    def stop(self):
        """정지"""
        self._is_stopped = True
    
    def run(self):
        """노출 실행"""
        print(f"[ExposureWorker] 시작 ({self.duration}초)")
        
        # LED 켜기
        if self.dlp and self.dlp.is_connected():
            self.dlp.led_on()
        
        # 대기
        start = time.time()
        while time.time() - start < self.duration and not self._is_stopped:
            time.sleep(0.1)
        
        # LED 끄기
        if self.dlp:
            self.dlp.led_off()
        
        if not self._is_stopped:
            self.completed.emit()
        
        print("[ExposureWorker] 완료")
