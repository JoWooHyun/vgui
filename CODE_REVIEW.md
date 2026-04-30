# MAZIC CERA GUI - 코드 리뷰

> 최종 업데이트: 2025-04-30

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

### 3.2 print_worker.py (~700줄)

**역할**: 프린트 시퀀스 전체 관리 (QThread)

**강점**: Mutex/WaitCondition 안전한 일시정지/정지, Klipper shutdown 자동 복구, 시뮬레이션 모드, 정지 시 즉시 LED OFF

**개선 가능**:
- `_process_layer()` 130줄+ → 블레이드/노출/Y축 로직 분리 고려
- 레진 소진 감지가 소프트웨어 카운터(91mm) 기반 → 물리 센서 감지로 전환 필요

### 3.3 settings_manager.py (~450줄)

**강점**: MaterialPreset dataclass 타입 안전성, 범위 클램핑

**개선 가능**: PrintSettings와 MaterialPreset 필드 일부 중복

### 3.4 motor_controller.py (~660줄)

**강점**: send_gcode 자동 재연결, M400 동기화, Klipper 상태 관리

**개선 가능**: HTTP 타임아웃 일부 하드코딩, 예외 처리 세분화 부족

### 3.5 dlp_controller.py (~490줄)

**강점**: CyUSBSerial 래핑 완비, 시뮬레이션 모드, 밝기 범위 검증

**알려진 이슈**: I2C 쓰기 오류 17 간헐적 발생 (USB 연결 불안정 또는 장치 점유 문제)

---

## 4. 미해결 이슈 및 기술 부채

### Critical

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 1 | Y축 프라이밍 절대 위치 파악 불가 | motor_controller, print_worker | 검토 중 |
| 2 | 레진 소진 감지: 소프트웨어 카운터 → 물리 센서 전환 필요 | print_worker.py | 검토 중 |

### High

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 3 | I2C 쓰기 오류 17 (LED 밝기 간헐적 실패) | dlp_controller.py | 조사 필요 |
| 4 | 일시정지 시 LED 상태 미처리 (LED 켜진 채로 일시정지) | print_worker.py | 미수정 |

### Medium

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 5 | 레이어 인덱스 0-based vs 1-based 혼용 | print_worker, progress_page | 미수정 |
| 6 | PrintSettings와 MaterialPreset 필드 중복 | settings_manager.py | 리팩토링 대기 |

### Low

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 7 | 시뮬레이션 모드 불완전 | 전체 | 미수정 |
| 8 | 하드코딩된 매직 넘버 | 전체 | 미수정 |
| 9 | 페이지 인덱스 수동 관리 | main.py | enum 도입 고려 |
| 10 | MotorWorker 스레드 빈번 생성/소멸 | main.py | ThreadPool 고려 |

### 해결 완료

| # | 이슈 | 해결 방법 | 커밋 |
|---|------|-----------|------|
| ~~A~~ | 정지 시 LED 안 꺼짐 | `_wait_exposure()`에서 즉시 LED OFF | `968e906` |
| ~~B~~ | 레진 없이 평탄화 | 레벨링 전 초기 레진 토출 추가 | `bf08cb5` |
| ~~C~~ | Exposure 정지 시 프로젝터 close | `clear_screen()`으로 변경, 페이지 나갈 때만 close | `a6b44a5` |
| ~~D~~ | X축 max position 불일치 (150 vs 140) | 코드에서 140으로 통일 | `6af0ccd` |
| ~~E~~ | 예상 프린트 시간 부정확 | 레진/블레이드/레벨링 시간 모두 반영 | `ab06063` |

---

## 5. 프린트 시퀀스 분석

### 5.1 전체 흐름

