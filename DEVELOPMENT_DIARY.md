# MAZIC CERA GUI - 개발 다이어리

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | MAZIC CERA DLP 3D Printer GUI |
| 개발 시작 | 2025-12-09 |
| 프레임워크 | PySide6 (Qt for Python) |
| 대상 장치 | 7인치 HDMI Touch LCD (1024x600) |
| 프로젝터 | Young Optics NVR2+ (1920x1080) |
| 모터 제어 | Klipper + Moonraker (Manta M8P 2.0) |

---

## v0.1 - 초기 GUI 프레임워크 (2025-12-09 ~ 12-16)

### 2025-12-09 | 프로젝트 시작
- Initial commit: VERICOM DLP 3D Printer GUI v2.0 기본 구조 생성
- README.md 및 requirements.txt 작성
- 프로젝트 구조 설계 완료

### 2025-12-16 | 하드웨어 연동
- 하드웨어 컨트롤 모듈 추가 (motor_controller, dlp_controller)
- main.py와 하드웨어 컨트롤러 통합
- 실제 장치 운용을 위한 하드웨어 컨트롤러 수정

---

## v0.5 - 하드웨어 연동 및 프린팅 (2025-12-19 ~ 12-23)

### 2025-12-19 | 프린팅 기능 디버깅
- 시뮬레이션 모드 OFF로 실제 하드웨어 테스트 시작
- DLP 재초기화 문제, 레이어 카운트 파싱 버그 수정
- PNG 파일 카운팅 개선 (서브폴더 지원)
- PrintWorker에 totalLayer 전달 누락 버그 수정

### 2025-12-22 | UI/UX 개선
- VERICOM 로고 GUI에 추가
- "SET Z=0" → "Calibration"으로 이름 변경 + 새 아이콘
- Clean 페이지 시간 표시 및 프로젝터 해상도 수정

### 2025-12-23 | Setting 및 Exposure 페이지 완성
- LED 파워 변환 로직 수정 (퍼센트 → 실제값)
- Exposure 페이지 리팩토링 (아이콘 버튼 + 로고 패턴)
- **Setting 페이지 신규 추가** (LED Power, Blade 컨트롤)
- Language, Device Info, Service 페이지 정비
- Manual 페이지 리팩토링
- Design Guide v7.1

---

## v1.0 - 테마 시스템 및 코드 리뷰 (2025-12-24 ~ 12-29)

### 2025-12-24 | 테마 시스템 대규모 업데이트
- **Theme 페이지 신규 추가** (Light/Dark)
- 실시간 테마 전환 구현 (Colors 메타클래스 + ThemeManager 싱글톤)
- SettingsManager에 테마 지원 추가
- 모든 다이얼로그에 동적 테마 적용
- FilePreviewPage 정보 표시 아이콘 기반으로 변경
- **PrintProgressPage 대규모 리디자인**
  - 아이콘 기반 정보 표시
  - 블레이드 시간을 예상 프린트 시간에 포함
  - 레이아웃 단순화 (프리뷰 왼쪽, 정보 오른쪽)
- 앱 재시작 시 다크모드 테마 유지 버그 수정

### 2025-12-29 | 코드 리뷰 및 버그 수정
- **코드 리뷰 완료**: Critical/High 우선순위 버그 수정
  - 블레이드 속도 단위 변환 버그 (×60 → ×50 통일)
  - show_image 시그널을 PrintProgressPage에 연결
  - 이미지 로드 실패 시 3회 재시도 + 프린트 중지
  - 모터 에러 체크 및 처리
  - 정지/에러 시 X축만 홈 복귀 (Z축 위치 유지)
- ZIP 파일 검증 추가 (run.gcode, 머신설정, 미리보기, 레이어 연속성)
- ZipErrorDialog, StoppedDialog, ErrorDialog 추가
- 홈 이동 타임아웃 100초 → 120초 증가

---

## v1.5 - 키오스크 모드 및 다크모드 완성 (2025-12-30 ~ 12-31)

### 2025-12-30 | 키오스크 모드 및 안전 기능
- **키오스크 모드 추가** (`utils/kiosk_manager.py`)
  - Alt+F4, Alt+Tab, Esc, F1-F11, Windows 키 차단
  - 관리자 모드: 로고 5회 클릭 (3초 내) 또는 Ctrl+Shift+F12
  - 5분 후 자동 해제
