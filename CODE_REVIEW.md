# MAZIC CERA GUI - 코드 리뷰

> 최종 업데이트: 2025-05-26

## 1. 프로젝트 아키텍처 요약

| 항목 | 내용 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| 패턴 | QStackedWidget 기반 페이지 네비게이션 |
| 스레딩 | QThread (PrintWorker, MotorWorker) |
| 상태 관리 | SettingsManager 싱글톤 (JSON 파일) |
| 하드웨어 | Moonraker REST API + CyUSBSerial I2C |
| 테마 | Colors 메타클래스 기반 동적 테마 |

### 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (QMainWindow)                 │
│            QStackedWidget (15 pages)                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Pages (BasePage)  ←→  Components (Header, NumericKeypad)│
│       ↑                      ↑                          │
│       │ Signal/Slot          │ Uses                     │
│       ↓                      ↓                          │
│  Controllers               Styles (Colors, Icons)       │
│  ├─ MotorController ──→ Moonraker REST API              │
│  ├─ DLPController ────→ CyUSBSerial I2C                 │
│  ├─ GCodeParser ──────→ ZIP file I/O                    │
│  ├─ SettingsManager ──→ data/settings.json              │
│  └─ ThemeManager ─────→ Colors metaclass                │
│                                                         │
│  Workers (QThread)                                      │
│  └─ PrintWorker ──→ Motor + DLP + GCode (background)   │
│                                                         │
│  Windows                                                │
│  └─ ProjectorWindow ──→ 2nd monitor (1920x1080)        │
│                                                         │
│  Utils                                                  │
│  ├─ KioskManager ──→ QApplication eventFilter           │
│  ├─ USBMonitor ────→ /media polling (2s)                │
│  ├─ ZipHandler ────→ ZIP extraction                     │
│  └─ TimeFormatter ─→ Time utilities                     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 설계 패턴 분석

### 2.1 페이지 네비게이션 (QStackedWidget)

- 인덱스 기반으로 단순하고 예측 가능
- Signal/Slot으로 페이지 간 결합도 낮음
- BasePage 상속으로 헤더/푸터 일관성 유지

```
PAGE_MAIN = 0         PAGE_DEVICE_INFO = 6    PAGE_THEME = 12
PAGE_TOOL = 1         PAGE_LANGUAGE = 7       PAGE_LEVELING = 13
PAGE_MANUAL = 2       PAGE_SERVICE = 8        PAGE_MATERIAL = 14
PAGE_PRINT = 3        PAGE_FILE_PREVIEW = 9
PAGE_EXPOSURE = 4     PAGE_PRINT_PROGRESS = 10
PAGE_SYSTEM = 5       PAGE_SETTING = 11
```

### 2.2 시그널/슬롯 패턴

모든 페이지 간 통신이 Signal을 통해 이루어짐 (직접 참조 없음):
```
page.go_back → main._go_to_page(PAGE_*)
page.z_move → main._move_z → motor.z_move_relative
worker.progress_updated → main._on_progress_updated → progress_page.update
worker.resin_empty → main._on_resin_empty → progress_page.show_resin_empty()
progress_page.refill_completed → main._on_refill_completed → worker.refill_resin()
progress_page.manual_feed_selected → main._on_manual_feed → worker.disable_y_dispensing()
```

### 2.3 싱글톤 패턴

- `SettingsManager`: `__new__` 기반 싱글톤, JSON 영속성
- `ThemeManager`: `__new__` 기반 싱글톤, Colors 메타클래스와 연동
- 스레드 안전하지 않음 (메인 스레드에서만 사용하므로 현재는 OK)

### 2.4 QThread 패턴

- `PrintWorker(QThread)`: `run()` 오버라이드, Mutex/WaitCondition으로 pause/stop
- `MotorWorker(QObject)`: `moveToThread()` 패턴, 개별 작업별 스레드 생성

---

## 3. 모듈별 코드 품질

### 3.1 main.py (~970줄)

