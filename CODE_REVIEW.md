# MAZIC CERA GUI - 코드 리뷰

> 최종 업데이트: 2025-04-16

## 1. 프로젝트 아키텍처 요약

| 항목 | 내용 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| 패턴 | QStackedWidget 기반 페이지 네비게이션 |
| 스레딩 | QThread (PrintWorker, MotorWorker) |
| 상태 관리 | SettingsManager 싱글톤 (JSON 파일) |
| 하드웨어 | Moonraker REST API + CyUSBSerial I2C |
| 테마 | Colors 메타클래스 기반 동적 테마 |

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

### 3.2 print_worker.py (~600줄)

**역할**: 프린트 시퀀스 전체 관리 (QThread)

**강점**: Mutex/WaitCondition 안전한 일시정지/정지, Klipper shutdown 자동 복구, 시뮬레이션 모드

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

**알려진 이슈**: I2C 쓰기 오류 17 간헐적 발생

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
| 3 | I2C 쓰기 오류 17 (LED 밝기) | dlp_controller.py | 조사 필요 |
| 4 | 일시정지 시 LED 상태 미처리 | print_worker.py | 미수정 |

### Medium

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 5 | 레이어 인덱스 0-based vs 1-based 혼용 | print_worker, progress_page | 미수정 |
| 6 | _process_layer() 후 stop 체크 누락 | print_worker.py | 미수정 |
| 7 | PrintSettings와 MaterialPreset 필드 중복 | settings_manager.py | 리팩토링 대기 |
| 8 | X축 엔드스톱 위치 미확정 | print_worker.py | TBD |

### Low

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 9 | 시뮬레이션 모드 불완전 | 전체 | 미수정 |
| 10 | 하드코딩된 매직 넘버 | 전체 | 미수정 |
| 11 | 페이지 인덱스 수동 관리 | main.py | enum 도입 고려 |
| 12 | MotorWorker 스레드 빈번 생성/소멸 | main.py | ThreadPool 고려 |

---

## 5. 프린트 시퀀스 분석

### 5.1 전체 흐름

```
파일 선택 (USB) → ZIP 검증 → 소재 선택 팝업 → 미리보기 (읽기전용) → 프린트 시작
    ↓
┌─── 초기화 ───┐
│ Z홈 → Z 0.1mm  │
│ X홈             │
│ 프라이밍 체크    │  ← priming_pos > 0 필수
│ 레진 평탄화     │
└──────────────┘
    ↓
┌─── 메인 루프 (레이어별) ───┐
│ 1. Z축 이동 (레이어 높이)    │
│ 2. Y축 레진 토출 (91mm 체크) │
│ 3. X축 블레이드 스윕 (140→0) │
│ 4. 일시정지/정지 체크         │
│ 5. 레이어 이미지 로드/표시    │
│ 6. LED ON → 노출 대기        │
│ 7. LED OFF → 이미지 클리어   │
│ 8. Z축 리프트 (+5mm)         │
│ 9. X축 복귀 (0→140)          │
└─────────────────────────────┘
    ↓
┌─── 정리 ───┐
│ LED OFF     │
│ 이미지 클리어│
│ Klipper 취소 │
└─────────────┘
```

### 5.2 에러 처리

| 에러 상황 | 처리 |
|-----------|------|
| 모터 이동 실패 | error_occurred 시그널 → 프린트 중지 |
| 이미지 로드 실패 | 3회 재시도 → 실패 시 프린트 중지 |
| Y축 91mm 도달 | 레진 부족 알림 → 사용자 선택 (계속/중지) |
| Klipper shutdown | 자동 firmware_restart → 재홈 |
| 사용자 정지 | STOPPING 상태 → cleanup → IDLE |

---

## 6. Y축 프라이밍 시스템 분석

### 6.1 현재 구현

```
Setting 페이지 PRIME 시작
  → SET_KINEMATIC_POSITION Y=0  (현재 위치를 0으로 설정, 모터 안 움직임)
  → +방향으로 소량 이동 (레진 나올 때까지)
  → 프라이밍 위치 저장 (settings.json)
  → 출력 시: 저장된 위치에서 시작, +방향으로 토출
  → Y >= 91mm 시: 소프트웨어 카운터로 레진 소진 감지
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

## 7. 결론 및 권장 사항

### 잘된 점
1. **Signal/Slot 아키텍처**: 페이지 간 결합도가 낮고 유지보수 용이
2. **에러 처리**: 프린트 중 대부분의 에러 상황 처리
3. **테마 시스템**: 메타클래스 기반 런타임 테마 전환
4. **소재 프리셋**: dataclass + JSON 영속성으로 확장 가능
5. **Klipper 통합**: pause/resume/cancel/restart 안전하게 처리

### 우선 개선 사항
1. **Y축 프라이밍 절대 위치 파악** — 가장 시급 (레진 소진 감지 정확성)
2. **main.py 분리** — 비즈니스 로직 별도 컨트롤러로
3. **LED 파워 변환 일원화** — % ↔ 91~1023 한 곳에서 관리
4. **페이지 인덱스 enum화** — 수동 관리 대신 IntEnum
5. **일시정지 시 LED OFF** — 안전 문제
