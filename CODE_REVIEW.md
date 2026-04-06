# MAZIC CERA GUI - 코드 리뷰 (2025-04-06)

## 1. 프로젝트 아키텍처 요약

| 항목 | 내용 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| 패턴 | QStackedWidget 기반 페이지 네비게이션 |
| 스레딩 | QThread (PrintWorker, MotorWorker) |
| 상태 관리 | SettingsManager 싱글톤 (JSON 파일) |
| 하드웨어 | Moonraker REST API + CyUSBSerial I2C |
| 테마 | Colors 메타클래스 기반 동적 테마 |

### 파일 구조

```
vgui/
├── main.py                      # 37KB - 메인 윈도우 (15개 페이지 관리)
├── components/                  # 재사용 UI 컴포넌트 (4개)
│   ├── header.py                # 페이지 헤더
│   ├── icon_button.py           # 버튼 유형 6종
│   ├── number_dial.py           # ±다이얼, DistanceSelector
│   └── numeric_keypad.py        # 터치 숫자 키패드
├── controllers/                 # 하드웨어 + 데이터 (5개)
│   ├── motor_controller.py      # Moonraker 모터 제어 (Z/X/Y)
│   ├── dlp_controller.py        # NVR2+ DLP/LED (I2C)
│   ├── gcode_parser.py          # ZIP/G-code 파싱
│   ├── settings_manager.py      # 설정 + 소재 프리셋 관리
│   └── theme_manager.py         # 동적 테마 관리
├── workers/
│   └── print_worker.py          # 프린트 시퀀스 (QThread)
├── windows/
│   └── projector_window.py      # 2차 모니터 전체화면
├── pages/                       # UI 페이지 (15개)
│   ├── base_page.py             # 기본 페이지 (헤더+컨텐츠+푸터)
│   ├── main_page.py             # 홈 (TOOL/PRINT/SYSTEM)
│   ├── tool_page.py             # 도구 메뉴 (5개 버튼)
│   ├── manual_page.py           # Z/X/Y 수동 제어
│   ├── print_page.py            # USB 파일 브라우저
│   ├── file_preview_page.py     # 파일 미리보기 + 소재 선택
│   ├── print_progress_page.py   # 프린트 진행 상황
│   ├── exposure_page.py         # LED 노출 테스트 (5패턴)
│   ├── leveling_page.py         # 3단계 레벨링
│   ├── setting_page.py          # LED/Blade/Y축 설정
│   ├── material_page.py         # 소재 프리셋 관리
│   ├── system_page.py           # 시스템 메뉴
│   ├── device_info_page.py      # 장치 정보
│   ├── language_page.py         # 언어 선택
│   ├── service_page.py          # 서비스 연락처
│   └── theme_page.py            # 테마 선택
├── styles/                      # 디자인 시스템
│   ├── colors.py                # 동적 컬러 팔레트
│   ├── fonts.py                 # 폰트 정의
│   ├── icons.py                 # SVG 아이콘 50+개
│   └── stylesheets.py           # QSS 스타일시트
└── utils/                       # 유틸리티
    ├── kiosk_manager.py         # 키오스크 보안
    ├── usb_monitor.py           # USB 감지
    ├── zip_handler.py           # ZIP 메타데이터 추출
    └── time_formatter.py        # 시간 포맷팅
```

---

## 2. 설계 패턴 분석

### 2.1 페이지 네비게이션 (QStackedWidget)

**장점:**
- 인덱스 기반으로 단순하고 예측 가능
- Signal/Slot으로 페이지 간 결합도 낮음
- BasePage 상속으로 헤더/푸터 일관성 유지

**현재 구조 (15개 페이지):**
```
PAGE_MAIN = 0         PAGE_DEVICE_INFO = 6    PAGE_THEME = 12
PAGE_TOOL = 1         PAGE_LANGUAGE = 7       PAGE_LEVELING = 13
PAGE_MANUAL = 2       PAGE_SERVICE = 8        PAGE_MATERIAL = 14
PAGE_PRINT = 3        PAGE_FILE_PREVIEW = 9
PAGE_EXPOSURE = 4     PAGE_PRINT_PROGRESS = 10
PAGE_SYSTEM = 5       PAGE_SETTING = 11
```

**주의점:**
- 페이지 추가 시 인덱스 수동 관리 필요 → enum 도입 고려

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
- **안전성**: 양쪽 모두 스레드 안전하지 않음 (메인 스레드에서만 사용하므로 현재는 OK)

### 2.4 QThread 패턴

