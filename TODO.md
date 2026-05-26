# MAZIC CERA GUI - TODO

> 최종 업데이트: 2025-05-26
> PENDING_WORK.md의 내용을 이 문서로 통합하였음.

---

## Critical - 현재 진행 중

### Y축 프라이밍 위치 감지 문제

현재 프라이밍 시 `SET_KINEMATIC_POSITION Y=0`으로 상대 좌표만 설정하므로, 홈센서 기준 절대 위치를 알 수 없음.

**문제점:**
- 홈잉(G28 Y)하면 토출 방향이라 레진 낭비 → 사용 불가
- 주사기 크기(20cc/50cc)나 재사용 여부에 따라 남은 거리가 다름
- Klipper는 일반 G1 이동 중 엔드스톱 무시 (G28 때만 감지)

**검토 중인 대안:**
- [ ] `gcode_button` (printer.cfg): 별도 GPIO 핀으로 Y 엔드스톱 감시
- [ ] 소프트웨어 폴링: GUI에서 200ms마다 `QUERY_ENDSTOPS` API 호출
- [ ] 토출 방향 반전: 홈센서 쪽(-) = 레진 소진, +방향 = 주사기 가득
- [ ] `filament_switch_sensor` 재활용: 별도 핀으로 auto-pause

---

## High - 미수정

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 1 | I2C 쓰기 오류 17 (LED 밝기 간헐적 실패) | dlp_controller.py | 조사 필요 |
| 2 | 일시정지 시 LED 상태 미처리 (LED 켜진 채로 일시정지) | print_worker.py | 미수정 |
| 3 | NVR2 exposure 테스트 시 데스크탑 플리커 | projector_window.py | NVR2 SET 버튼 테스트 필요 |

---

## Medium - 미수정

| # | 이슈 | 파일 |
|---|------|------|
| 4 | 레이어 인덱스 0-based vs 1-based 혼용 | print_worker.py, progress_page |
| 5 | PrintSettings와 MaterialPreset 필드 중복 | settings_manager.py |

---

## 코드 내 TODO / 미완성 메서드

### `main.py` - G-code 전송 스텁
- 미사용 `_send_gcode()` 스텁 메서드. `motor_controller.send_gcode()`로 대체 완료.
- **조치**: 삭제 가능

### `pages/device_info_page.py` - UI 갱신 미구현
- `update_info()` 메서드에서 UI 반영 없음 (하드코딩 정보만 표시 중)
- **조치**: Klipper/Moonraker에서 실시간 정보 가져올 때 구현

### `pages/manual_page.py` - set_value() 비활성화
- 축 위치 표시용 메서드. 현재 위치 표시 기능 없이 운영 중.
- **조치**: 모터 현재 위치 실시간 표시 시 구현

---

## 향후 기능 (New Features)

### 페이지 추가
- [ ] Network 설정 페이지 (WiFi 연결, IP 확인)
- [ ] Calibration 페이지 (LED/Blade/Z=0 통합 테스트)
- [ ] 프린트 이력 페이지 (과거 프린트 기록 조회)

### 시스템 기능
- [ ] 자동 시작 (부팅 시 systemd 서비스)
- [ ] 다국어 지원 실제 구현 (한국어/영어 전환)
- [ ] OTA 업데이트
- [ ] 프린트 로그 파일 저장

### 프린팅 고급 기능
- [ ] 프린트 재개 (중단된 프린트 특정 레이어부터)
- [ ] 테스트 프린트 (첫 N개 레이어만)
- [ ] Y축 레진 펌프 → Klipper extruder 이전

### UI/UX 개선
- [ ] 모터 현재 위치 실시간 표시
- [ ] 이동 중 상태 표시 (Moving... / Idle)
- [ ] 파일 정렬 옵션 (이름, 날짜, 크기)
- [ ] 최근 프린트 파일 기록

---

## 코드 정리 (Refactoring)

- [ ] `Folder for reference/` 디렉토리 정리 또는 삭제
- [ ] main.py 분리 (비즈니스 로직 → PrintController, HardwareController)
- [ ] LED 파워 변환 일원화 (% ↔ 91~1023)
- [ ] 페이지 인덱스 IntEnum 도입
- [ ] 하드코딩된 매직 넘버 상수화
- [ ] 시뮬레이션 모드 완성도 개선

---

## 향후 대형 변경 계획

### Y축 → Klipper Extruder 이전
- 현재 Y축 모터가 레진 시린지 펌프로 사용 중
- 향후 Y축은 다른 용도로 전환 예정, 레진 펌프는 Klipper extruder로 이전
- 영향 파일: motor_controller.py, print_worker.py, manual_page.py, setting_page.py, main.py

---

## 테스트

- [ ] 시뮬레이션 모드 전체 플로우 테스트
- [ ] 실제 하드웨어 연속 프린트 테스트
- [ ] 에러 상황 복구 테스트
- [ ] 장시간 프린트 안정성 테스트
- [ ] Push-Pull 3단계 토출 검증 (Pull/Return=0 → 기존과 동일 동작)
- [ ] 레진 소진 → 주사기 리필 / 수동배급 / STOP 동작 검증

---

## 완료된 항목 (Done)

### v5.0 - Push-Pull 3단계 토출 및 레진 소모 UI 개선 (2025-05-26)

- [x] Push-Pull 3단계 레진 토출 시퀀스 (`_dispense_3step()`)
- [x] MaterialPreset 필드 개편: blade_cycles/leveling_cycles/lift_height/drop_speed 제거, y_pull/y_return 추가
- [x] 레진 소모 시 ConfirmDialog → PrintProgressPage 내 버튼 변경 (주사기 리필/수동배급/STOP)
- [x] Push 직후 즉시 레진 소진 감지 (불완전 레이어 방지)
- [x] refill_resin(): 주사기 교체 후 Klipper Y위치 읽어 토출 재개
- [x] _motor_y_move() 반환값 bool → tuple(bool, float) 변경
- [x] Material 페이지 UI 변경 (Pull/Return 파라미터 행 추가)

### v4.2 - 프린트 안전성 강화 및 UI 개선 (2025-04-30)

- [x] 정지 시 LED 즉시 OFF
- [x] 레벨링 전 초기 레진 토출 추가
- [x] Exposure 정지 시 `clear_screen()` 사용
- [x] Blade Speed / Resin Delay 입력 범위 확대
- [x] X축 max position 140mm 통일
- [x] Manual X축 속도 컨트롤, NumericKeypad 전환
- [x] 예상 프린트 시간 재계산

### v4.1 - Y축 프라이밍 개편 (2025-04)

- [x] SET_KINEMATIC_POSITION Y=0 기반 전환, dir_pin 반전
- [x] 프라이밍 시 - 버튼 비활성화
- [x] test_y_priming.py 추가

### v4.0 - 소재 프리셋 시스템 (2025-04-06)

- [x] MaterialPreset, Material 페이지, MaterialSelectDialog
- [x] 프린트 플로우 변경, Y축 50cc 보정, Z축 5mm 리프트

### v3.0 이전

- [x] Oneway 블레이드, Klipper 통합, Y축 자동 레진 토출
- [x] Leveling, Exposure+Clean 통합, Setting 3패널, 키오스크, 다크모드
- [x] 테마 시스템, PrintProgressPage, ZIP 검증, 기본 GUI 프레임워크