**역할**: 앱 진입점, 페이지 관리, 하드웨어 연결, 비즈니스 로직

**강점**: 시그널 연결 체계적, 하드웨어 초기화와 UI 분리, closeEvent 리소스 정리

**개선 가능**:
- 파일 크기가 크다 → 비즈니스 로직을 별도 컨트롤러로 분리 고려
- LED 파워 변환 로직이 여러 곳에 분산

### 3.2 print_worker.py (~750줄)

**역할**: 프린트 시퀀스 전체 관리 (QThread)

**강점**:
- Mutex/WaitCondition 안전한 일시정지/정지
- Klipper shutdown 자동 복구, 시뮬레이션 모드
- 정지 시 즉시 LED OFF
- **3단계 토출 시퀀스** (`_dispense_3step()`): Push → Pull → Return
- **즉시 레진 소진 감지**: Push 직후 position ≤ 0이면 바로 사용자 알림
- **refill_resin()**: 주사기 교체 후 새 Y위치로 토출 재개

**개선 가능**:
- Y축 position 추적이 소프트웨어 카운터 기반 → drift 가능
- Pull/Return speed 기본값(600 mm/min) 매직넘버
- 연속 소진 시 재시도 제한 없음

### 3.3 settings_manager.py (~400줄)

**MaterialPreset dataclass (9개 필드)**:
- blade_speed, led_power
- y_dispense_distance, y_dispense_speed, y_dispense_delay
- y_pull_distance, y_pull_delay (Push-Pull 3단계)
- y_return_distance, y_return_delay (Push-Pull 3단계)

**강점**: dataclass 타입 안전성, 범위 클램핑, 소재별 프리셋 CRUD

### 3.4 motor_controller.py (~660줄)

**강점**: send_gcode 자동 재연결, M400 동기화, Klipper 상태 관리

**개선 가능**: HTTP 타임아웃 일부 하드코딩, 예외 처리 세분화 부족

### 3.5 dlp_controller.py (~490줄)

**강점**: CyUSBSerial 래핑 완비, 시뮬레이션 모드, 밝기 범위 검증

**알려진 이슈**: I2C 쓰기 오류 17 간헐적 발생

---

## 4. 3단계 레진 토출 시퀀스 (v5.0)

### 4.1 Push-Pull 토출 흐름

```
_dispense_3step(layer_idx, job, push_speed_override=0)

Step 1: Push (필수)
  └─ Y축 -distance 이동 (토출)
  └─ position ≤ 0? → 즉시 resin_empty → 사용자 선택 대기
     ├─ "주사기 리필" → refill_resin(new_y) → 토출 재개
     ├─ "수동배급" → disable_y_dispensing() → Y축 스킵, delay만 유지
     └─ "STOP" → 프린트 중지

Resin Delay (y_dispense_delay초 대기)

Step 2: Pull (y_pull_distance > 0일 때만)
  └─ Y축 +pull_distance 이동 (되돌리기)
  └─ speed = pull_distance / pull_delay × 60 (mm/min 자동 계산)

Step 3: Return (y_return_distance > 0일 때만)
  └─ Y축 -return_distance 이동 (다시 밀기)
  └─ speed = return_distance / return_delay × 60 (mm/min 자동 계산)
```

### 4.2 레진 소진 처리 UI

기존 ConfirmDialog 팝업 → **PrintProgressPage 내 버튼**으로 변경:

| 상태 | 표시 버튼 |
|------|----------|
| 레진 부족 감지 | "주사기 리필" (초록) + "수동배급" (시안) + "STOP" (빨강) |
| 주사기 리필 완료 | PAUSE + STOP (정상 복귀) |
| 수동배급 선택 | PAUSE + STOP, 타이틀 "Printing (수동배급)..." |

### 4.3 _motor_y_move() 반환값

```python
# 기존: bool (성공/실패)
# 변경: tuple(bool, float) (성공여부, 실제이동거리)
success, actual_distance = self._motor_y_move(distance, speed)
```