```
파일 선택 (USB) → ZIP 검증 → 소재 선택 팝업 → 미리보기 (읽기전용) → 프린트 시작
    ↓
┌─── 초기화 ────────────────────────────────┐
│ 1. Z홈 → Z 0.1mm                          │
│ 2. X홈 → X 10mm (스탠바이)                 │
│ 3. Y축 프라이밍 위치 설정                    │
│ 4. 초기 레진 토출 (프라이밍 설정 시)          │
│ 5. 레벨링 (X 0→140→0, cycles만큼 반복)      │
└────────────────────────────────────────────┘
    ↓
┌─── 메인 루프 (레이어별) ──────────────────────┐
│ 1. Z축 이동 (레이어 높이 = layerHeight × N)   │
│ 2. Y축 레진 토출 (dispense_distance만큼)       │
│    └─ Y ≤ 0 감지 시 resin_empty 알림          │
│ 3. 레진 대기 (dispense_delay초)                │
│ 4. X축 블레이드 스윕 (10→140mm, oneway)        │
│    └─ blade_cycles만큼 추가 반복               │
│ 5. 일시정지/정지 체크                          │
│ 6. 레이어 이미지 로드/표시 (3회 재시도)         │
│ 7. LED ON → 노출 대기                         │
│    └─ 정지 요청 시 즉시 LED OFF                │
│ 8. LED OFF → 이미지 클리어                     │
│ 9. Z축 리프트 (+5mm)                          │
│ 10. X축 복귀 (140→10mm)                       │
└────────────────────────────────────────────────┘
    ↓
┌─── 정리 ────────────┐
│ LED OFF              │
│ 이미지 클리어         │
│ Klipper CANCEL_PRINT │
│ Klipper CLEAR_PAUSE  │
└──────────────────────┘
```

### 5.2 에러 처리

| 에러 상황 | 처리 |
|-----------|------|
| 모터 이동 실패 | error_occurred 시그널 → 프린트 중지 |
| 이미지 로드 실패 | 3회 재시도 (500ms간격) → 실패 시 프린트 중지 |
| Y축 0mm 도달 | 레진 부족 알림 → 사용자 선택 (Y축 비활성화 계속/중지) |
| Klipper shutdown | 자동 firmware_restart → Z/X 재홈 |
| 사용자 정지 | STOPPING 상태 → LED 즉시 OFF → cleanup → IDLE |
| 노출 중 정지 | `_wait_exposure()`에서 즉시 LED OFF + 이미지 클리어 |

---

## 6. Y축 프라이밍 시스템 분석

### 6.1 현재 구현

```
Setting 페이지 PRIME 시작
  → SET_KINEMATIC_POSITION Y=0  (현재 위치를 0으로 설정, 모터 안 움직임)
  → +방향으로 소량 이동 (레진 나올 때까지)
  → 프라이밍 위치 저장 (settings.json)
  → 출력 시: 저장된 위치에서 시작, -방향으로 토출
  → Y ≤ 0 시: 소프트웨어 카운터로 레진 소진 감지
```

### 6.2 문제점

1. **절대 위치 모름**: SET_KINEMATIC_POSITION은 상대 좌표만 설정
2. **주사기 크기 미대응**: 91mm 하드코딩, 20cc 주사기는 더 짧음
3. **재사용 주사기**: 남은 양 파악 불가
4. **물리적 한계 미감지**: Klipper는 G1 이동 중 엔드스톱 무시

### 6.3 검토 중인 해결 방안

| 방법 | 설명 | 장단점 |
|------|------|--------|
| gcode_button | printer.cfg에 별도 GPIO로 Y 엔드스톱 감시 | 즉시 감지, 별도 배선 필요 |
| 소프트웨어 폴링 | QUERY_ENDSTOPS API 200ms 주기 | 배선 불필요, 200~500ms 지연 |
| 토출 방향 반전 | -방향 토출, position_min=0으로 Klipper가 거부 | 간단, 하지만 G28 Y 필요 |
| filament_switch_sensor | 별도 핀으로 auto-pause | 내장 pause 기능, 별도 핀 필요 |

---

## 7. 하드웨어 인터페이스 상세

### 7.1 모터 제어 (Moonraker REST API)

| 축 | 범위 | 기본 속도 | 홈 방향 | 용도 |
|----|------|-----------|---------|------|
| Z | 0~80mm | 300 mm/min | 0mm (상단) | 빌드 플레이트 |
| X | 0~140mm | 300 mm/min | 0mm (좌측) | 블레이드 수평 이동 |
| Y | 0~85mm | 300 mm/min | 0mm (비움) | 시린지 펌프 레진 토출 |

