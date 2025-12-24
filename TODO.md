# VERICOM DLP 3D Printer GUI - TODO

## 현재 상태

**기본 프린팅 동작 확인됨** (2025-12)

---

## 알려진 문제점 (Bugs)

### 높은 우선순위

- [ ] **LED 밝기 설정 실패** - I2C 쓰기 오류 17 발생
  - 로그: `[DLP] I2C 쓰기 실패: 17`
  - 원인 조사 필요 (I2C 주소, 권한, 하드웨어 연결 확인)

- [ ] **프린트 완료 후 홈 복귀 없음** - 프린트 완료 시 Z축이 현재 위치에 멈춤
  - PrintWorker `_cleanup()`에서 홈 복귀 로직 추가 필요

### 중간 우선순위

- [ ] **일시정지/재개 동작 확인 필요** - 실제 테스트 미완료
- [ ] **비상 정지 후 상태 복구** - STOP 후 재시작 시 상태 초기화 확인

---

## 수정/개선 사항 (Improvements)

### 프린팅 관련

- [ ] 프린트 완료 후 Z축 상단으로 이동 (출력물 제거 용이)
- [ ] 레이어별 진행 로그 개선 (현재 레이어/총 레이어 표시)
- [ ] 예상 남은 시간 계산 및 표시
- [ ] 프린트 중 현재 레이어 이미지 미리보기 (선택적)

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
  - ThemeManager 싱글톤
  - Colors 메타클래스 동적 테마
  - 동적 스타일 함수 (get_*_style())
  - 다이얼로그/페이지 테마 지원
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

- [x] 기본 GUI 프레임워크 구축 (PySide6)
- [x] 12개 페이지 UI 구현
- [x] Moonraker API 모터 제어 연동
- [x] NVR2+ DLP 프로젝터 제어 연동
- [x] PrintWorker QThread 구현
- [x] ZIP 파일 파싱 및 레이어 이미지 추출
- [x] 프로젝터 윈도우 (두 번째 모니터 출력)
- [x] totalLayer 파라미터 전달 버그 수정 (2025-12)
- [x] 레이어 이미지 탐지 개선 (1.png 형식 지원)
- [x] VERICOM 로고 추가 (메인 페이지 + 모든 서브페이지 우측하단)
- [x] "Set Z=0" → "Calibration" 이름/아이콘 변경
- [x] Clean 페이지 시간 표시 수정 (10.0 sec → 10 sec)
- [x] 프로젝터 해상도 수정 (1440x2560 → 1920x1080)
- [x] LED Power 퍼센트→실제값 변환 수정 (100%=440, 120%=528)
- [x] Setting 페이지 구현 (LED Power + Blade 설정) (2025-12)
- [x] LED ON/OFF 토글 버튼 구현 (1.png 테스트 이미지 표시)
- [x] Blade HOME/MOVE 버튼 구현
- [x] 설정 저장/로드 구현 (JSON, SettingsManager)
- [x] Setting ↔ File Preview 페이지 설정 동기화
- [x] System 페이지 레이아웃 개선 (3×2 그리드, 6버튼)
- [x] Theme 버튼 추가 (SUN 아이콘)
- [x] Theme 페이지 구현 (Light/Dark 선택) (2025-12-24)
- [x] ThemeManager 싱글톤 구현 (2025-12-24)
- [x] Colors 메타클래스 동적 테마 지원 (2025-12-24)
- [x] 동적 스타일 함수 추가 (get_*_style()) (2025-12-24)
- [x] 다이얼로그 테마 지원 (NumberDial) (2025-12-24)
- [x] QStackedWidget 배경색 테마 연동 (2025-12-24)
- [x] FilePreviewPage 아이콘 기반 정보 표시 (2025-12-24)
  - 5개 파라미터: totalLayer, estimatedPrintTime, layerHeight, bottomLayerExposureTime, normalExposureTime
  - 커스텀 아이콘: EXPOSURE_NORMAL (광선+레이어), EXPOSURE_BOTTOM (레이어+바닥선)
- [x] Blade Speed 단위 변경 (2025-12-24)
  - mm/min → mm/s 표시
  - 범위: 10-100 mm/s (실제값 = 표시값 × 50)
- [x] Manual 페이지 다크모드 버튼 수정 (2025-12-24)
  - get_button_control_style(), get_button_home_style() 동적 함수 추가
- [x] Print 페이지 다크모드 버튼 수정 (2025-12-24)
  - get_button_nav_style() 동적 함수 추가
  - btn_up, btn_down, btn_home 테마 지원
- [x] 다크모드 앱 재시작 시 흰색 코너 버그 수정 (2025-12-24)
  - main.py: GLOBAL_STYLE → get_global_style() 동적 함수 사용
  - header.py: right_spacer 배경색 BG_PRIMARY로 변경
- [x] PrintProgressPage 아이콘 기반 정보 표시 (2025-12-24)
  - 9개 정보행을 3열 그리드로 재배치
  - 왼쪽: 현재 레이어(STACK), 경과 시간(CLOCK), 남은 시간(HOURGLASS)
  - 중앙: 레이어 높이(RULER), 바닥 노출(EXPOSURE_BOTTOM), 일반 노출(EXPOSURE_NORMAL)
  - 오른쪽: 바닥 레이어 수(BOTTOM_LAYERS), 블레이드 속도(BLADE_SPEED), LED 파워(LED_POWER)
  - 새 아이콘 추가: BOTTOM_LAYERS, BLADE_SPEED, LED_POWER

---

## 진행 중 (In Progress)

### PrintProgressPage 예상 시간 계산 개선
- [ ] 블레이드 시간 포함한 총 예상 시간 계산
  - 현재: run.gcode의 estimatedPrintTime만 사용 (일반 레진 프린터 기준)
  - 필요: 블레이드 X축 왕복 시간 추가 계산
  - 계산식: `총 시간 = gcode 시간 + (250mm / blade_speed_mm_s) × 총 레이어`
  - 예시: 30mm/s, 100레이어 → 블레이드 시간 ≈ 833초 추가
- [ ] 향후 확장 예정
  - Z축 이동 시간 (5mm 하강/상승)
  - 딜레이 시간 (run.gcode에서 가져올 예정)

---

## 우선순위 가이드

1. **Critical** - 프린팅 불가능한 버그
2. **High** - 사용성에 큰 영향
3. **Medium** - 개선 필요하지만 동작함
4. **Low** - 나중에 해도 되는 기능