---

## 5. 미해결 이슈 및 기술 부채

### Critical

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 1 | Y축 프라이밍 절대 위치 파악 불가 | motor_controller, print_worker | 검토 중 |
| 2 | 레진 소진 감지: 소프트웨어 카운터 기반 | print_worker.py | 운영 중 |

### High

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 3 | I2C 쓰기 오류 17 (LED 밝기 간헐적 실패) | dlp_controller.py | 조사 필요 |
| 4 | 일시정지 시 LED 상태 미처리 | print_worker.py | 미수정 |

### Medium

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 5 | 레이어 인덱스 0-based vs 1-based 혼용 | print_worker, progress_page | 미수정 |
| 6 | PrintSettings와 MaterialPreset 필드 중복 | settings_manager.py | 리팩토링 대기 |

### Low

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 7 | 시뮬레이션 모드 불완전 | 전체 | 미수정 |
| 8 | 하드코딩된 매직 넘버 | print_worker.py | 상수화 고려 |
| 9 | 페이지 인덱스 수동 관리 | main.py | enum 도입 고려 |

### 해결 완료

| # | 이슈 | 해결 방법 | 버전 |
|---|------|-----------|------|
| ~~A~~ | 정지 시 LED 안 꺼짐 | `_wait_exposure()`에서 즉시 LED OFF | v4.2 |
| ~~B~~ | 레진 없이 평탄화 | 레벨링 전 초기 레진 토출 추가 | v4.2 |
| ~~C~~ | Exposure 정지 시 프로젝터 close | `clear_screen()`으로 변경 | v4.2 |
| ~~D~~ | X축 max position 불일치 | 코드에서 140으로 통일 | v4.2 |
| ~~E~~ | 예상 프린트 시간 부정확 | 레진/블레이드/레벨링 시간 반영 | v4.2 |
| ~~F~~ | 불완전 토출 시 블레이드/노출 진행 | Push 직후 즉시 resin_empty 감지 | v5.0 |
| ~~G~~ | 레진 소모 시 팝업 다이얼로그 사용성 | Progress 페이지 내 버튼으로 변경 | v5.0 |
| ~~H~~ | 단일 단계 토출만 지원 | Push-Pull 3단계 토출 구현 | v5.0 |

---

## 6. 프린트 시퀀스 분석

### 6.1 전체 흐름

```
파일 선택 (USB) → ZIP 검증 → 소재 선택 팝업 → 미리보기 (읽기전용) → 프린트 시작
    ↓
┌─── 초기화 ────────────────────────────────┐
│ 1. Z홈 → Z 0.1mm                          │
│ 2. X홈 → X 10mm (스탠바이)                 │
│ 3. Y축 프라이밍 위치 설정                    │
│ 4. 초기 레진 토출 (_dispense_3step)          │
│ 5. 레벨링 (X 0→140→0, cycles만큼 반복)      │
└────────────────────────────────────────────┘
    ↓
┌─── 메인 루프 (레이어별) ──────────────────────┐
│ 1. Z축 이동 (레이어 높이)                     │
│ 2. _dispense_3step() 3단계 레진 토출           │
│    ├─ Push → position ≤ 0? → 즉시 resin_empty │
│    ├─ Delay (y_dispense_delay초)              │
│    ├─ Pull (distance > 0이면)                 │
│    └─ Return (distance > 0이면)               │
│ 3. X축 블레이드 스윕 (10→140mm)               │
│ 4. 일시정지/정지 체크                          │
│ 5. 레이어 이미지 로드/표시 (3회 재시도)         │
│ 6. LED ON → 노출 대기 → LED OFF               │
│ 7. Z축 리프트 (+5mm)                          │
│ 8. X축 복귀 (140→10mm)                       │
└────────────────────────────────────────────────┘
    ↓
┌─── 정리 ────────────┐
│ LED OFF              │
│ 이미지 클리어         │
│ Klipper CANCEL_PRINT │
│ Klipper CLEAR_PAUSE  │
└──────────────────────┘
```

