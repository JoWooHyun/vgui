# VERICOM DLP 3D Printer GUI 디자인 가이드

> **Version:** 7.1
> **Last Updated:** 2025-12-23
> **Target Device:** 7인치 터치 LCD (1024×600)
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
| 해상도 | 1024 × 600 px |
| 입력방식 | 터치 전용 (마우스/키보드 없음) |
| 보드 | CM4 + Manta M8P 2.0 통합보드 |
| 프로젝터 | Young Optics NVR2+ |
| 모델명 | MAZIC CERA |
| 출력 영역 | 124.8 x 70.2 x 80 mm |
| 픽셀 | 65 μm |
| 펌웨어 | V 2.0.0 |

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
| **Amber** | `#F59E0B` | 주의, 일시정지, Backspace |

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
- background-color: transparent (자식에게 상속됨)
- rgba 투명도 배경 (일부 케이스에서 검은색으로 표시)
- QFrame 자식 QLabel에 border 스타일 미지정

✅ 권장:
- 명시적 배경색 지정 (#FFFFFF, #F8FAFC 등)
- 모든 QLabel에 background-color: transparent; border: none 명시
- QFrame 내부 요소에 스타일 상속 방지
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

전체: 1024 × 600px
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
키패드 버튼: 70 × 55px
```

---

## 5. 컴포넌트 가이드

### 5.1 버튼 종류

| 타입 | 용도 | 스타일 |
|------|------|--------|
| **Primary** | 주요 액션 (START) | Navy 배경 + 흰 텍스트 |
| **Secondary** | 보조 액션 | 흰 배경 + 테두리 |
| **Danger** | 위험 액션 (STOP, Delete) | Red 테두리/배경 |
| **Accent** | 강조 액션 (Start Print, Confirm) | Cyan 배경 + 흰 텍스트 |
| **Warning** | 주의 액션 (PAUSE) | Amber 배경 + 흰 텍스트 |
| **Icon Button** | 아이콘 전용 | 60×60px, 둥근 모서리 |
| **Main Menu** | 메인 화면 | 200×200px |
| **Tool Button** | 도구 메뉴 | 그리드 배치 |
| **Keypad Button** | 숫자 키패드 | 70×55px, Navy 배경 |

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

### 5.3 숫자 키패드 (NumericKeypad) ✅
```
┌──────────────────────────────────┐
│          Blade Speed              │
│                                   │
│     ┌────────────────────┐       │
│     │    1500  mm/min    │       │  ← Cyan 테두리
│     └────────────────────┘       │
│                                   │
│      [1]   [2]   [3]             │  ← Navy 배경, 70×55px
│      [4]   [5]   [6]             │
│      [7]   [8]   [9]             │
│      [⌫]   [0]   [C]             │  ← Amber / Red
│                                   │
│    [Cancel]      [Confirm]        │
└──────────────────────────────────┘

- 다이얼로그 크기: 350×420px
- 버튼 간격: 8px
- 범위 초과 시 빨간 테두리 피드백
```

### 5.4 정보 행 (InfoRow / ProgressInfoRow)
```
┌──────────────────────────────────┐
│ Total Time              16.8 min │  ← 값 우측 정렬
│ Normal Exp.              3.0 sec │
│ Bottom Exp.              5.0 sec │
└──────────────────────────────────┘
```

### 5.5 편집 가능 행 (EditableRow) ✅
```
┌──────────────────────────────────────────┐
│ Blade Speed         1500 mm/min       ✎ │  ← Cyan 테두리 + EDIT 아이콘
└──────────────────────────────────────────┘

- 클릭 시 NumericKeypad 팝업
- 라벨 폭: 110px
- EDIT 아이콘: 18px
```

### 5.6 진행률 바 (QProgressBar) ✅ NEW
```
┌────────────────────────────────────────────────┐
│████████████████░░░░░░░░░░░░░░░░░░░░░░   45%    │
└────────────────────────────────────────────────┘

- 높이: 24px
- 채움 색상: Cyan
- 배경 색상: BG_TERTIARY
- 퍼센트 라벨: 별도 QLabel (우측)
```

### 5.7 확인 다이얼로그 (ConfirmDialog)
```
┌─────────────────────────────┐
│         Delete File          │
│                              │
│  Are you sure you want to    │
│  delete 'filename.zip'?      │
│                              │
│   [Cancel]     [Delete]      │
└─────────────────────────────┘
```

### 5.8 완료 다이얼로그 (CompletedDialog) ✅ NEW
```
┌─────────────────────────────┐
│                              │
│      완료되었습니다!          │
│                              │
│          [확인]              │
└─────────────────────────────┘

- 크기: 300×160px
- Cyan 테두리
- 확인 버튼: Cyan 배경
```

### 5.9 정지 확인 다이얼로그 (StopConfirmDialog) ✅ NEW
```
┌─────────────────────────────┐
│                              │
│  프린트를 중지하시겠습니까?   │
│                              │
│   [취소]        [중지]       │
└─────────────────────────────┘

- 크기: 320×160px
- 중지 버튼: Red 배경
```

### 5.10 파일 아이템 (FileItem)
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
| **액션** | PLAY, PAUSE, STOP_CIRCLE, EDIT | 재생 제어, 편집 |
| **도구** | WRENCH, SETTINGS, MOVE | 설정, 도구 |
| **형태** | SQUARE, SQUARE_HALF, LAYERS | 패턴, 레이어 |
| **시스템** | INFO, GLOBE, MAIL, WIFI | 시스템 메뉴 |
| **파일** | FILE, FILE_TEXT, FOLDER_OPEN | 파일 관련 |
| **Exposure** | PATTERN_RAMP, PATTERN_CHECKER, PATTERN_LOGO | 테스트 패턴 |

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
│   ├── Manual (L2) ────────────── Z축/X축 수동 제어 ✅ 업데이트
│   │   └── 위치표시 삭제, 타이틀 가운데정렬
│   │   └── X축 거리: 1, 10, 100 (단위 없음)
│   │   └── 홈 타임아웃: 100초
│   ├── Exposure (L2) ──────────── LED 노출 테스트 ✅ 업데이트
│   │   └── 아이콘 버튼 (100x100px)
│   │   └── RAMP/CHECKER/LOGO 패턴
│   │   └── Flip 기능 삭제, 시간표시 "5 sec"
│   ├── Clean (L2) ─────────────── 트레이 청소 ✅
│   │   └── 시간 설정 + START/STOP
│   ├── Set Z=0 (알림창) ────────── "아직 구현중" ✅
│   ├── Setting (L2) ─────────────── LED/Blade 설정 ✅ NEW
│   │   └── LED Power: 30-230%, ON/OFF 토글
│   │   └── Blade Speed: 10-100 mm/s, HOME/MOVE
│   │   └── 설정값 JSON 저장 (SettingsManager)
│   └── STOP (즉시 실행) ────────── 비상 정지
│
├── System (L1) ✅ 업데이트 (3×2 그리드, 6버튼)
│   ├── Device Info (L2) ────────── 장치 정보 ✅
│   │   └── 모델명: MAZIC CERA
│   │   └── 해상도: 1920 x 1080
│   │   └── 출력 영역: 124.8 x 70.2 x 80 mm
│   │   └── 픽셀: 65 μm
│   │   └── 펌웨어 ver: V 2.0.0
│   ├── Language (L2) ───────────── 언어 설정 ✅
│   │   └── 4개 버튼: 한, 中, 日, E (100x100px)
│   │   └── 눌렀을때 색상만 변경 (기능 없음)
│   ├── Service (L2) ────────────── 서비스 정보 ✅
│   │   └── Email: vericom@vericom.co.kr
│   │   └── Website: www.vericom.co.kr
│   │   └── Tel: 1661-2883
│   ├── Network (알림창) ─────────── "구현중입니다" ✅
│   ├── Theme (L2) ───────────────── 테마 설정 (계획중)
│   │   └── Light / Dark / High Contrast
│   └── Back ─────────────────────── 메인으로 이동
│
└── Print (L1) ✅
    ├── File List (L2) ──────────── 파일 목록 (3×2 그리드) ✅
    │   └── 썸네일 + 파일명, Open 버튼으로 이동
    ├── File Preview (L2) ───────── 파일 미리보기 ✅
    │   └── 썸네일, 파라미터 정보, Blade Speed/LED Power 편집
    │   └── Delete/Start 버튼, NumericKeypad 팝업
    └── Print Progress (L2) ─────── 인쇄 진행 ✅
        └── 진행률, 레이어, 시간, PAUSE/STOP 버튼
        └── 완료 시 다이얼로그 → 홈으로 이동
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
| 10 | FilePreviewPage | 파일 미리보기 |
| 11 | PrintProgressPage | 인쇄 진행 |
| 12 | SettingPage | LED/Blade 설정 ✅ NEW |
| 13 | ThemePage | 테마 설정 (계획중) |

---

## 8. 구현 현황

### 8.1 폴더 구조
```
vgui/
├── main.py                     # 진입점, 페이지 관리 ✅ 업데이트
├── assets/                     # 이미지 리소스
├── components/                 # 재사용 컴포넌트
│   ├── __init__.py            ✅ 업데이트
│   ├── header.py
│   ├── icon_button.py
│   ├── number_dial.py
│   └── numeric_keypad.py       ✅ NEW
├── pages/                      # 페이지들
│   ├── __init__.py            ✅ 업데이트
│   ├── base_page.py
│   ├── main_page.py
│   ├── tool_page.py
│   ├── manual_page.py
│   ├── print_page.py
│   ├── exposure_page.py
│   ├── clean_page.py
│   ├── system_page.py
│   ├── device_info_page.py
│   ├── language_page.py
│   ├── service_page.py
│   ├── file_preview_page.py    ✅ 업데이트
│   ├── print_progress_page.py  ✅
│   └── setting_page.py         ✅ NEW
├── styles/                     # 스타일 정의
│   ├── __init__.py
│   ├── colors.py
│   ├── fonts.py
│   ├── icons.py                ✅ EDIT, SUN 아이콘 추가
│   └── stylesheets.py
├── controllers/                # 하드웨어/설정 컨트롤러 ✅ NEW
│   ├── motor_controller.py     # Moonraker API
│   ├── dlp_controller.py       # NVR2+ I2C
│   ├── gcode_parser.py         # ZIP 파싱
│   └── settings_manager.py     # JSON 설정 저장
├── workers/                    # 백그라운드 워커 ✅ NEW
│   └── print_worker.py         # QThread 프린트 워커
└── windows/                    # 추가 윈도우 ✅ NEW
    └── projector_window.py     # 프로젝터 출력
```

### 8.2 완료된 컴포넌트 ✅

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| Header | header.py | 페이지 헤더 |
| IconButton | icon_button.py | 아이콘 버튼 |
| MainMenuButton | icon_button.py | 메인 메뉴 버튼 |
| ToolButton | icon_button.py | 도구 버튼 |
| NumberDial | number_dial.py | ±버튼 숫자 입력 |
| NumericKeypad | numeric_keypad.py | 터치 키패드 ✅ |
| ConfirmDialog | file_preview_page.py | 확인 다이얼로그 |
| CompletedDialog | print_progress_page.py | 완료 다이얼로그 ✅ NEW |
| StopConfirmDialog | print_progress_page.py | 정지 확인 다이얼로그 ✅ NEW |
| InfoRow | file_preview_page.py | 정보 표시 행 |
| ProgressInfoRow | print_progress_page.py | 진행 정보 행 ✅ NEW |
| EditableRow | file_preview_page.py | 편집 가능 행 ✅ |
| FileItem | print_page.py | 파일 아이템 |

### 8.3 완료된 페이지 ✅

| 페이지 | 파일 | 기능 |
|--------|------|------|
| MainPage | main_page.py | Tool, System, Print 버튼 |
| ToolPage | tool_page.py | 6개 버튼 그리드 |
| ManualPage | manual_page.py | Z축/X축 제어 패널 |
| PrintPage | print_page.py | 파일 목록 + 썸네일 + Open |
| ExposurePage | exposure_page.py | Ramp/Checker, Flip, 시간 |
| CleanPage | clean_page.py | 시간 설정 + START/STOP |
| SystemPage | system_page.py | 6개 버튼 (3×2 그리드) |
| DeviceInfoPage | device_info_page.py | 장치 정보 테이블 |
| LanguagePage | language_page.py | 영어/한국어 선택 |
| ServicePage | service_page.py | 연락처 정보 |
| FilePreviewPage | file_preview_page.py | 미리보기 + 설정 + Start |
| PrintProgressPage | print_progress_page.py | 진행률 + PAUSE/STOP |
| SettingPage | setting_page.py | LED Power + Blade Speed ✅ NEW |

### 8.4 PrintProgressPage 상세 ✅ NEW

**레이아웃 (Option C - 컴팩트)**
```
┌─────────────────────────────────────────────────────┐
│ [<]              Printing...                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│   ┌────────┐    filename.zip                        │
│   │ 썸네일  │                                        │
│   │(120×100)│   ████████████░░░░░░░░░░░░   45%      │
│   └────────┘                                         │
│                                                      │
│   Layer         562 / 1250                          │
│   Elapsed       25:30                               │
│   Remaining     30:15                               │
│   Blade Speed   1500 mm/min                         │
│   LED Power     100 %                               │
│                                                      │
│           [PAUSE]                [STOP]              │
└─────────────────────────────────────────────────────┘
```

**표시 정보**
| 항목 | 설명 |
|------|------|
| 썸네일 | FilePreviewPage에서 전달받은 미리보기 이미지 |
| 파일명 | 현재 프린팅 파일명 |
| Layer | 현재 레이어 / 전체 레이어 |
| Elapsed | 경과 시간 (QTimer로 1초마다 업데이트) |
| Remaining | 예상 남은 시간 (레이어 기준 계산) |
| Blade Speed | 설정된 블레이드 속도 |
| LED Power | 설정된 LED 파워 |

**버튼 상태**
| 상태 | 타이틀 | PAUSE 버튼 | STOP 버튼 |
|------|--------|------------|-----------|
| Printing | "Printing..." | "PAUSE" (Amber) | 활성화 |
| Paused | "Paused" | "RESUME" (Cyan) | 활성화 |
| Stopping | "Stopping..." | 비활성화 | 비활성화 |
| Completed | "Completed" | - | - |

**시그널**
| 시그널 | 설명 |
|--------|------|
| `pause_requested` | 일시정지 요청 → Worker |
| `resume_requested` | 재개 요청 → Worker |
| `stop_requested` | 정지 요청 → Worker |
| `go_home` | 메인 화면으로 이동 |

**Public API (Worker에서 호출)**
| 메서드 | 설명 |
|--------|------|
| `set_print_info(...)` | 프린트 시작 시 정보 설정 |
| `update_progress(current, total)` | 진행률 업데이트 |
| `show_completed()` | 완료 다이얼로그 표시 → 확인 시 홈으로 |
| `show_stopped()` | 정지됨 → 홈으로 이동 |
| `get_status()` | 현재 상태 반환 |

---

## 9. TODO 리스트

### 9.1 Phase 1: UI 페이지 (⭐⭐⭐) ✅ 완료!

| 항목 | 설명 | 상태 |
|------|------|------|
| ~~Main Page~~ | 메인 홈 화면 | ✅ 완료 |
| ~~Tool Page~~ | 도구 메뉴 | ✅ 완료 |
| ~~Manual Page~~ | Z/X축 수동 제어 | ✅ 완료 |
| ~~Print Page~~ | 파일 목록 + 썸네일 | ✅ 완료 |
| ~~File Preview~~ | 파일 미리보기 + 설정 | ✅ 완료 |
| ~~Print Progress~~ | 인쇄 진행 모니터링 | ✅ 완료 |
| ~~Exposure Page~~ | LED 노출 테스트 | ✅ 완료 |
| ~~Clean Page~~ | 트레이 청소 | ✅ 완료 |
| ~~System Pages~~ | 시스템 메뉴들 | ✅ 완료 |

### 9.2 Phase 2: 컴포넌트 (⭐⭐⭐) ✅ 대부분 완료

| 항목 | 설명 | 상태 |
|------|------|------|
| ~~NumericKeypad~~ | 터치 숫자 키패드 | ✅ 완료 |
| ~~ConfirmDialog~~ | 확인 다이얼로그 | ✅ 완료 |
| ~~CompletedDialog~~ | 완료 다이얼로그 | ✅ 완료 |
| ~~EditableRow~~ | 편집 가능 행 | ✅ 완료 |
| Toggle Switch | ON/OFF 설정용 | ❌ 필요시 |
| Slider | 범위 값 조절용 | ❌ 필요시 |

### 9.3 Phase 3: 핵심 기능 연동 (⭐⭐⭐) ✅ 완료!

| 항목 | 설명 | 상태 |
|------|------|------|
| ~~PrintWorker~~ | QThread 기반 프린트 워커 | ✅ 완료 |
| ~~Moonraker API~~ | 모터 제어 연동 | ✅ 완료 |
| ~~NVR2+ I2C~~ | LED/프로젝터 제어 | ✅ 완료 |
| ~~프로젝터 윈도우~~ | 두 번째 모니터 출력 | ✅ 완료 |
| 실시간 상태 | 위치/온도 업데이트 | ❌ |

### 9.4 Phase 4: 고급 기능 (⭐)

| 항목 | 설명 | 상태 |
|------|------|------|
| 다국어 지원 | 영어/한국어 텍스트 전환 | ❌ |
| ~~설정 저장~~ | JSON 파일로 설정 유지 | ✅ 완료 (SettingsManager) |
| **테마 기능** | Light/Dark/High Contrast | ❌ **진행중** |
| 에러 핸들링 | 오류 알림 및 복구 | ❌ |
| 부팅 자동 실행 | systemd 서비스 등록 | ❌ |

### 9.5 제외 항목 (오프라인 환경)
- ~~클라우드 서비스~~
- ~~시스템 업데이트~~
- ~~가열/예열~~ (Top-Down 방식에서 불필요)

---

## 10. 코드 컨벤션

### 10.1 명명 규칙
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

### 10.2 시그널 명명
```python
go_back = Signal()           # 페이지 이동
go_home = Signal()
file_selected = Signal(str)  # 데이터 전달
value_changed = Signal(float)
value_confirmed = Signal(float)  # 값 확정
start_print = Signal(str, dict)  # 파일경로, 파라미터
file_deleted = Signal(str)       # 삭제된 파일경로
pause_requested = Signal()       # 제어 요청
resume_requested = Signal()
stop_requested = Signal()
```

### 10.3 새 페이지 추가 체크리스트
```
□ BasePage 상속
□ __init__에서 super().__init__(title, show_back=True)
□ _setup_content() 메서드 구현
□ go_back 시그널 자동 포함 (BasePage)
□ pages/__init__.py에 import 추가
□ main.py에 페이지 인덱스, 생성, 시그널 연결 추가
□ 라즈베리파이에서 테스트 (transparent 배경 주의)
```

### 10.4 QLabel 스타일 체크리스트 ⚠️
```
□ QFrame 내부 QLabel에 반드시 border: none 명시
□ background-color: transparent 대신 명시적 색상 또는 border: none 함께 사용
□ 테두리 상속 문제 방지
```

### 10.5 Header 메서드 참고
```python
# Header 타이틀 변경
self.header.set_title("New Title")  # ✅ 올바른 방법
self.header.title_label.setText()   # ⚠️ 직접 접근 (비권장)
```

---

## 📜 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2024-12 | 초기 버전 |
| 2.0 | 2024-12 | UniFormation 분석 반영, 컴포넌트 추가 |
| 3.0 | 2024-12-02 | Tool/System 페이지 완료, 10개 페이지 구현 |
| 4.0 | 2024-12-04 | Print 플로우 완료 (PrintPage 개선, FilePreviewPage 추가) |
| 5.0 | 2024-12-08 | NumericKeypad 추가, FilePreviewPage 개선 (EditableRow, 값 우측정렬) |
| 6.0 | 2024-12-08 | PrintProgressPage 추가, 완료/정지 다이얼로그, 전체 UI 완성 |
| 7.0 | 2024-12-23 | 해상도 1024x600 변경, Exposure 아이콘버튼+LOGO패턴, Language 4버튼, Manual 위치삭제/X거리변경, Service/DeviceInfo 정보 업데이트, 홈 타임아웃 100초 |
| 7.1 | 2025-12-23 | **Setting 페이지 추가** (LED Power/Blade Speed), **SettingsManager** (JSON 저장), System 페이지 6버튼 그리드, Theme 버튼 추가, controllers/workers/windows 폴더 구조 추가, PrintWorker/Moonraker/NVR2+ 연동 완료 |

---

## 📊 진행률 요약

| 카테고리 | 완료 | 전체 | 진행률 |
|----------|------|------|--------|
| **UI 페이지** | 13 | 14 | **93%** ✅ |
| 컴포넌트 | 13 | 15 | 87% |
| 하드웨어 연동 | 4 | 5 | **80%** ✅ |
| 고급 기능 | 1 | 5 | 20% |

🎉 **핵심 기능 연동 완료!** (PrintWorker, Moonraker API, NVR2+ I2C)

**다음 우선순위:** Theme 페이지 구현 (Light/Dark/High Contrast)

---

> **Note:** 이 가이드는 프로젝트 진행에 따라 업데이트됩니다.