- `PrintWorker(QThread)`: `run()` 오버라이드, Mutex/WaitCondition으로 pause/stop
- `MotorWorker(QObject)`: `moveToThread()` 패턴, 개별 작업별 스레드 생성
- **잠재 이슈**: MotorWorker 스레드가 빈번히 생성/소멸됨 (ThreadPool 고려 가능)

---

## 3. 모듈별 코드 품질

### 3.1 main.py (37KB, ~900줄)

**역할**: 앱 진입점, 페이지 관리, 하드웨어 연결, 비즈니스 로직

**강점:**
- 시그널 연결이 체계적으로 정리됨
- 하드웨어 초기화와 UI 분리
- closeEvent에서 리소스 정리 철저

**개선 가능:**
- 파일 크기가 크다 (900줄+) → 비즈니스 로직을 별도 컨트롤러로 분리 고려
- `_on_start_print()` 메서드가 100줄+ → 파라미터 추출 로직 별도 함수화 고려
- LED 파워 변환 로직이 여러 곳에 분산 (% → 91~1023)

### 3.2 print_worker.py (~700줄)

**역할**: 프린트 시퀀스 전체 관리 (QThread)

**강점:**
- Mutex/WaitCondition으로 안전한 일시정지/정지
- 에러 처리 체계적 (모터 실패, 이미지 로드 실패)
- Klipper shutdown 자동 복구
- 시뮬레이션 모드 완비

**개선 가능:**
- `_process_layer()` 하나의 메서드가 130줄 → 블레이드/노출/Y축 로직 분리 고려
- 레진 부족 처리가 메인 스레드(다이얼로그)와 워커 스레드(대기) 간 교차 → 깔끔하지만 복잡

### 3.3 settings_manager.py (~450줄)

**역할**: JSON 설정 영속성 + MaterialPreset CRUD

**강점:**
- MaterialPreset dataclass로 타입 안전성
- 기본값이 명확하게 정의됨
- 범위 클램핑 (min/max)

**개선 가능:**
- PrintSettings와 MaterialPreset 필드가 일부 중복 (blade_speed, led_power 등)
- `get_*/set_*` 메서드가 많아 코드량이 큼 → property 패턴 고려

### 3.4 motor_controller.py (~650줄)

**역할**: Moonraker REST API로 3축 모터 제어

**강점:**
- send_gcode에 자동 재연결 로직
- wait_for_movement_complete (M400) 로 동기화
- Klipper 상태 관리 (pause/resume/cancel)

**개선 가능:**
- HTTP 요청 타임아웃이 일부 하드코딩 (120초)
- 예외 처리에서 구체적 오류 구분이 부족 (모두 try/except)

### 3.5 dlp_controller.py (~490줄)

**역할**: NVR2+ DLP 프로젝터 + UV LED 제어 (I2C)

**강점:**
- CyUSBSerial 라이브러리 래핑 완비
- 시뮬레이션 모드 지원
- 밝기 범위 검증 (91~1023)

**알려진 이슈:**
- I2C 쓰기 오류 17 간헐적 발생 (하드웨어 원인 조사 필요)

### 3.6 pages/ (15개 파일)

**일관성:**
- 모든 페이지가 BasePage 상속 (MainPage 제외)
- Signal 정의가 클래스 수준에서 명확
- 다이얼로그들이 자체 클래스로 분리

**가독성:**
- Korean 주석 일관 사용
- 섹션 구분 (`# ===== Title =====`)
- 매직 넘버에 주석 설명

---

## 4. 미해결 이슈 및 기술 부채

### 4.1 Critical / High

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 1 | I2C 쓰기 오류 17 (LED 밝기) | dlp_controller.py | 조사 필요 |
| 2 | 일시정지 시 LED 상태 미처리 | print_worker.py | 미수정 |

### 4.2 Medium

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 3 | 레이어 인덱스 0-based vs 1-based 혼용 | print_worker.py, progress_page | 미수정 |
| 4 | _process_layer() 후 stop 체크 누락 | print_worker.py | 미수정 |
| 5 | PrintSettings와 MaterialPreset 필드 중복 | settings_manager.py | 리팩토링 대기 |
| 6 | X축 엔드스톱 위치 미확정 (cleanup 홈) | print_worker.py | TBD |

### 4.3 Low

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 7 | 시뮬레이션 모드 불완전 | 전체 | 미수정 |
| 8 | 하드코딩된 매직 넘버 | 전체 | 미수정 |
| 9 | 페이지 인덱스 수동 관리 | main.py | enum 도입 고려 |
| 10 | MotorWorker 스레드 빈번 생성/소멸 | main.py | ThreadPool 고려 |

---

## 5. 프린트 시퀀스 분석

### 5.1 전체 흐름

