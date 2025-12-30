# VERICOM DLP 3D Printer GUI - TODO

## 현재 상태

**키오스크 모드 & 모터 비동기 처리** (2025-12-30)
- 키오스크 보안 모드 추가 (Alt+F4, Alt+Tab, Esc 차단)
- 관리자 모드 (로고 5회 클릭 또는 Ctrl+Shift+F12)
- 모터 작업 비동기 처리 (GUI 멈춤 방지)
- Manual 페이지 UI 잠금 기능 (모터 작업 중 버튼 비활성화)

**다크모드 완전 지원** (2025-12-30)
- 모든 페이지 및 다이얼로그 다크모드 테마 지원
- 테마 전환 시 UI 자동 새로고침
- 테마 설정 재시작 후에도 유지

**코드 리뷰 완료** (2025-12-29)
- Critical/High 우선순위 버그 수정 완료
- Medium 일부 항목 수정 완료 (ZIP 파일 검증, 프린트 종료 UI 개선)
- Medium/Low 나머지 항목 대기 중

---

## 코드 리뷰 결과 (2025-12-29)

### Critical - 수정 완료 ✅

- [x] **블레이드 속도 단위 혼란** - main.py에서 ×60 사용, FilePreviewPage에서 ×50 사용
  - 수정: main.py에서 ×60 제거, ×50으로 통일

- [x] **레이어 이미지 업데이트 안됨** - PrintProgressPage에 show_image 시그널 미연결
  - 수정: main.py에서 print_worker.show_image → print_progress_page.update_layer_image 연결

- [x] **이미지 로드 실패 시 무시** - 레이어 이미지 로드 실패해도 프린트 계속 진행
  - 수정: 3회 재시도 후 실패 시 프린트 중지, 에러 다이얼로그 표시

### High - 수정 완료 ✅

- [x] **홈 이동 타임아웃** - Z/X축 홈 이동 시 100초 타임아웃으로 실패
  - 수정: motor_controller.py에서 타임아웃 100초 → 120초 증가

- [x] **에러 시 ProgressPage 미통보** - 에러 발생해도 PrintProgressPage가 모르고 계속 표시
  - 수정: ErrorDialog 추가, 에러 시 다이얼로그 표시 후 메인 페이지로 이동

- [x] **모터 에러 무시** - 모터 이동 실패해도 프린트 계속 진행
  - 수정: 모터 래퍼 함수에 반환값 체크, 실패 시 error_occurred 시그널 emit

- [x] **정지/에러 시 홈 복귀 순서** - Z축 먼저 복귀하면 출력물 손상 가능
  - 수정: X축만 홈 복귀 (Z축은 현재 위치 유지 - 안전)

### Medium - 일부 수정 완료

- [x] **ZIP 파싱 실패 시 피드백 없음** - 에러 시 사용자에게 알림 없음
  - 수정: ZIP 파일 검증 기능 추가 (run.gcode, 머신설정, 미리보기, 레이어 이미지 연속성)
  - 수정: ZipErrorDialog 추가, 검증 실패 시 에러 메시지 표시

- [x] **프린트 종료 후 Z축 복귀 선택 없음** - 자동으로 결정됨
  - 수정: 프린트 완료/에러/정지 후 "GUI 홈" / "Z축 홈" 버튼 2개 표시
  - 사용자가 Z축 홈 복귀 여부 선택 가능

- [ ] **_process_layer() 후 stop 체크 없음** - 레이어 처리 후 즉시 다음 레이어로 진행
- [ ] **일시정지 시 LED 상태** - 일시정지해도 LED가 계속 켜져 있을 수 있음
- [ ] **파라미터 기본값 의존** - PrintParameters 기본값과 실제 gcode 값 불일치 가능

### Low - 대기 중

- [ ] **레이어 인덱스 0-based vs 1-based** - 로그와 UI에서 혼용
- [ ] **시뮬레이션 모드 불완전** - 일부 하드웨어 로직 시뮬레이션 누락
- [ ] **하드코딩된 값들** - 매직 넘버 상수화 필요

---

