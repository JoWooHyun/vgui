# MAZIC CERA GUI

MAZIC CERA DLP 3D 프린터를 위한 터치스크린 GUI 애플리케이션입니다.

## 시스템 사양

| 항목 | 스펙 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| GUI 해상도 | 1024 x 600 px |
| 프로젝터 해상도 | 1920 x 1080 px |
| 타겟 디바이스 | 7인치 HDMI Touch LCD |
| 보드 | CM4 + Manta M8P 2.0 |
| 프로젝터 | Young Optics NVR2+ |
| 모터 제어 | Moonraker API (Klipper) |
| 디자인 테마 | Navy (#1E3A5F) + Cyan (#06B6D4) |

## 프린터 구조

**Top-Down 방식** DLP 3D 프린터

| 축 | 용도 | 범위 | 비고 |
|----|------|------|------|
| Z축 | 빌드 플레이트 상하 이동 | 0~80mm | |
| X축 | 블레이드 수평 이동 (레진 평탄화) | 0~150mm | 리드스크류 |
| Y축 | 시린지 펌프 레진 토출 | 0~91mm (실측) | 50cc 주사기 |
| LED | UV 노출 (NVR2+ 모듈) | 91~1023 | I2C 제어 |
| 밸브 | 레진 공급 밸브 (PF7) | ON/OFF | output_pin |

## 프로젝트 구조

```
vgui/
├── main.py                     # 메인 진입점, 15개 페이지 관리
├── printer.cfg                 # Klipper 설정 (참조용)
├── components/                 # 재사용 UI 컴포넌트
│   ├── header.py               # 페이지 헤더 (뒤로가기 + 타이틀)
│   ├── icon_button.py          # 아이콘 버튼 (6종)
│   ├── number_dial.py          # ±버튼 숫자 다이얼, DistanceSelector
│   └── numeric_keypad.py       # 터치 숫자 키패드 팝업
├── controllers/                # 하드웨어 + 데이터 컨트롤러
│   ├── motor_controller.py     # Moonraker 모터 제어 (Z/X/Y)
│   ├── dlp_controller.py       # NVR2+ DLP/LED 제어 (I2C)
│   ├── gcode_parser.py         # ZIP/G-code 파싱
│   ├── settings_manager.py     # 설정 + 소재 프리셋 관리 (JSON)
│   └── theme_manager.py        # 동적 테마 관리
├── workers/                    # 백그라운드 워커
│   └── print_worker.py         # 프린팅 시퀀스 실행 (QThread)
├── windows/                    # 추가 윈도우
│   └── projector_window.py     # 프로젝터 출력 윈도우 (2차 모니터)
├── pages/                      # GUI 페이지 (15개)
│   ├── base_page.py            # 기본 페이지 (헤더+컨텐츠+푸터)
│   ├── main_page.py            # 0: 메인 홈
│   ├── tool_page.py            # 1: 도구 메뉴
│   ├── manual_page.py          # 2: Z/X/Y축 수동 제어
│   ├── print_page.py           # 3: USB 파일 브라우저
│   ├── exposure_page.py        # 4: LED 노출 테스트 (5패턴)
│   ├── system_page.py          # 5: 시스템 설정 허브
│   ├── device_info_page.py     # 6: 장치 정보
│   ├── language_page.py        # 7: 언어 선택
│   ├── service_page.py         # 8: 서비스 연락처
│   ├── file_preview_page.py    # 9: 파일 미리보기 + 소재 선택
│   ├── print_progress_page.py  # 10: 프린트 진행 상황
│   ├── setting_page.py         # 11: LED/블레이드/Y축 설정
│   ├── theme_page.py           # 12: Light/Dark 테마
│   ├── leveling_page.py        # 13: 3단계 레벨링 가이드
│   └── material_page.py        # 14: 소재 프리셋 관리
├── styles/                     # 스타일 정의
│   ├── colors.py               # 동적 컬러 팔레트 (메타클래스)
│   ├── fonts.py                # 폰트 설정
│   ├── icons.py                # SVG 아이콘 (50+)
│   └── stylesheets.py          # Qt 스타일시트 생성 함수
├── utils/                      # 유틸리티
│   ├── kiosk_manager.py        # 키오스크 모드 + 관리자 접근
│   ├── usb_monitor.py          # USB 디바이스 감지
│   ├── zip_handler.py          # ZIP 파일 처리
│   └── time_formatter.py       # 시간 포맷팅
└── data/
    └── settings.json           # 사용자 설정 영속성
```

## 설치 및 실행

```bash
# Raspberry Pi (실제 환경)
git clone https://github.com/JoWooHyun/vgui.git
cd vgui
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Windows (개발 환경)
git clone https://github.com/JoWooHyun/vgui.git
cd vgui
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py --sim
```

### 실행 옵션

| 옵션 | 설명 |
|------|------|
| `--kiosk` | 키오스크 모드 (전체화면, 커서 숨김) |
| `--windowed` | 윈도우 모드 (개발용) |
| `--sim` | 시뮬레이션 모드 (하드웨어 없이 테스트) |
| `--no-sim` | 실제 하드웨어 모드 |

## 프린팅 워크플로우

```
파일 선택 (USB ZIP) → ZIP 검증 → 소재 선택 (팝업) → 미리보기 (읽기전용) → 프린트 시작
```

### 프린트 시퀀스

1. **초기화**: Z홈 → Z 0.1mm → X홈
2. **프라이밍 체크**: Setting에서 저장된 Y축 프라이밍 위치 확인 (미설정 시 차단)
3. **레이어 루프**:
   - Z축 → 레이어 높이 이동
   - Y축 → 레진 토출 (dispense_distance만큼)
   - X축 → 블레이드 스윕 (140→0, oneway)
   - LED ON → 노광 대기 → LED OFF
   - Z축 → 리프트 (+5mm)
4. **완료/에러**: LED OFF → 사용자 선택 (GUI홈 / Z축홈)

### 레진 소진 감지 (현재 구현)

- Y축 누적 위치가 `Y_MAX_POSITION (91mm)` 도달 시 `resin_empty` 시그널
- 사용자 선택: **Yes** (Y축 비활성화, 수동 공급 모드로 계속) / **No** (출력 종료)
- **알려진 제한**: 소프트웨어 카운터 기반 감지 (홈센서 물리 감지 미구현)

### Y축 프라이밍 시스템

1. Setting 페이지에서 "PRIME" 시작 → `SET_KINEMATIC_POSITION Y=0`으로 좌표 리셋
2. +방향으로 소량 이동하며 레진 나오는 지점 확인
3. 프라이밍 위치 저장 → 출력 시 해당 위치부터 토출 시작

### Y축 프라이밍 미해결 과제

- 현재 `SET_KINEMATIC_POSITION Y=0`은 상대 좌표만 설정 → 홈센서까지 절대 거리를 모름
- `G28 Y` 홈잉은 토출 방향이라 레진 낭비 → 사용 불가
- 주사기 크기(20cc/50cc)나 재사용 여부에 따라 남은 거리가 다름
- 홈센서 물리 감지 방식 전환 검토 중 (gcode_button, 소프트웨어 폴링 등)

## ZIP 파일 형식

```
print_file.zip
├── run.gcode             # 프린트 파라미터 (필수)
├── preview.png           # 썸네일 이미지 (필수)
├── preview_cropping.png  # 크롭된 썸네일 (필수)
├── 1.png ~ N.png         # 레이어 이미지 (연속 번호)
```

### 필수 머신 설정 (run.gcode 내)

```gcode
;resolutionX:1920
;resolutionY:1080
;machineX:124.8
;machineY:70.2
;machineZ:80
```

## 키오스크 모드

- Alt+F4, Alt+Tab, Esc, F1-F11, Windows 키 차단
- 관리자 모드: 로고 5회 클릭 (3초 내) 또는 Ctrl+Shift+F12
- 5분 후 자동 해제

## 테마 시스템

- Light / Dark 2가지 테마 지원
- `Colors` 메타클래스 기반 동적 색상 변경
- `get_*_style()` 함수로 동적 스타일 적용
- 테마 변경 시 `_rebuild_pages()`로 모든 페이지 재생성

## 문서

| 문서 | 내용 |
|------|------|
| [TODO.md](TODO.md) | 미해결 이슈 및 향후 작업 |
| [CODE_REVIEW.md](CODE_REVIEW.md) | 코드 리뷰 및 아키텍처 분석 |
| [FEATURE_SPEC.md](FEATURE_SPEC.md) | 페이지별 기능 상세 정리 |
| [WIREFRAME.md](WIREFRAME.md) | 페이지별 와이어프레임 (ASCII) |
| [DEVELOPMENT_DIARY.md](DEVELOPMENT_DIARY.md) | 개발 다이어리 (버전별 변경 이력) |
| [VERICOM_GUI_Design_Guide_v7.md](VERICOM_GUI_Design_Guide_v7.md) | 디자인 가이드 (최신) |

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| **v4.1** | 2025-04 | Y축 프라이밍 개편: SET_KINEMATIC_POSITION 기반, dir_pin 반전, 테스트 도구 |
| **v4.0** | 2025-04-06 | 소재 프리셋 시스템, Material 페이지, 프린트 플로우 변경 |
| **v3.0** | 2025-02 | Y축 자동 레진 토출, Leveling 페이지, Exposure+Clean 통합, Oneway 블레이드 |
| **v2.0** | 2025-01 | 블레이드 Cycles/Mode 설정, Klipper 자동 복구, 프린트 시퀀스 고도화 |
| **v1.5** | 2025-12-30 | 키오스크 모드, 비동기 모터 제어, 다크모드 완전 지원 |
| **v1.0** | 2025-12-24 | 테마 시스템, PrintProgressPage 리디자인, 코드 리뷰 반영 |
| **v0.5** | 2025-12-19 | 하드웨어 연동, 프린팅 기능, Setting 페이지 |
| **v0.1** | 2025-12-09 | 초기 GUI 프레임워크, 12개 페이지 UI |

## 라이선스

Private - VERICOM
