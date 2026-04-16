# MAZIC CERA GUI - TODO

> 최종 업데이트: 2025-04-16

---

## Critical - 현재 진행 중

### Y축 프라이밍 위치 감지 문제

현재 프라이밍 시 `SET_KINEMATIC_POSITION Y=0`으로 상대 좌표만 설정하므로, 홈센서 기준 절대 위치를 알 수 없음.

**문제점:**
- 홈잉(G28 Y)하면 토출 방향이라 레진 낭비 → 사용 불가
- 주사기 크기(20cc/50cc)나 재사용 여부에 따라 남은 거리가 다름
- Klipper는 일반 G1 이동 중 엔드스톱 무시 (G28 때만 감지)
- 현재 `Y_MAX_POSITION = 91mm` 소프트웨어 카운터 기반 감지만 있음

**검토 중인 대안:**
- [ ] `gcode_button` (printer.cfg): 별도 GPIO 핀으로 Y 엔드스톱 감시, 트리거 시 PAUSE
- [ ] 소프트웨어 폴링: GUI에서 200ms마다 `QUERY_ENDSTOPS` API 호출
- [ ] 토출 방향 반전: 홈센서 쪽(-) = 레진 소진, +방향 = 주사기 가득
- [ ] `filament_switch_sensor` 재활용: 별도 핀으로 auto-pause

---

## High - 미수정

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 1 | I2C 쓰기 오류 17 (LED 밝기 간헐적 실패) | dlp_controller.py | 조사 필요 |
| 2 | 일시정지 시 LED 상태 미처리 (LED 켜진 채로 일시정지) | print_worker.py | 미수정 |
| 3 | _process_layer() 후 stop 체크 누락 | print_worker.py | 미수정 |

---

## Medium - 미수정

| # | 이슈 | 파일 |
|---|------|------|
| 4 | 레이어 인덱스 0-based vs 1-based 혼용 | print_worker.py, progress_page |
| 5 | PrintSettings와 MaterialPreset 필드 중복 | settings_manager.py |
| 6 | X축 엔드스톱 위치 미확정 (cleanup 시 홈 복귀) | print_worker.py |
| 7 | 파라미터 기본값과 실제 gcode 값 불일치 가능 | print_worker.py |

---

## 향후 기능 (New Features)

### 페이지 추가
- [ ] Network 설정 페이지 (WiFi 연결, IP 확인)
- [ ] Calibration 페이지 (LED/Blade/Z=0 통합 테스트)
- [ ] 프린트 이력 페이지 (과거 프린트 기록 조회)

### 시스템 기능
- [ ] 자동 시작 (부팅 시 systemd 서비스)
- [ ] 다국어 지원 실제 구현 (한국어/영어 전환)
- [ ] OTA 업데이트 (원격 펌웨어/소프트웨어 업데이트)
- [ ] 프린트 로그 파일 저장

### 프린팅 고급 기능
- [ ] 프린트 재개 (중단된 프린트 특정 레이어부터)
- [ ] 테스트 프린트 (첫 N개 레이어만)
- [ ] Y축 레진 펌프 → Klipper extruder 이전 (향후 Y축은 다른 용도로 사용 예정)

### UI/UX 개선
- [ ] 모터 현재 위치 실시간 표시
- [ ] 이동 중 상태 표시 (Moving... / Idle)
- [ ] 파일 정렬 옵션 (이름, 날짜, 크기)
- [ ] 최근 프린트 파일 기록

---

## 코드 정리 (Refactoring)

- [ ] `Folder for reference/` 디렉토리 정리 또는 삭제
- [ ] main.py 분리 (비즈니스 로직 → PrintController, HardwareController)
- [ ] LED 파워 변환 일원화 (% ↔ 91~1023 변환을 한 곳에서 관리)
- [ ] 페이지 인덱스 IntEnum 도입 (수동 인덱스 관리 대신)
- [ ] 하드코딩된 매직 넘버 상수화
- [ ] 시뮬레이션 모드 완성도 개선

---

## 테스트