## 알려진 문제점 (Bugs)

### 높은 우선순위

- [ ] **LED 밝기 설정 실패** - I2C 쓰기 오류 17 발생
  - 로그: `[DLP] I2C 쓰기 실패: 17`
  - 원인 조사 필요 (I2C 주소, 권한, 하드웨어 연결 확인)

### 중간 우선순위

- [ ] **일시정지/재개 동작 확인 필요** - 실제 테스트 미완료
- [ ] **비상 정지 후 상태 복구** - STOP 후 재시작 시 상태 초기화 확인

---

## 수정/개선 사항 (Improvements)

### 프린팅 관련

- [ ] 프린트 완료 후 Z축 상단으로 이동 (출력물 제거 용이)
- [ ] 레이어별 진행 로그 개선 (현재 레이어/총 레이어 표시)
- [x] 프린트 중 현재 레이어 이미지 미리보기 ✅ (2025-12-24)

### DLP/LED 관련

- [ ] LED 밝기 조절 UI 개선 (슬라이더 또는 직접 입력)
- [ ] LED 밝기 값 범위 확인 (91~1023 vs 0~100%)
- [ ] 프로젝터 상태 모니터링 (온도, 연결 상태)

### 모터 관련

- [ ] 모터 현재 위치 실시간 표시
- [ ] Z축 리밋 스위치 상태 표시
- [ ] 이동 중 상태 표시 (Moving... / Idle)

### 파일 관리

- [ ] 파일 정렬 옵션 (이름, 날짜, 크기)
- [ ] 파일 삭제 확인 다이얼로그 개선
- [ ] 내부 저장소 지원 (USB 외에 로컬 저장)
- [ ] 최근 프린트 파일 기록

---

## 추가 기능 (New Features)

### GUI 페이지 추가

- [ ] **Network 설정 페이지** - WiFi 연결, IP 확인
- [x] **Theme 페이지** - Light/Dark 테마 선택 ✅ (2025-12-24)
- [ ] **Calibration 페이지** - LED Test, Blade Test, Z=0 설정
- [ ] **프린트 이력 페이지** - 과거 프린트 기록 조회
- [x] **Setting 페이지** - LED Power/Blade Speed 설정

### 시스템 기능

- [ ] **자동 시작** - 부팅 시 자동 실행 (systemd 서비스)
- [x] **설정 저장/로드** - JSON 파일로 설정 유지 (SettingsManager)
- [ ] **다국어 지원** - 한국어/영어 전환 실제 구현
- [x] **테마 기능** - Light/Dark 2가지 테마 ✅ (2025-12-24)
- [ ] **OTA 업데이트** - 원격 펌웨어/소프트웨어 업데이트
- [ ] **로그 저장** - 프린트 로그 파일 저장

### 프린팅 고급 기능

- [ ] **프린트 재개** - 중단된 프린트 특정 레이어부터 재개
- [ ] **테스트 프린트** - 첫 N개 레이어만 프린트
- [ ] **다중 노출** - 레이어당 복수 노출 (언더컷 처리)
- [ ] **프린트 일정** - 예약 프린트

---

## 코드 정리 (Refactoring)

- [ ] `Folder for reference/` 디렉토리 정리 또는 삭제
- [ ] `pages/system_page (1).py` 중복 파일 삭제
- [ ] 사용하지 않는 `_parse_gcode_params()` 함수 제거 (file_preview_page.py)
- [ ] 오래된 TODO 파일들 정리 (`*_todo*.md`)
- [ ] 디자인 가이드 파일 통합 (`VERICOM_GUI_Design_Guide_v*.md`)

---

## 테스트

- [ ] 시뮬레이션 모드 전체 플로우 테스트
- [ ] 실제 하드웨어 연속 프린트 테스트
- [ ] 에러 상황 복구 테스트 (연결 끊김, 전원 차단)
- [ ] 장시간 프린트 안정성 테스트

---

## 완료된 항목 (Done)

### 2025-12-30 (키오스크 & 모터 비동기)