- **API 엔드포인트**: `http://localhost:7125`
- **G-code 전송**: POST `/printer/gcode/script`
- **상태 조회**: GET `/printer/objects/query`
- **타임아웃**: X축 300s, Y축 120s, Z홈 120s, 기본 60s
- **재시도**: 3회, 1초 간격, 자동 재연결

### 7.2 DLP 제어 (NVR2+ I2C)

| 기능 | I2C 명령 | 데이터 |
|------|----------|--------|
| LED ON | 0x52 | [0x07] |
| LED OFF | 0x52 | [0x00] |
| 밝기 설정 | 0x54 | [LSB,MSB] × 3 (RGB) |
| 프로젝터 ON | GPIO 2 = HIGH | - |
| 프로젝터 OFF | GPIO 2 = LOW | - |
| 패턴 선택 | 0x05 | [pattern_id] |
| 패턴 ON/OFF | 0x0B | [0x01/0x00] |
| Flip 설정 | 0x14 | [mode] |

- **I2C Slave Address**: 0x1B
- **밝기 범위**: 91~1023 (UI에서 9~100%)
- **라이브러리**: libcyusbserial.so (Raspberry Pi)
- **Windows**: 시뮬레이션 모드

### 7.3 입력값 제한 범위 (전체)

| 페이지 | 항목 | 범위 | 단위 |
|--------|------|------|------|
| Material | Blade Speed | 1~100 | mm/s |
| Material | LED Power | 9~100 | % |
| Material | Blade Cycles | 1~3 | 회 |
| Material | Y Dispense Distance | 0.1~5.0 | mm |
| Material | Y Dispense Speed | 1~15 | mm/s |
| Material | Y Dispense Delay | 0.5~300 | s |
| Material | Leveling Cycles | 0~5 | 회 |
| Material | Lift Height | 1.0~20.0 | mm |
| Material | Drop Speed | 10~300 | mm/min |
| Setting | LED Power | 9~100 | % |
| Setting | Blade Speed | 1~100 | mm/s |
| Manual | 축 이동 거리 | 0.05~10.0 | mm |
| Manual | X축 속도 | 5~9999 | mm/s |
| Exposure | 노출 시간 | 1~60 (Clean: 120) | s |

---

## 8. 스레드 안전성

### PrintWorker 동기화 메커니즘

```
_mutex (QMutex)          → _is_paused, _is_stopped 보호
_pause_condition (QWC)   → pause/resume 동기화
_resin_mutex (QMutex)    → 레진 대기 상태 보호
_resin_condition (QWC)   → resin_empty 사용자 응답 동기화
```

### 안전 패턴
```python
# Flag 체크 (항상 mutex 락 후 읽기)
def _check_stopped(self):
    self._mutex.lock()
    stopped = self._is_stopped
    self._mutex.unlock()
    return stopped

# 노출 대기 중 정지 → 즉시 LED OFF
def _wait_exposure(self, duration):
    while elapsed < duration:
        if self._check_stopped():
            self._dlp_led_off()      # 즉시 LED OFF
            self.clear_image.emit()   # 이미지 클리어
            return
        time.sleep(0.1)
```

---

## 9. 결론 및 권장 사항

### 잘된 점
1. **Signal/Slot 아키텍처**: 페이지 간 결합도가 낮고 유지보수 용이
2. **에러 처리**: 프린트 중 대부분의 에러 상황 처리
3. **테마 시스템**: 메타클래스 기반 런타임 테마 전환
4. **소재 프리셋**: dataclass + JSON 영속성으로 확장 가능
5. **Klipper 통합**: pause/resume/cancel/restart 안전하게 처리
6. **안전 정지**: 노출 중 즉시 LED OFF, 레진 부족 사용자 알림

### 우선 개선 사항
1. **Y축 프라이밍 절대 위치 파악** - 가장 시급 (레진 소진 감지 정확성)
2. **일시정지 시 LED OFF** - 안전 문제 (노출 중 pause 시 LED 상태 미처리)
3. **main.py 분리** - 비즈니스 로직 별도 컨트롤러로
4. **LED 파워 변환 일원화** - % ↔ 91~1023 한 곳에서 관리
5. **페이지 인덱스 enum화** - 수동 관리 대신 IntEnum