- **비동기 모터 제어** (MotorWorker QThread) - GUI 프리징 방지
- Z/X축 위치 제한 추가 (안전 기능)
- **모든 페이지 및 다이얼로그 다크모드 완전 지원**
  - 정적 스타일시트 → 동적 get_*_style() 함수로 전환
  - manual_page, setting_page, numeric_keypad, icon_button 등
- Design Guide v7.4

### 2025-12-31 | 마무리 및 안정화
- STOP 버튼: emergency_stop → quickstop으로 변경
- Exposure/Clean 페이지 버그 수정:
  - 패턴 표시 전 데스크탑 노출 방지
  - LED 파워 스케일 수정 (1023 = 100%)
  - 프로젝터 ON 순서 수정

---

## v2.0 - 프린팅 시퀀스 고도화 (2025-01)

### 프로젝터 및 블레이드 개선
- 프로젝터 앱 수명주기 내 상시 ON (데스크탑 플래시 방지)
- LED ON 전 150ms 딜레이 추가
- **블레이드 모션**: round-trip 모드 도입, Cycles 설정 (1~3회), Mode 설정 (roundtrip/oneway)
- X축 400 에러 수정 (절대 이동 전 자동 호밍)

### Klipper 통합 강화
- **일시정지 개선**: 노출 완료 후 일시정지, Klipper idle timeout 방지
- Klipper CANCEL_PRINT, CLEAR_PAUSE 통합
- **Klipper 자동 복구**: 장시간 일시정지 후 shutdown 상태 → 자동 firmware restart

### 기타
- X축 리드스크류 변환에 따른 속도 조정
- X축 블레이드 방향 반전 (새 홈 위치 150mm)
- 예상 프린트 시간 계산 정확도 개선

---

## v3.0 - Y축 레진 공급 및 UI 개편 (2025-01~02)

### Y축 자동 레진 공급 시스템
- **자동 레진 공급** 추가 (시린지 펌프, Y축 모터)
  - MANUAL_STEPPER → 표준 G-code 전환
  - 레이어당 자동 토출 (거리/속도/딜레이 설정 가능)
- Y축 펌프 제어를 Manual 페이지에 추가
- 솔레노이드 밸브 시도 → 실패 → Y축 모터 방식으로 복귀
- 프로젝터 수평 미러링 수정
- **Y축 50cc 보정**: 홈(~60cc) → 6mm 이동 → 50cc 시작점 보정
- 80mm 한계 도달 시 레진 부족 알림 + 사용자 선택

### UI 리팩토링
- Exposure + Clean 페이지 통합 (5패턴)
- **Leveling 페이지 신규 추가** (3단계 가이드 시퀀스)
- Setting 페이지 3패널 레이아웃 (LED/Blade/Y축)
- Manual 페이지 3축 제어 (Z/X/Y)
- Tool 페이지 수평 레이아웃 변경 (STOP 버튼 제거)
- NumericKeypad 스타일 개선 및 테마 지원
- 모터 동시 G-code 명령 지원 (작업 락 제거)

### 프린트 시퀀스 최적화
- 초기화 순서: Z홈 → Z 0.1mm → X홈 → 레벨링
- Oneway 블레이드 모드로 전환
- Y축 자동 토출 프린트 워크플로우 통합

---

## v4.0 - 소재 프리셋 시스템 (2025-04-06)

### Material 페이지 신규 추가
- **좌측**: 프리셋 리스트 (추가/삭제/선택)
- **우측**: 9개 파라미터 편집 (클릭하여 수정)
- 기본 소재: Zirconia, Alumina, Hydroxyapatite

### 프린트 플로우 변경
- 파일 선택 → **소재 선택 팝업 (MaterialSelectDialog)** → 미리보기 (읽기전용)
- FilePreviewPage: EditableRow → ReadOnlyRow로 변경
- MaterialPreset dataclass (9개 필드): blade_speed, led_power, blade_cycles, y_dispense_distance, y_dispense_speed, y_dispense_delay, leveling_cycles, lift_height, drop_speed

### 기타
- Manual 페이지 확장: Y축 "Resin Feeder" 패널 추가
- Tool 페이지에 Material 버튼 추가
- SettingsManager에 소재 CRUD 메서드 추가
- Material 프리셋 UI 라벨 정리, 기본값 조정

---

## v4.1 - Y축 프라이밍 시스템 개편 (2025-04)

