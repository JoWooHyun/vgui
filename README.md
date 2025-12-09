# VERICOM DLP 3D Printer GUI

VERICOM DLP 3D 프린터를 위한 터치스크린 GUI 애플리케이션입니다.

> **Note**: 현재 GUI 프로토타입 단계입니다. UI만 구현되어 있으며, 실제 하드웨어 제어 기능은 추후 추가 예정입니다.

## 개요

| 항목 | 스펙 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| 해상도 | 800 x 480 px |
| 타겟 디바이스 | 7인치 HDMI Touch LCD |
| 보드 | CM4 + Manta M8P 2.0 |
| 프로젝터 | Young Optics NVR2+ |
| 디자인 테마 | Navy (#1E3A5F) + Cyan (#06B6D4) |

## 프린터 특징

- **Top-Down 방식** DLP 프린터
- **Z축**: 빌드 플레이트 상하 이동
- **X축**: 블레이드 수평 이동 (일반 레진프린터와 차별점)
- **LED 노출**: NVR2+ 모듈을 통한 패턴/전체 노출

## 프로젝트 구조

```
vgui/
├── main.py                 # 메인 진입점, 페이지 관리
├── components/             # 재사용 컴포넌트
│   ├── header.py           # 페이지 헤더
│   ├── icon_button.py      # 아이콘 버튼 (MainMenu, Tool, Icon)
│   ├── number_dial.py      # ±버튼 숫자 다이얼
│   └── numeric_keypad.py   # 터치 숫자 키패드
├── pages/                  # 페이지 화면 (12개)
│   ├── main_page.py        # 메인 홈
│   ├── tool_page.py        # 도구 메뉴
│   ├── manual_page.py      # Z축/X축 수동 제어
│   ├── print_page.py       # 파일 목록
│   ├── file_preview_page.py    # 파일 미리보기 + 파라미터 설정
│   ├── print_progress_page.py  # 프린트 진행 모니터링
│   ├── exposure_page.py    # LED 노출 테스트
│   ├── clean_page.py       # 트레이 클리닝
│   ├── system_page.py      # 시스템 설정 메뉴
│   ├── device_info_page.py # 장치 정보
│   ├── language_page.py    # 언어 설정
│   └── service_page.py     # 서비스/고객지원 정보
├── styles/                 # 스타일 정의
│   ├── colors.py           # 컬러 팔레트
│   ├── fonts.py            # 폰트 설정
│   ├── icons.py            # SVG 아이콘
│   └── stylesheets.py      # Qt 스타일시트
└── assets/                 # 이미지, 리소스
```

## 설치

```bash
# 저장소 클론
git clone https://github.com/JoWooHyun/vgui.git
cd vgui

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

## 페이지 네비게이션

```
Main (홈)
├── Tool (도구)
│   ├── Manual      # Z축/X축 수동 제어
│   ├── Exposure    # LED 노출 테스트 (Ramp/Checker, H/V Flip)
│   ├── Clean       # 트레이 청소
│   ├── Set Z=0     # (구현 예정)
│   └── STOP        # 비상 정지
│
├── System (시스템)
│   ├── Device Info # 장치 정보 (해상도, 픽셀 크기, FW 버전 등)
│   ├── Language    # 언어 설정 (English / 한국어)
│   ├── Service     # 서비스 연락처
│   └── Network     # (구현 예정)
│
└── Print (프린트)
    ├── File List       # 파일 목록 (3x2 그리드, 썸네일)
    ├── File Preview    # 미리보기 + Blade Speed/LED Power 설정
    └── Print Progress  # 진행률, 레이어, 시간, PAUSE/STOP
```

## 컴포넌트

| 컴포넌트 | 설명 |
|----------|------|
| Header | 페이지 상단 헤더 (뒤로가기, 타이틀, 액션버튼) |
| IconButton | 60x60px 아이콘 버튼 |
| MainMenuButton | 200x200px 메인 메뉴 버튼 |
| ToolButton | 도구 메뉴용 그리드 버튼 |
| NumberDial | ±1, ±10 버튼으로 값 조절 |
| NumericKeypad | 터치 숫자 키패드 (350x420px) |
| ConfirmDialog | 확인/취소 다이얼로그 |
| EditableRow | 클릭 시 키패드로 값 편집 |

## 컬러 시스템

| 용도 | 색상 | HEX |
|------|------|-----|
| 주요 버튼/텍스트 | Navy | `#1E3A5F` |
| 강조/활성 상태 | Cyan | `#06B6D4` |
| 정지/삭제/경고 | Red | `#DC2626` |
| 시작/완료 | Teal | `#14B8A6` |
| 일시정지/주의 | Amber | `#F59E0B` |
| 주 배경 | White | `#FFFFFF` |
| 보조 배경 | Gray 50 | `#F8FAFC` |

## 진행 현황

| 카테고리 | 완료 | 전체 | 진행률 |
|----------|------|------|--------|
| UI 페이지 | 12 | 12 | 100% |
| 컴포넌트 | 13 | 15 | 87% |
| 하드웨어 연동 | 0 | 4 | 0% |

## TODO (추후 구현)

### Phase 1: 핵심 기능 연동
- [ ] PrintWorker (QThread 기반 프린트 워커)
- [ ] Moonraker API 연동 (모터 제어)
- [ ] NVR2+ I2C 제어 (LED/프로젝터)
- [ ] 실시간 상태 업데이트 (위치/온도)

### Phase 2: 고급 기능
- [ ] 다국어 지원 (영어/한국어 전환)
- [ ] 설정 저장 (JSON)
- [ ] 에러 핸들링
- [ ] 부팅 시 자동 실행 (systemd)

## 디자인 가이드

자세한 디자인 스펙은 [VERICOM_GUI_Design_Guide_v6.md](VERICOM_GUI_Design_Guide_v6.md) 참고

## 라이선스

Private