```
파일 선택 (USB)
    ↓
ZIP 검증 (run.gcode, 머신설정, 미리보기, 레이어 연속성)
    ↓
소재 선택 팝업 (MaterialSelectDialog)
    ↓
파일 미리보기 (ReadOnly 파라미터)
    ↓
프린트 시작
    ↓
┌─── 초기화 ───┐
│ Z홈 → Z 0.1mm  │
│ X홈 (140mm)    │
│ Y홈 → Y +6mm   │  ← 50cc 보정
│ 레진 평탄화     │
└──────────────┘
    ↓
┌─── 메인 루프 (레이어별) ───┐
│ 1. Z축 이동 (레이어 높이)    │
│ 2. Y축 레진 토출 (80mm 체크) │
│ 3. X축 블레이드 스윕 (140→0) │
│ 4. 일시정지/정지 체크         │
│ 5. 레이어 이미지 로드/표시    │
│ 6. LED ON → 노출 대기        │
│ 7. LED OFF → 이미지 클리어   │
│ 8. 일시정지/정지 체크         │
│ 9. X축 복귀 (0→140)          │
│ 10. Z축 다음 레이어로 하강   │
└─────────────────────────────┘
    ↓
┌─── 정리 ───┐
│ LED OFF     │
│ 이미지 클리어│
│ Klipper 취소 │
└─────────────┘
```

### 5.2 에러 처리 경로

| 에러 상황 | 처리 |
|-----------|------|
| 모터 이동 실패 | error_occurred 시그널 → 프린트 중지 |
| 이미지 로드 실패 | 3회 재시도 → 실패 시 프린트 중지 |
| Y축 80mm 도달 | 레진 부족 알림 → 사용자 선택 (계속/중지) |
| Klipper shutdown | 자동 firmware_restart → 재홈 |
| 사용자 정지 | STOPPING 상태 → cleanup → IDLE |

---

## 6. 소재 프리셋 시스템

### 6.1 MaterialPreset 구조

```python
@dataclass
class MaterialPreset:
    name: str                          # 프리셋 이름
    blade_speed: int = 5               # 블레이드 속도 (1-15 mm/s)
    led_power: int = 43                # LED 파워 (9-100%)
    blade_cycles: int = 1              # 블레이드 반복 (1~3)
    y_dispense_distance: float = 1.0   # Y축 토출 거리 (0.1~5.0 mm)
    y_dispense_speed: int = 5          # Y축 토출 속도 (1~15 mm/s)
    y_dispense_delay: float = 2.0      # Y축 토출 후 대기 (0.5~10.0 s)
    leveling_cycles: int = 1           # 레벨링 횟수 (0~5)
    lift_height: float = 5.0           # 리프트 높이 (1.0~20.0 mm)
    drop_speed: int = 150              # Z축 하강 속도 (10~300 mm/min)
```

### 6.2 기본 소재

| 소재 | LED | Blade | Y Dist | Y Speed | Y Delay | Drop Speed |
|------|-----|-------|--------|---------|---------|------------|
| Zirconia | 43% | 5mm/s | 1.0mm | 5mm/s | 2.0s | 150mm/min |
| Alumina | 50% | 5mm/s | 1.0mm | 5mm/s | 2.0s | 150mm/min |
| Hydroxyapatite | 45% | 4mm/s | 1.2mm | 4mm/s | 2.5s | 120mm/min |

### 6.3 프린트 플로우 통합

```
파일 선택 → MaterialSelectDialog(팝업) → FilePreviewPage(읽기전용)
                                            ↓
                                     Start 버튼 클릭
                                            ↓
                                  MaterialPreset 값으로 프린트 시작
```

---

## 7. 결론 및 권장 사항

### 잘된 점
1. **Signal/Slot 아키텍처**: 페이지 간 결합도가 낮고 유지보수 용이
2. **에러 처리**: 프린트 중 발생 가능한 대부분의 에러 상황 처리
3. **테마 시스템**: 메타클래스 기반으로 런타임 테마 전환 깔끔
4. **소재 프리셋**: dataclass + JSON 영속성으로 확장 가능한 구조
5. **Klipper 통합**: pause/resume/cancel/restart 안전하게 처리

### 개선 권장
1. **main.py 분리**: 비즈니스 로직을 별도 컨트롤러로 (PrintController, HardwareController)
2. **LED 파워 변환 일원화**: % ↔ 91~1023 변환을 한 곳에서 관리
3. **페이지 인덱스 enum화**: 수동 인덱스 관리 대신 IntEnum 사용
4. **PrintSettings 정리**: MaterialPreset과 중복 제거
5. **단위 테스트**: controllers/ 모듈에 대한 테스트 추가