### 프라이밍 로직 변경
- **Y축 홈잉 제거**: 프라이밍에서 G28 Y 사용하지 않음
- **SET_KINEMATIC_POSITION Y=0** 기반 좌표 리셋으로 전환
- 프라이밍 시 +방향으로만 이동 (- 버튼 비활성화)
- 프라이밍 위치 저장 → 출력 시 확인 팝업 (미설정 시 출력 차단)

### dir_pin 및 방향 수정
- dir_pin 반전 (printer.cfg: `!PE1`)으로 +방향 = 레진 토출
- G92 Y0 → SET_KINEMATIC_POSITION Y=0으로 완전 전환
- 음수 Y축 이동 허용 (G92 리셋 후)

### 도구 추가
- `test_y_priming.py`: Y축 프라이밍 동작 테스트 도구

### 미해결 과제 (진행 중)
- SET_KINEMATIC_POSITION Y=0은 상대 좌표만 설정 → 홈센서 기준 절대 위치 모름
- G28 Y 홈잉은 토출 방향이라 레진 낭비 → 사용 불가
- 주사기 크기별/재사용 시 남은 거리 파악 불가
- 레진 소진 감지: 소프트웨어 카운터(91mm) vs 홈센서 물리 감지 방식 검토 중
  - Klipper는 일반 G1 이동 중 엔드스톱 무시 (G28 때만 감지)
  - gcode_button, 소프트웨어 폴링, filament_switch_sensor 등 대안 조사 완료

---

## v4.2 - 프린트 안전성 강화 및 UI 개선 (2025-04-30)

### 프린트 시퀀스 안전성 개선
- **LED 즉시 OFF**: 정지(stop) 요청 시 노출 대기 중 즉시 LED OFF 및 이미지 클리어
  - `_wait_exposure()`에서 stop 감지 시 `_dlp_led_off()` + `clear_image.emit()` 호출
- **초기 레진 토출**: 레벨링(평탄화) 전 레진 토출 1회 추가
  - 레진 없이 평탄화가 수행되는 문제 해결
- **프로젝터 윈도우 관리**: exposure 정지 시 `close()` 대신 `clear_screen()` 사용
  - 페이지 나갈 때만 `close()` 호출 → 데스크탑 플래시 방지

### 입력 제한 범위 변경
- **Blade Speed**: Material 페이지 최대 30→100 mm/s, Setting 페이지 최대 15→100 mm/s
- **Resin Delay**: Material 페이지 최대 20→60→300초 (5분)
- **Manual X-axis 속도**: 기본값 5→10 mm/s (300→600 mm/min)

### X축 관련 수정
- **X-axis max position**: 코드에서 150→140mm으로 수정 (printer.cfg position_max=140 기준)
- **Manual X-axis 속도 컨트롤**: NumericKeypad로 속도 직접 입력 (최소 5mm/s, 기본 10mm/s)
  - `x_move` 시그널을 `Signal(float, int)`로 변경 (거리 + 속도)

### UI 변경
- **DistanceSelector → NumericKeypad**: Manual/Setting 페이지의 축 거리 선택을 버튼식에서 직접 입력으로 변경
  - 0.05~10.0mm 범위, 소수점 입력 지원
- **예상 프린트 시간 재계산**: 레진 토출 시간, 정확한 X 이동 거리(130mm×2), 레벨링 시간 모두 포함

---

## v5.0 - Push-Pull 3단계 토출 및 레진 소모 UI 개선 (2025-05-26)

### Push-Pull 3단계 레진 토출 시퀀스
- **`_dispense_3step()` 메서드 추가**: test_vgui에서 검증된 Mode 3 토출 시퀀스 이식
  - Step 1: Push (Y축 -방향 토출) → 즉시 레진 소진 감지
  - Step 2: Pull (Y축 +방향 되돌리기, distance=0이면 스킵)
  - Step 3: Return (Y축 -방향 다시 밀기, distance=0이면 스킵)
- **Pull/Return 속도 자동 계산**: `distance / delay × 60` (mm/min)
- **기존 호환성 유지**: Pull/Return=0이면 기존과 동일하게 Push만 동작

### MaterialPreset 필드 개편
- **제거**: blade_cycles, leveling_cycles, lift_height, drop_speed
- **추가**: y_pull_distance, y_pull_delay, y_return_distance, y_return_delay
- Material 페이지 UI 업데이트 (Pull/Return 파라미터 행 추가)
- settings_manager.py 로드/저장 로직 업데이트