- [x] 키오스크 모드 구현 (`utils/kiosk_manager.py`)
  - Alt+F4, Alt+Tab, Esc, F1-F11, Windows 키 차단
  - 관리자 모드 토글: 로고 5회 클릭 (3초 내) 또는 Ctrl+Shift+F12
  - 관리자 모드 5분 후 자동 해제
- [x] 모터 작업 비동기 처리 (`MotorWorker` QThread)
  - GUI 멈춤 없이 모터 작업 실행
  - 작업 중 버튼 비활성화로 오작동 방지
- [x] Manual 페이지 `set_busy()` 메서드 추가
  - 모터 작업 중 뒤로가기/제어 버튼 비활성화
  - 타이틀 "Moving..." 표시

### 2025-12-30 (다크모드)

- [x] 정적 스타일시트 상수를 동적 함수로 전환
  - `get_axis_panel_style()`, `get_axis_title_style()`, `get_stop_button_style()`
  - `get_distance_button_style()`, `get_distance_button_active_style()`
  - `get_icon_button_style()`, `get_icon_button_active_style()`
- [x] manual_page.py 다크모드 지원
- [x] setting_page.py 다크모드 지원 (인라인 스타일을 동적 메서드로 전환)
- [x] numeric_keypad.py 다이얼로그 배경 수정 (WHITE → BG_PRIMARY)
- [x] number_dial.py DistanceSelector 동적 스타일 적용
- [x] icon_button.py 동적 스타일 적용
- [x] file_preview_page.py 다이얼로그 배경 수정 (ConfirmDialog, ZipErrorDialog)
- [x] print_progress_page.py 다이얼로그 배경 수정 (CompletedDialog, StopConfirmDialog, StoppedDialog, ErrorDialog)

### 2025-12-29 (코드 리뷰)

- [x] 블레이드 속도 단위 통일 (×50)
- [x] PrintProgressPage 레이어 이미지 업데이트 연결
- [x] 이미지 로드 실패 시 3회 재시도 + 프린트 중지
- [x] 홈 이동 타임아웃 120초로 증가
- [x] ErrorDialog 추가 및 에러 처리 개선
- [x] 모터 에러 체크 및 처리
- [x] 정지/에러 시 X축만 홈 복귀 (Z축 위치 유지)
- [x] ZIP 파일 검증 기능 추가 (run.gcode, 머신설정, 미리보기, 레이어 연속성)
- [x] ZipErrorDialog 추가 (파일 오류 시 에러 메시지 표시)
- [x] 프린트 종료 UI 개선 (GUI홈/Z축홈 버튼 선택)
- [x] StoppedDialog, show_stopped(), show_error() 추가

### 2025-12-24

- [x] Theme 페이지 구현 (Light/Dark 선택)
- [x] ThemeManager 싱글톤 구현
- [x] Colors 메타클래스 동적 테마 지원
- [x] 동적 스타일 함수 추가 (get_*_style())
- [x] 다이얼로그 테마 지원 (NumberDial)
- [x] FilePreviewPage 아이콘 기반 정보 표시
- [x] PrintProgressPage 레이아웃 재설계
- [x] 프린트 중 현재 레이어 이미지 미리보기
- [x] 블레이드 시간 포함한 총 예상 시간 계산

### 2025-12 (이전)

- [x] 기본 GUI 프레임워크 구축 (PySide6)
- [x] 12개 페이지 UI 구현
- [x] Moonraker API 모터 제어 연동
- [x] NVR2+ DLP 프로젝터 제어 연동
- [x] PrintWorker QThread 구현
- [x] ZIP 파일 파싱 및 레이어 이미지 추출
- [x] 프로젝터 윈도우 (두 번째 모니터 출력)
- [x] totalLayer 파라미터 전달 버그 수정
- [x] Setting 페이지 구현 (LED Power + Blade 설정)
- [x] 설정 저장/로드 구현 (JSON, SettingsManager)

---

## 우선순위 가이드

1. **Critical** - 프린팅 불가능한 버그
2. **High** - 사용성에 큰 영향
3. **Medium** - 개선 필요하지만 동작함
4. **Low** - 나중에 해도 되는 기능
