# VERICOM DLP 3D Printer GUI 디자인 가이드

> **Version:** 4.0  
> **Last Updated:** 2024-12-04  
> **Target Device:** 7인치 터치 LCD (800×480)  
> **Framework:** PySide6  
> **Reference:** UniFormation 프린터 UI 분석 기반

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [컬러 시스템](#2-컬러-시스템)
3. [타이포그래피](#3-타이포그래피)
4. [레이아웃 규칙](#4-레이아웃-규칙)
5. [컴포넌트 가이드](#5-컴포넌트-가이드)
6. [아이콘 가이드](#6-아이콘-가이드)
7. [페이지 구조](#7-페이지-구조)
8. [구현 현황](#8-구현-현황)
9. [TODO 리스트](#9-todo-리스트)
10. [코드 컨벤션](#10-코드-컨벤션)

---

## 1. 프로젝트 개요

### 1.1 하드웨어 환경
| 항목 | 스펙 |
|------|------|
| 디스플레이 | 7인치 HDMI Touch LCD |
| 해상도 | 800 × 480 px |
| 입력방식 | 터치 전용 (마우스/키보드 없음) |
| 보드 | CM4 + Manta M8P 2.0 통합보드 |
| 프로젝터 | Young Optics NVR2+ |

### 1.2 프린터 특징
- **Top-Down 방식** DLP 프린터
- **Z축**: 빌드 플레이트 상하 이동
- **X축**: 블레이드 수평 이동 (일반 레진프린터와 차별점)
- **LED 노출**: NVR2+ 모듈 통해 패턴/전체 노출

### 1.3 디자인 원칙
```
✓ 터치 친화적 - 최소 48×48px 터치 영역
✓ 고대비 - 흰 배경에 네이비/시안 포인트
✓ 플랫 디자인 - 그림자 없이 테두리로 구분
✓ 일관성 - 동일한 컴포넌트는 동일한 스타일
✓ 피드백 - 터치 시 시각적 상태 변화
```

---

## 2. 컬러 시스템

### 2.1 Primary Colors (주요 색상)

| 이름 | HEX | 용도 |
|------|-----|------|
| **Navy** | `#1E3A5F` | 주요 버튼, 텍스트, 아이콘 |
| **Navy Light** | `#2D4A6F` | Navy hover/pressed 상태 |
| **Cyan** | `#06B6D4` | 액센트, 강조, 활성 상태, 선택됨 |
| **Cyan Light** | `#22D3EE` | Cyan hover 상태 |

### 2.2 Semantic Colors (의미적 색상)

| 이름 | HEX | 용도 |
|------|-----|------|
| **Red** | `#DC2626` | 정지, 삭제, 경고 |
| **Teal** | `#14B8A6` | 성공, 시작, 완료 |
| **Amber** | `#F59E0B` | 주의, 일시정지 |

### 2.3 Neutral Colors (중립 색상)

| 이름 | HEX | 용도 |
|------|-----|------|
| **White** | `#FFFFFF` | 주 배경 (BG_PRIMARY) |
| **Gray 50** | `#F8FAFC` | 보조 배경 (BG_SECONDARY) |
| **Gray 100** | `#F1F5F9` | 비활성 배경 (BG_TERTIARY) |
| **Gray 200** | `#E2E8F0` | 테두리 (BORDER) |
| **Gray 500** | `#64748B` | 보조 텍스트 (TEXT_SECONDARY) |
| **Gray 700** | `#334155` | 주요 텍스트 (TEXT_PRIMARY) |

### 2.4 라즈베리파이 주의사항 ⚠️
```
❌ 피해야 할 것:
- background-color: transparent
- rgba 투명도 배경 (일부 케이스에서 검은색으로 표시)

✅ 권장:
- 명시적 배경색 지정 (#FFFFFF, #F8FAFC 등)
- 모든 QLabel에 background-color와 border: none 명시
```

---

## 3. 타이포그래피

### 3.1 폰트 체계

| 이름 | 크기 | 굵기 | 용도 |
|------|------|------|------|
| **Display** | 42px | 700 | 다이얼 숫자 |
| **H1** | 24px | 700 | 큰 숫자, 메인 값 |
| **H2** | 20px | 600 | 메인 버튼 레이블 |
| **H3** | 18px | 600 | 페이지 타이틀, 서브타이틀 |
| **Body** | 16px | 500 | 일반 버튼, 본문 |
| **Body Small** | 14px | 500 | 보조 정보 |
| **Caption** | 12px | 400 | 힌트, 레이블 |

---

## 4. 레이아웃 규칙

### 4.1 화면 구조
```
┌─────────────────────────────────────────────────────┐
│                    Header (56px)                     │
│  [Back]           Title                    [Action]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│                  Content Area                        │
│                   (404px)                            │
│                                                      │
├─────────────────────────────────────────────────────┤
│              Footer/Navigation (20px padding)        │
└─────────────────────────────────────────────────────┘

전체: 800 × 480px
Header: 56px 높이
Content: 나머지 영역 (padding 20px)
```

### 4.2 간격 시스템

| 토큰 | 크기 | 용도 |
|------|------|------|
| `xs` | 4px | 아이콘-텍스트 간격 |
| `sm` | 8px | 밀접한 요소 간격 |
| `md` | 12px | 일반 요소 간격 |
| `lg` | 16px | 섹션 내 간격 |
| `xl` | 20px | 콘텐츠 패딩 |
| `2xl` | 24px | 큰 섹션 간격 |

### 4.3 터치 영역 규칙
```
최소 터치 영역: 48 × 48px
권장 버튼 크기: 60 × 60px 이상
메인 버튼 크기: 200 × 200px
일반 버튼 높이: 50px
```

---

## 5. 컴포넌트 가이드

### 5.1 버튼 종류

| 타입 | 용도 | 스타일 |
|------|------|--------|
| **Primary** | 주요 액션 (START) | Navy 배경 + 흰 텍스트 |
| **Secondary** | 보조 액션 | 흰 배경 + 테두리 |
| **Danger** | 위험 액션 (STOP, Delete) | Red 테두리/배경 |
| **Accent** | 강조 액션 (Start Print) | Cyan 배경 + 흰 텍스트 |
| **Icon Button** | 아이콘 전용 | 60×60px, 둥근 모서리 |
| **Main Menu** | 메인 화면 | 200×200px |
| **Tool Button** | 도구 메뉴 | 그리드 배치 |

### 5.2 숫자 입력 다이얼 (NumberDial)
```
┌─────────────────────────────────────┐
│              Title                   │
├─────────────────────────────────────┤
│     [-10]  [-1]  [+1]  [+10]        │
│                                      │
│           10.5 sec                   │
│                                      │
│   [Cancel]            [Confirm]      │
└─────────────────────────────────────┘
```

### 5.3 테이블 컴포넌트 (InfoRow)
```
┌─────────────────────────────────────┐
│ 항목 (헤더)       │ 값 (헤더)        │
├───────────────────┼─────────────────┤
│ Print Size        │ 192×108×200 mm  │
│ Resolution        │ 3840×2160 (4K)  │
└───────────────────┴─────────────────┘
```

### 5.4 알림창 (SimpleAlert)
```
┌─────────────────────────┐
│                         │
│      메시지 텍스트       │
│                         │
│        [ OK ]           │
│                         │
└─────────────────────────┘
```

### 5.5 확인 다이얼로그 (ConfirmDialog) ✅ NEW
```
┌─────────────────────────────┐
│         Delete File          │
│                              │
│  Are you sure you want to    │
│  delete 'filename.zip'?      │
│                              │
│   [Cancel]     [Delete]      │
└─────────────────────────────┘

- Cancel: 회색 배경
- Delete: 빨간 배경
```

### 5.6 파일 아이템 (FileItem) ✅ NEW
```
┌──────────────────────┐
│      ┌────────┐      │
│      │ 썸네일  │      │  100×100px
│      └────────┘      │
│      파일명.zip       │
└──────────────────────┘

- 비선택: 회색 테두리 2px
- 선택됨: Cyan 테두리 3px + 파일명 Cyan 색상
```

---

## 6. 아이콘 가이드

### 6.1 구현된 아이콘

| 카테고리 | 아이콘 | 용도 |
|----------|--------|------|
| **네비게이션** | ARROW_LEFT, ARROW_UP, ARROW_DOWN, HOME, CHEVRON_UP, CHEVRON_DOWN | 방향, 홈 |
| **액션** | PLAY, PAUSE, STOP_CIRCLE | 재생 제어 |
| **도구** | WRENCH, SETTINGS, MOVE | 설정, 도구 |
| **형태** | SQUARE, SQUARE_HALF, LAYERS | 패턴, 레이어 |
| **시스템** | INFO, GLOBE, MAIL, WIFI | 시스템 메뉴 |
| **파일** | FILE, FILE_TEXT, FOLDER_OPEN | 파일 관련 |
| **Exposure** | PATTERN_RAMP, PATTERN_CHECKER | 테스트 패턴 |
| **Flip** | FLIP_HORIZONTAL, FLIP_VERTICAL | 이미지 반전 |

### 6.2 아이콘 스타일
```
형식: SVG (stroke 기반)
기본 크기: 24×24px
선 굵기: 2px
색상: 동적 (color 파라미터)
```

---

## 7. 페이지 구조

### 7.1 네비게이션 맵

```
Main (L0)
├── Tool (L1)
│   ├── Manual (L2) ────────────── Z축/X축 수동 제어
│   ├── Exposure (L2) ──────────── LED 노출 테스트 ✅
│   │   └── Ramp/Checker + H/V Flip + 시간 설정
│   ├── Clean (L2) ─────────────── 트레이 청소 ✅
│   │   └── 시간 설정 + START/STOP
│   ├── Set Z=0 (알림창) ────────── "아직 구현중" ✅
│   └── STOP (즉시 실행) ────────── 비상 정지
│
├── System (L1) ✅
│   ├── Device Info (L2) ────────── 장치 정보 ✅
│   │   └── Print Size, Resolution, Pixel Size, FW Version, Model
│   ├── Language (L2) ───────────── 언어 설정 ✅
│   │   └── English / 한국어
│   ├── Service (L2) ────────────── 서비스 정보 ✅
│   │   └── Email, Website, Tel
│   └── Network (알림창) ─────────── "구현중입니다" ✅
│
└── Print (L1) ✅
    ├── File List (L2) ──────────── 파일 목록 (3×2 그리드) ✅
    │   └── 썸네일 + 파일명, Open 버튼으로 이동
    ├── File Preview (L2) ───────── 파일 미리보기 ✅
    │   └── 썸네일, 파라미터 정보, Delete/Start 버튼
    └── Print Progress (L2) ─────── 인쇄 진행 ❌
```

### 7.2 페이지 인덱스 (main.py)

| 인덱스 | 페이지 | 설명 |
|--------|--------|------|
| 0 | MainPage | 메인 홈 |
| 1 | ToolPage | 도구 메뉴 |
| 2 | ManualPage | 수동 제어 |
| 3 | PrintPage | 파일 선택 |
| 4 | ExposurePage | 노출 테스트 |
| 5 | CleanPage | 트레이 청소 |
| 6 | SystemPage | 시스템 메뉴 |
| 7 | DeviceInfoPage | 장치 정보 |
| 8 | LanguagePage | 언어 설정 |
| 9 | ServicePage | 서비스 정보 |
| 10 | FilePreviewPage | 파일 미리보기 ✅ NEW |

---

## 8. 구현 현황

### 8.1 완료된 스타일/컴포넌트 ✅

| 카테고리 | 항목 | 파일 |
|----------|------|------|
| **Styles** | Colors, Fonts, Icons, Stylesheets | styles/*.py |
| **Components** | Header, IconButton, ControlButton | components/*.py |
| **Components** | MainMenuButton, ToolButton | icon_button.py |
| **Components** | NumberDial, DistanceSelector | number_dial.py |
| **Components** | SimpleAlert | tool_page.py, system_page.py |
| **Components** | ConfirmDialog | file_preview_page.py ✅ NEW |
| **Components** | FileItem (썸네일+파일명) | print_page.py ✅ NEW |
| **Components** | InfoRow | file_preview_page.py ✅ NEW |

### 8.2 완료된 페이지 ✅

| 페이지 | 파일 | 기능 |
|--------|------|------|
| **MainPage** | main_page.py | Tool, System, Print 버튼 |
| **ToolPage** | tool_page.py | 6개 버튼 그리드 + Set Z=0 알림 |
| **ManualPage** | manual_page.py | Z축/X축 제어 패널 |
| **PrintPage** | print_page.py | 파일 목록 (그리드) + 썸네일 + Open 버튼 |
| **ExposurePage** | exposure_page.py | Ramp/Checker, Flip, 시간 |
| **CleanPage** | clean_page.py | 시간 설정 + START/STOP |
| **SystemPage** | system_page.py | 4개 버튼 + Network 알림 |
| **DeviceInfoPage** | device_info_page.py | 장치 정보 테이블 |
| **LanguagePage** | language_page.py | 영어/한국어 선택 |
| **ServicePage** | service_page.py | 연락처 정보 |
| **FilePreviewPage** | file_preview_page.py | 미리보기 + 정보 + Delete/Start ✅ NEW |

### 8.3 NVR2+ 명령값 (ExposurePage)

| 항목 | 레지스터 | 값 |
|------|----------|-----|
| Pattern | 0x05 | Ramp=0x01, Checker=0x07 |
| Flip | 0x14 | None=0x00, H=0x02, V=0x04, HV=0x06 |

### 8.4 USB 파일 스캔 ✅ NEW

```python
# 3단계 스캔 구조
/media/
  └── {user}/           # 예: veri
        └── {device}/   # 예: 6C0F-5149 (USB 장치)
              └── *.zip # DLP 프린터 파일

# 지원 확장자
['.zip', '.dlp', '.photon', '.ctb']
```

### 8.5 ZIP 파일 파라미터 추출 ✅ NEW

```python
# run.gcode에서 추출하는 파라미터
- totalLayer: 총 레이어 수
- bottomLayerCount: 바닥 레이어 수
- bottomLayerExposureTime: 바닥 노출 시간 (초)
- normalExposureTime: 일반 노출 시간 (초)
- normalLayerLiftHeight: 리프트 높이 (mm)
- normalLayerLiftSpeed: 리프트 속도 (mm/min)

# 썸네일 이미지 우선순위
1. preview_cropping.png
2. preview.png
3. thumbnail.png
```

---

## 9. TODO 리스트

### 9.1 Phase 1: 추가 컴포넌트 (⭐⭐⭐)

| 항목 | 설명 | 상태 |
|------|------|------|
| ~~Confirm Dialog~~ | 정지/삭제 확인 팝업 | ✅ 완료 |
| Toggle Switch | ON/OFF 설정용 | ❌ |
| Slider | 범위 값 조절용 | ❌ |

### 9.2 Phase 2: 인쇄 관련 페이지 (⭐⭐⭐)

| 페이지 | 설명 | 상태 |
|--------|------|------|
| ~~File Preview~~ | 파일 미리보기 + 정보 + 시작 | ✅ 완료 |
| **Print Progress** | 인쇄 진행 모니터링 | ❌ 다음 우선 |
| Print Settings | 인쇄 중 설정 (탭 UI) | ❌ |

### 9.3 Phase 3: 하드웨어 연동 (⭐⭐)

| 항목 | 설명 | 상태 |
|------|------|------|
| Moonraker API | 모터 제어 연동 | ❌ |
| NVR2+ I2C | LED/프로젝터 제어 | ❌ |
| ~~USB 파일 스캔~~ | 3단계 스캔 구현 | ✅ 완료 |
| 실시간 상태 | 위치/온도 업데이트 | ❌ |

### 9.4 Phase 4: 고급 기능 (⭐)

| 항목 | 설명 | 상태 |
|------|------|------|
| 다국어 지원 | 영어/한국어 텍스트 전환 | ❌ |
| 설정 저장 | JSON 파일로 설정 유지 | ❌ |
| 에러 핸들링 | 오류 알림 및 복구 | ❌ |
| 부팅 자동 실행 | systemd 서비스 등록 | ❌ |

### 9.5 제외 항목 (오프라인 환경)
- ~~클라우드 서비스~~
- ~~시스템 업데이트~~
- ~~가열/예열~~ (Top-Down 방식에서 불필요)

---

## 10. 코드 컨벤션

### 10.1 파일 구조
```
vgui/
├── main.py                 # 진입점, 페이지 관리
├── styles/
│   ├── colors.py           # 컬러 상수
│   ├── fonts.py            # 폰트 설정
│   ├── icons.py            # SVG 아이콘
│   └── stylesheets.py      # QSS 스타일시트
├── components/
│   ├── header.py
│   ├── icon_button.py
│   └── number_dial.py
├── pages/
│   ├── base_page.py
│   ├── main_page.py
│   ├── tool_page.py
│   ├── manual_page.py
│   ├── print_page.py       ✅ 업데이트 (썸네일+Open)
│   ├── exposure_page.py    ✅
│   ├── clean_page.py       ✅
│   ├── system_page.py      ✅
│   ├── device_info_page.py ✅
│   ├── language_page.py    ✅
│   ├── service_page.py     ✅
│   └── file_preview_page.py ✅ NEW
└── assets/
```

### 10.2 명명 규칙
```python
# 클래스: PascalCase
class MainPage(QWidget):

# 메서드: snake_case (private: _prefix)
def _setup_content(self):

# 상수: UPPER_SNAKE_CASE
NAVY = "#1E3A5F"

# 위젯 변수: prefix_name
self.btn_start = QPushButton()
self.lbl_title = QLabel()
```

### 10.3 시그널 명명
```python
go_back = Signal()           # 페이지 이동
go_home = Signal()
file_selected = Signal(str)  # 데이터 전달
value_changed = Signal(float)
exposure_start = Signal(int, bool, bool, float)  # 복합 데이터
start_print = Signal(str, dict)  # 파일경로, 파라미터
file_deleted = Signal(str)       # 삭제된 파일경로
```

### 10.4 새 페이지 추가 체크리스트
```
□ BasePage 상속
□ __init__에서 super().__init__(title, show_back=True)
□ _setup_content() 메서드 구현
□ go_back 시그널 자동 포함 (BasePage)
□ pages/__init__.py에 import 추가
□ main.py에 페이지 인덱스, 생성, 시그널 연결 추가
□ 라즈베리파이에서 테스트 (transparent 배경 주의)
```

---

## 📜 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2024-12 | 초기 버전 |
| 2.0 | 2024-12 | UniFormation 분석 반영, 컴포넌트 추가 |
| 3.0 | 2024-12-02 | Tool/System 페이지 완료, 10개 페이지 구현 |
| 4.0 | 2024-12-04 | Print 플로우 완료 (PrintPage 개선, FilePreviewPage 추가), 11개 페이지 |

---

## 📊 진행률 요약

| 카테고리 | 완료 | 전체 | 진행률 |
|----------|------|------|--------|
| 페이지 | 11 | 12 | 92% |
| 컴포넌트 | 8 | 10 | 80% |
| 하드웨어 연동 | 1 | 4 | 25% |
| 고급 기능 | 0 | 4 | 0% |

**다음 우선순위:** Print Progress 페이지 구현

---

> **Note:** 이 가이드는 프로젝트 진행에 따라 업데이트됩니다.