### 레진 소모 팝업 UI 개선
- **기존**: ConfirmDialog 팝업 ("Continue printing?") → OK/NO
- **변경**: PrintProgressPage 내 버튼 직접 표시
  - "주사기 리필" (초록): 주사기 교체 후 Klipper Y위치 읽어 토출 재개
  - "수동배급" (시안): Y축 비활성화, 대기시간만 유지하며 계속
  - "STOP" (빨강): 출력 중지
- `refill_completed`, `manual_feed_selected` 시그널 추가

### 즉시 레진 소진 감지
- **기존**: 다음 레이어 시작 시 감지 → 불완전 토출로 인한 블레이드/노출 계속 진행
- **변경**: Push 직후 position ≤ 0이면 즉시 감지 → 블레이드/노출 전에 사용자 선택

### 기타
- `_motor_y_move()` 반환값: `bool` → `tuple(bool, float)` (성공여부, 실제이동거리)
- `_wait_interruptible()` 헬퍼 추가 (대기 중 stop 감지)
- `refill_resin(new_y_position)` 메서드 추가
- Y축 max position 125→130mm 증가
- DLP 수평 미러링(flip) 기동 시 비활성화

---

## 개발 통계

| 항목 | 수치 |
|------|------|
| 총 커밋 수 | 170개+ |
| 개발 기간 | 2025-12-09 ~ 현재 |
| 주요 페이지 | 15개 |
| 컴포넌트 | 4개 |
| 컨트롤러 | 5개 |
| 소재 프리셋 | 3개 기본 (Zirconia, Alumina, Hydroxyapatite) |

---

## 기술적 도전과 해결

### 1. GUI 프리징 문제
- **문제**: 모터 제어 시 GUI가 멈춤
- **해결**: QThread 기반 MotorWorker로 비동기 처리

### 2. 다크모드 일관성
- **문제**: 일부 페이지/다이얼로그가 테마 미적용
- **해결**: Colors 메타클래스로 동적 색상 변경, get_*_style() 함수 패턴

### 3. LED 타이밍 이슈
- **문제**: 프로젝터 ON 전 데스크탑 화면 노출
- **해결**: 앱 수명주기 내 프로젝터 상시 ON + LED만 ON/OFF 제어

### 4. ZIP 파일 호환성
- **문제**: 다양한 슬라이서 출력 파일 형식 차이
- **해결**: 필수 조건 검증 시스템 (머신 설정, 레이어 연속성)

### 5. Klipper 장시간 일시정지
- **문제**: 일시정지 중 Klipper idle_timeout으로 shutdown
- **해결**: PAUSE 알림, 재개 시 shutdown 감지 → firmware_restart → 재홈

### 6. Y축 레진 토출 보정
- **문제**: Y축 홈 위치(~60cc)와 시린지 용량(50cc) 불일치
- **해결**: 홈 후 6mm 오프셋 이동으로 50cc 시작점 보정

### 7. 소재별 설정 관리
- **문제**: 소재마다 다른 프린트 파라미터를 매번 수동 설정
- **해결**: MaterialPreset 시스템으로 소재별 프리셋 저장/로드

### 8. Y축 프라이밍 위치 파악 (미해결)
- **문제**: 홈잉 없이 홈센서 기준 절대 위치를 알 수 없음
- **제약**: G28 Y는 토출 방향이라 레진 낭비, Klipper는 G1 중 엔드스톱 무시
- **검토 중**: gcode_button (별도 핀), 소프트웨어 폴링, 토출 방향 반전 등

### 9. 정지 시 LED 안전 (해결)
- **문제**: 노출 중 정지 요청 시 LED가 꺼지지 않고 대기 시간이 끝날 때까지 유지
- **해결**: `_wait_exposure()`에서 stop 감지 즉시 `_dlp_led_off()` 호출

### 10. 레진 없이 평탄화 (해결)
- **문제**: 초기화 단계에서 레진 토출 없이 블레이드 평탄화 수행
- **해결**: 레벨링 전 초기 레진 토출 1회 추가

### 11. 불완전 토출로 인한 출력 실패 (해결)
- **문제**: 레진 소진 시 Push 완료 후 블레이드/노출까지 진행하여 불완전 레이어 생성
- **해결**: Push 직후 position ≤ 0이면 즉시 resin_empty 감지, 블레이드/노출 전에 사용자 선택

### 12. 레진 소모 시 팝업 사용성 (해결)
- **문제**: ConfirmDialog 팝업으로 레진 소모 알림 → 선택지가 불명확
- **해결**: PrintProgressPage 내에 "주사기 리필" / "수동배급" / "STOP" 버튼 직접 표시