- [ ] 시뮬레이션 모드 전체 플로우 테스트
- [ ] 실제 하드웨어 연속 프린트 테스트
- [ ] 에러 상황 복구 테스트 (연결 끊김, 전원 차단)
- [ ] 장시간 프린트 안정성 테스트

---

## 완료된 항목 (Done)

### v4.1 - Y축 프라이밍 개편 (2025-04)

- [x] 프라이밍에서 G28 Y 제거, SET_KINEMATIC_POSITION Y=0 기반으로 전환
- [x] dir_pin 반전으로 +방향 = 레진 토출
- [x] 프라이밍 시 - 버튼 비활성화 (+ 방향만 이동)
- [x] G92 → SET_KINEMATIC_POSITION 완전 전환
- [x] test_y_priming.py 테스트 도구 추가

### v4.0 - 소재 프리셋 시스템 (2025-04-06)

- [x] MaterialPreset dataclass (9개 필드)
- [x] Material 페이지 신규 생성 (프리셋 리스트 + 편집 패널)
- [x] 프린트 플로우 변경 (파일 → 소재 팝업 → 읽기전용 미리보기)
- [x] MaterialSelectDialog 팝업 추가
- [x] FilePreviewPage EditableRow → ReadOnlyRow 변경
- [x] Manual 페이지에 Y축 (Resin Feeder) 패널 추가
- [x] Y축 50cc 보정 코드 추가 (홈 후 6mm 오프셋)
- [x] Z축 5mm 리프트 추가 (LED 노광 후)

### v3.0 - Y축 레진 공급 및 UI 개편 (2025-01~02)

- [x] Oneway 블레이드 모드 전환
- [x] Klipper idle_timeout 대응 (PAUSE/RESUME 통합)
- [x] Klipper shutdown 자동 복구 (firmware_restart)
- [x] Y축 자동 레진 토출 시스템 (시린지 펌프)
- [x] Y축 80mm 한계 감지 및 사용자 알림
- [x] Exposure + Clean 페이지 통합 (5패턴)
- [x] Leveling 페이지 추가 (3단계 가이드)
- [x] Setting 페이지 3패널 구조 (LED/Blade/Y축)
- [x] 프로젝터 앱 수명주기 내 상시 ON
- [x] X축 블레이드 방향 반전 (150mm 홈)
- [x] 예상 프린트 시간 계산 정확도 개선

### v2.0 - 프린팅 시퀀스 고도화 (2025-01)

- [x] 블레이드 Cycles 설정 (1~3회/레이어)
- [x] 블레이드 Mode 설정 (roundtrip/oneway)
- [x] 일시정지 개선 (노출 완료 후 일시정지)
- [x] Klipper CANCEL_PRINT, CLEAR_PAUSE 통합
- [x] X축 리드스크류 속도 조정

### v1.5 - 키오스크 모드 및 다크모드 (2025-12-30)

- [x] 키오스크 모드 (kiosk_manager.py)
- [x] 비동기 모터 제어 (MotorWorker QThread)
- [x] 모든 페이지/다이얼로그 다크모드 완전 지원
- [x] 정적 스타일시트 → 동적 get_*_style() 전환

### v1.0 - 테마 시스템 및 코드 리뷰 (2025-12-24~29)

- [x] Theme 페이지 (Light/Dark 선택)
- [x] ThemeManager + Colors 메타클래스 동적 테마
- [x] PrintProgressPage 리디자인 (아이콘 기반)
- [x] 코드 리뷰 Critical/High 버그 수정
- [x] ZIP 파일 검증 + ZipErrorDialog
- [x] 프린트 종료 UI (GUI홈/Z축홈 선택)

### v0.5 이전 (2025-12)

- [x] 기본 GUI 프레임워크 (PySide6, 12개 페이지)
- [x] Moonraker API 모터 제어 연동
- [x] NVR2+ DLP 프로젝터 제어 연동
- [x] PrintWorker QThread 구현
- [x] ZIP 파일 파싱 및 레이어 이미지 추출
- [x] 프로젝터 윈도우 (두 번째 모니터)
- [x] Setting 페이지 (LED Power + Blade 설정)
- [x] 설정 저장/로드 (JSON, SettingsManager)