### 6.2 에러 처리

| 에러 상황 | 처리 |
|-----------|------|
| 모터 이동 실패 | error_occurred 시그널 → 프린트 중지 |
| 이미지 로드 실패 | 3회 재시도 → 실패 시 프린트 중지 |
| Y축 0mm 도달 (Push 직후) | 즉시 레진 부족 UI → 사용자 선택 |
| Klipper shutdown | 자동 firmware_restart → Z/X 재홈 |
| 사용자 정지 | LED 즉시 OFF → cleanup → IDLE |
| 노출 중 정지 | 즉시 LED OFF + 이미지 클리어 |

---

## 7. Y축 프라이밍 시스템 분석

### 7.1 현재 구현

```
Setting 페이지 PRIME 시작
  → SET_KINEMATIC_POSITION Y=0 (좌표 리셋)
  → +방향으로 이동 (레진 나올 때까지)
  → 프라이밍 위치 저장 (settings.json)
  → 출력 시: 저장된 위치부터 -방향 토출
  → Y ≤ 0: 즉시 레진 소진 감지 → 사용자 선택
```

### 7.2 문제점

1. **절대 위치 모름**: SET_KINEMATIC_POSITION은 상대 좌표만 설정
2. **주사기 크기 미대응**: 하드코딩된 한계
3. **재사용 주사기**: 남은 양 파악 불가
4. **물리적 한계 미감지**: Klipper는 G1 이동 중 엔드스톱 무시

---

## 8. 하드웨어 인터페이스 상세

### 8.1 입력값 제한 범위

| 페이지 | 항목 | 범위 | 단위 |
|--------|------|------|------|
| Material | Blade Speed | 1~100 | mm/s |
| Material | LED Power | 9~100 | % |
| Material | Y Dispense Distance | 0.1~5.0 | mm |
| Material | Y Dispense Speed | 1~15 | mm/s |
| Material | Y Dispense Delay | 0.5~300 | s |
| Material | Y Pull Distance | 0.0~5.0 | mm |
| Material | Y Pull Delay | 0.1~20.0 | s |
| Material | Y Return Distance | 0.0~5.0 | mm |
| Material | Y Return Delay | 0.1~20.0 | s |
| Setting | LED Power | 9~100 | % |
| Setting | Blade Speed | 1~100 | mm/s |
| Manual | 축 이동 거리 | 0.05~10.0 | mm |
| Manual | X축 속도 | 5~9999 | mm/s |

---

## 9. 스레드 안전성

### PrintWorker 동기화 메커니즘

```
_mutex (QMutex)          → _is_paused, _is_stopped 보호
_pause_condition (QWC)   → pause/resume 동기화
_resin_mutex (QMutex)    → 레진 대기 상태 보호
_resin_condition (QWC)   → resin_empty 사용자 응답 동기화
```

---

## 10. 결론 및 권장 사항

### 잘된 점
1. **Signal/Slot 아키텍처**: 페이지 간 결합도 낮음
2. **에러 처리**: 프린트 중 대부분의 에러 상황 처리
3. **테마 시스템**: 메타클래스 기반 런타임 테마 전환
4. **소재 프리셋**: dataclass + JSON 영속성
5. **Klipper 통합**: pause/resume/cancel/restart 안전 처리
6. **안전 정지**: 노출 중 즉시 LED OFF
7. **3단계 토출**: Push-Pull 시퀀스로 정밀한 레진 제어
8. **즉시 소진 감지**: Push 직후 감지하여 불완전 레이어 방지

### 우선 개선 사항
1. **Y축 프라이밍 절대 위치 파악** - 가장 시급
2. **일시정지 시 LED OFF** - 안전 문제
3. **main.py 분리** - 비즈니스 로직 별도 컨트롤러로
4. **LED 파워 변환 일원화** - % ↔ 91~1023
5. **Y축 position 주기적 동기화** - Klipper 실제 위치 비교
