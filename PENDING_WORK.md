# MAZIC CERA GUI - 미완성/보류 작업 정리

> 최종 업데이트: 2025-04-30
> 이 문서는 코드 내 TODO, 대화 중 합의된 향후 계획, 보류 중인 테스트 항목을 정리합니다.

---

## 1. 코드 내 TODO / 미완성 메서드

### 1.1 `main.py:846` - G-code 전송 스텁

```python
def _send_gcode(self, gcode: str):
    """G-code 전송 (Moonraker API)"""
    # TODO: Moonraker API 연동
    pass
```

- **상태**: 미사용 스텁 메서드
- **설명**: main.py에 직접 G-code 전송 기능을 넣으려 했으나, 현재는 `motor_controller.send_gcode()`를 통해 이미 동작 중
- **조치**: 삭제하거나, 향후 직접 G-code 전송이 필요할 때 구현

### 1.2 `pages/device_info_page.py:142` - UI 갱신 미구현

```python
def update_info(self, key: str, value: str):
    """정보 업데이트"""
    self._info[key] = value
    # TODO: UI 갱신
```

- **상태**: 메서드는 존재하나 UI 반영 코드 없음
- **설명**: 현재 Device Info 페이지는 하드코딩된 정보만 표시하므로 동적 업데이트 불필요
- **조치**: Klipper/Moonraker에서 실시간 정보를 가져올 때 구현 필요

### 1.3 `pages/manual_page.py:169` - set_value() 비활성화

```python
def set_value(self, value: float):
    """현재 값 업데이트 (사용 안함)"""
    pass
```

- **상태**: 의도적 비활성화
- **설명**: `AxisControlPanel`에 현재 축 위치를 표시하려던 메서드. 현재는 위치 표시 기능 없이 운영 중
- **조치**: 모터 현재 위치 실시간 표시 기능 추가 시 구현

---

## 2. 대화 중 합의된 향후 계획

### 2.1 Y축 → Klipper Extruder 이전 (가장 큰 변경)

> **배경**: 현재 Y축 모터가 레진 시린지 펌프로 사용 중이나, 향후 Y축은 다른 용도로 전환 예정. 레진 펌프 기능은 Klipper extruder로 이전.

**필요 작업:**

1. **printer.cfg 설정 추가**:
   ```ini
   [extruder]
   min_extrude_temp: 0          # 온도 제한 해제 (히터 없음)
   max_extrude_only_distance: 100  # 최대 토출 거리
   # step_pin, dir_pin 등 현재 Y축 모터 핀 이전
   ```

2. **motor_controller.py 수정**:
   - `extruder_move(distance, speed)` 메서드 추가 → `G1 E{dist} F{speed}`
   - `extruder_reset_position()` 메서드 추가 → `G92 E0`
   - 홈 동작 불필요 (extruder는 G28 미지원)

3. **print_worker.py 수정**:
   - `_motor_y_move()` → `_extruder_move()`로 전환
   - Y축 관련 로직을 extruder 명령으로 교체

4. **pages 수정**:
   - Manual 페이지: Y축 패널 → Extruder 패널로 변경
   - Setting 페이지: Y축 프라이밍 → Extruder 프라이밍으로 변경

5. **영향 범위**: motor_controller.py, print_worker.py, manual_page.py, setting_page.py, main.py

### 2.2 NVR2 Exposure 데스크탑 플리커 수정

> **배경**: Exposure 테스트 시 NVR2에서 데스크탑이 잠깐 보이는 현상. NVM에서는 발생하지 않음.

**현재 상태**: NVR2 테스트 프로그램의 **SET 버튼**으로 power-on 기본값(LED OFF 상태)을 저장하는 것을 먼저 시도하기로 합의.

**다음 단계:**
1. NVR2 테스트 프로그램에서 LED OFF, 패턴 OFF 상태로 SET 버튼 클릭
2. 전원 재투입 후 플리커 확인
3. **해결 안 되면**: 코드에서 이미지 표시 순서 변경 (이미지 먼저 프로젝터에 표시 → 이후 LED ON)

**관련 파일**: `windows/projector_window.py`, `main.py` (_start_exposure 메서드)

---

## 3. 미해결 버그/이슈 (코드 수정 보류 중)

### 3.1 일시정지 시 LED 상태 미처리

- **현상**: 노출(exposure) 중 일시정지(pause) 시 LED가 꺼지지 않음
- **위치**: `print_worker.py` - `_check_paused()` / `_wait_exposure()`
- **참고**: 정지(stop) 시에는 즉시 LED OFF 처리 완료 (`968e906`)
- **수정 방향**: `_wait_exposure()` 내부에서 pause 감지 시에도 LED OFF 호출
- **보류 이유**: 사용자가 "sleep은 괜찮다, 인터럽트 불필요"라고 했으나, pause 시 LED 상태는 별도 논의 필요

### 3.2 I2C 오류 17

- **현상**: NVR2+ I2C 통신 중 간헐적으로 error code 17 발생
- **위치**: `controllers/dlp_controller.py`
- **원인 추정**: USB 케이블 접촉 불량, NVR2 테스트 프로그램이 장치를 점유하고 있는 경우
- **조치**: USB 케이블 확인, 장치 관리자에서 Cypress USB 확인, NVR 테스트 프로그램 종료 후 재시도

### 3.3 레이어 인덱스 혼용

- **현상**: print_worker에서 0-based, progress_page에서 1-based로 혼용
- **위치**: `print_worker.py`, `pages/print_progress_page.py`
- **영향**: UI 표시에서 "0/100" 대신 "1/100"으로 보이는 것은 정상이나, 내부 로직 혼란 가능

---

## 4. 참고: Folder for reference/

`Folder for reference/` 디렉토리에 레거시 코드가 남아있음:

| 파일 | 내용 |
|------|------|
| `dlp_simple_slideshow.py` | 초기 DLP 슬라이드쇼 구현 |
| `file_preview_page.py` | 이전 버전 파일 미리보기 |
| `gcode_parser.py` | 이전 버전 G-code 파서 |
| `gui5.py` | 초기 GUI 프로토타입 |
| `pirnt_worker.py` | 초기 프린트 워커 (오타 포함 파일명) |

- **조치**: 정리 또는 삭제 가능. 현재 코드에 영향 없음.

---

## 5. TODO.md와의 관계

이 문서는 **코드 내부**에 남아있는 미완성 항목과 **대화 중 합의된 계획**에 집중합니다.
전체 향후 기능 계획과 리팩토링 목록은 [TODO.md](TODO.md)를 참조하세요.
