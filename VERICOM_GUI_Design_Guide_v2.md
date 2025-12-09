# VERICOM DLP 3D Printer GUI 디자인 가이드

> **Version:** 2.0  
> **Last Updated:** 2024-12  
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
8. [상태 스타일](#8-상태-스타일)
9. [TODO 리스트](#9-todo-리스트)
10. [코드 컨벤션](#10-코드-컨벤션)
11. [레이아웃 변경 검토](#11-레이아웃-변경-검토)

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

| 이름 | HEX | RGB | 용도 |
|------|-----|-----|------|
| **Navy** | `#1E3A5F` | 30, 58, 95 | 주요 버튼, 텍스트, 아이콘 |
| **Navy Light** | `#2D4A6F` | 45, 74, 111 | Navy hover 상태 |
| **Cyan** | `#06B6D4` | 6, 182, 212 | 액센트, 강조, 활성 상태 |
| **Cyan Light** | `#22D3EE` | 34, 211, 238 | Cyan hover 상태 |

### 2.2 Semantic Colors (의미적 색상)

| 이름 | HEX | RGB | 용도 |
|------|-----|-----|------|
| **Red** | `#DC2626` | 220, 38, 38 | 정지, 삭제, 경고 |
| **Red Light** | `#FEE2E2` | 254, 226, 226 | Red 배경 |
| **Teal** | `#14B8A6` | 20, 184, 166 | 성공, 시작, 완료 |
| **Teal Light** | `#CCFBF1` | 204, 251, 241 | Teal 배경 |
| **Amber** | `#F59E0B` | 245, 158, 11 | 주의, 일시정지 |

### 2.3 Neutral Colors (중립 색상)

| 이름 | HEX | RGB | 용도 |
|------|-----|-----|------|
| **White** | `#FFFFFF` | 255, 255, 255 | 주 배경 |
| **Gray 50** | `#F8FAFC` | 248, 250, 252 | 보조 배경, 카드 배경 |
| **Gray 100** | `#F1F5F9` | 241, 245, 249 | 비활성 배경 |
| **Gray 200** | `#E2E8F0` | 226, 232, 240 | 테두리, 구분선 |
| **Gray 400** | `#94A3B8` | 148, 163, 184 | 비활성 텍스트, 힌트 |
| **Gray 500** | `#64748B` | 100, 116, 139 | 보조 텍스트 |
| **Gray 700** | `#334155` | 51, 65, 85 | 주요 텍스트 |
| **Gray 900** | `#0F172A` | 15, 23, 42 | 강조 텍스트 |

### 2.4 PySide6 색상 정의 예시
```python
class Colors:
    # Primary
    NAVY = "#1E3A5F"
    NAVY_LIGHT = "#2D4A6F"
    CYAN = "#06B6D4"
    CYAN_LIGHT = "#22D3EE"
    
    # Semantic
    RED = "#DC2626"
    RED_LIGHT = "#FEE2E2"
    TEAL = "#14B8A6"
    TEAL_LIGHT = "#CCFBF1"
    AMBER = "#F59E0B"
    
    # Neutral
    WHITE = "#FFFFFF"
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F8FAFC"
    BG_TERTIARY = "#F1F5F9"
    BORDER = "#E2E8F0"
    TEXT_DISABLED = "#94A3B8"
    TEXT_SECONDARY = "#64748B"
    TEXT_PRIMARY = "#334155"
    TEXT_EMPHASIS = "#0F172A"
```

---

## 3. 타이포그래피

### 3.1 폰트 패밀리
```
Primary: "Pretendard", "Noto Sans KR", sans-serif
Monospace: "SF Mono", "Consolas", monospace (숫자, 코드용)
```

### 3.2 폰트 크기 체계

| 이름 | 크기 | 굵기 | 용도 |
|------|------|------|------|
| **Display** | 42px | Bold (700) | 다이얼 숫자 |
| **H1** | 24px | Bold (700) | 큰 숫자, 메인 값 |
| **H2** | 20px | SemiBold (600) | 메인 버튼 레이블 |
| **H3** | 18px | SemiBold (600) | 페이지 타이틀, 섹션 제목 |
| **Body** | 16px | Medium (500) | 일반 버튼, 본문 |
| **Body Small** | 14px | Medium (500) | 보조 정보, 작은 버튼 |
| **Caption** | 12px | Regular (400) | 힌트, 레이블, 파일명 |
| **Tiny** | 11px | Medium (500) | 아이콘 하단 레이블 |

---

## 4. 레이아웃 규칙

### 4.1 화면 구조
```
┌─────────────────────────────────────────────────────┐
│                    Header (56px)                     │
│  [Back]           Title                    [Action]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│                                                      │
│                  Content Area                        │
│                   (404px)                            │
│                                                      │
│                                                      │
├─────────────────────────────────────────────────────┤
│              Footer/Navigation (20px padding)        │
└─────────────────────────────────────────────────────┘

전체: 800 × 480px
Header: 56px 높이
Content: 나머지 영역 (padding 20px)
```

### 4.2 간격 시스템 (Spacing)

| 토큰 | 크기 | 용도 |
|------|------|------|
| `xs` | 4px | 아이콘-텍스트 간격 |
| `sm` | 8px | 밀접한 요소 간격 |
| `md` | 12px | 일반 요소 간격 |
| `lg` | 16px | 섹션 내 간격, 기본 패딩 |
| `xl` | 20px | 콘텐츠 영역 패딩 |
| `2xl` | 24px | 큰 섹션 간격 |
| `3xl` | 32px | 메인 버튼 간격 |

### 4.3 터치 영역 규칙
```
최소 터치 영역: 48 × 48px
권장 버튼 크기: 60 × 60px 이상
메인 버튼 크기: 200 × 200px
일반 버튼 높이: 50px
```

---

## 5. 컴포넌트 가이드

### 5.1 버튼 (Button)

#### Primary Button (주요 액션)
```css
background: #1E3A5F (Navy)
border: none
border-radius: 12px
color: #FFFFFF
font-size: 16px
font-weight: 600
padding: 14px 24px
min-height: 50px
```

#### Secondary Button (보조 액션)
```css
background: #FFFFFF
border: 2px solid #E2E8F0
border-radius: 12px
color: #334155
font-size: 16px
font-weight: 600
padding: 14px 24px
min-height: 50px
```

#### Icon Button (아이콘 버튼)
```css
background: #F8FAFC
border: 2px solid #E2E8F0
border-radius: 14px
width: 60-70px
height: 60-70px
/* 아이콘 중앙 정렬 */
```

#### Danger Button (위험 액션)
```css
background: #F8FAFC
border: 2px solid #DC2626
border-radius: 12px
color: #DC2626
```

#### Main Menu Button (메인 메뉴)
```css
background: #F8FAFC
border: 2px solid #E2E8F0
border-radius: 20px
width: 200px
height: 200px
/* 아이콘 64px, 텍스트 20px */
```

### 5.2 카드 (Card)

#### 기본 카드
```css
background: #F8FAFC
border: 2px solid #E2E8F0
border-radius: 16px
padding: 20px
```

#### 선택 가능 카드
```css
/* 기본 상태 */
background: #F8FAFC
border: 2px solid #E2E8F0

/* 선택 상태 */
background: rgba(30, 58, 95, 0.05)
border: 2px solid #1E3A5F
```

### 5.3 Toggle Switch (NEW)
```css
/* Container */
width: 52px
height: 28px
border-radius: 14px
background: #E2E8F0 (OFF) / #06B6D4 (ON)

/* Handle */
width: 24px
height: 24px
border-radius: 12px
background: #FFFFFF
/* 위치: left 2px (OFF) / right 2px (ON) */
```

### 5.4 Slider (NEW)
```css
/* Track */
height: 6px
background: #E2E8F0
border-radius: 3px

/* Fill */
background: #06B6D4
border-radius: 3px

/* Handle */
width: 20px
height: 20px
border-radius: 50%
background: #06B6D4
border: 3px solid #FFFFFF
```

### 5.5 Setting Item (NEW)
```css
/* Container */
background: #F8FAFC / rgba(30, 58, 95, 0.05)
border-radius: 12px
padding: 16px 20px
height: 70-80px

/* Layout */
┌──────────────────────────────────────────┐
│ [Icon]  Title                   [Control]│
│         Subtitle/Value                   │
└──────────────────────────────────────────┘

/* Icon */
size: 32-40px
color: #06B6D4

/* Title */
font-size: 16px
color: #334155

/* Subtitle */
font-size: 14px
color: #64748B

/* Control */
Toggle Switch / Slider / Icon
```

### 5.6 Confirm Dialog (NEW)
```css
/* Overlay */
background: rgba(0, 0, 0, 0.5)

/* Dialog */
background: #FFFFFF
border-radius: 16px
padding: 30px
min-width: 320px

/* Message */
font-size: 18px
font-weight: 600
color: #334155
text-align: center
margin-bottom: 24px

/* Buttons */
┌───────────────────────────────────────┐
│                                       │
│        인쇄를 중지하시겠습니까?          │
│                                       │
│   ┌─────────┐      ┌─────────┐       │
│   │   ✗    │      │   ✓    │        │
│   └─────────┘      └─────────┘       │
└───────────────────────────────────────┘

/* Cancel Button */
background: #FFFFFF
border: 2px solid #E2E8F0
icon: X (Red)

/* Confirm Button */
background: #1E3A5F
border: none
icon: Check (White)
```

### 5.7 프로그레스 바 (Progress Bar)

#### Linear (기존)
```css
/* Container */
background: #E2E8F0
border-radius: 10px
height: 36px

/* Fill */
background: linear-gradient(90deg, #1E3A5F, #06B6D4)
border-radius: 10px
```

#### Circular (NEW - 선택적)
```css
/* Container */
width: 120px
height: 120px
stroke-width: 8px

/* Background Circle */
stroke: #E2E8F0

/* Progress Circle */
stroke: #06B6D4
/* 또는 gradient */

/* Center Text */
font-size: 24px
font-weight: 700
color: #334155
```

### 5.8 숫자 입력 다이얼 (Number Dial)
```css
/* Value Display */
background: #F8FAFC
border: 2px solid #06B6D4
border-radius: 16px
width: 160px
height: 80px
/* 숫자: 42px Bold Navy */

/* +/- Buttons */
border: 2px solid #1E3A5F
border-radius: 14px
width: 60px
height: 60px
```

### 5.9 File List Item (NEW)
```css
/* Container */
background: #F8FAFC / transparent
border-radius: 8px
padding: 12px 16px
height: 60px

/* Layout */
┌────────────────────────────────────────────────┐
│ [📁]  파일명.ctb                        [ctb] │
└────────────────────────────────────────────────┘

/* Icon */
Folder: 폴더 아이콘
File: 파일 아이콘
color: #64748B

/* Filename */
font-size: 16px
color: #334155

/* Type Badge */
background: #06B6D4
border-radius: 6px
padding: 4px 12px
color: #FFFFFF
font-size: 14px
```

---

## 6. 아이콘 가이드

### 6.1 아이콘 스타일
```
스타일: Outlined (선형)
선 두께: 1.5px (작은 아이콘) ~ 2px (큰 아이콘)
끝 처리: Round (stroke-linecap: round)
연결 처리: Round (stroke-linejoin: round)
```

### 6.2 아이콘 크기

| 용도 | 크기 |
|------|------|
| 메인 메뉴 버튼 | 64px |
| 도구 버튼 | 40px |
| 일반 버튼 내 | 24px |
| 헤더/네비게이션 | 20px |
| 작은 아이콘 | 16px |

### 6.3 아이콘 색상 규칙
```
기본: Navy (#1E3A5F)
강조/활성: Cyan (#06B6D4)
위험/정지: Red (#DC2626)
비활성화: Gray 400 (#94A3B8)
반전(어두운 배경): White (#FFFFFF)
```

### 6.4 주요 아이콘 목록

| 기능 | 아이콘 설명 | Lucide 이름 |
|------|-------------|-------------|
| Tool | 렌치 | `Wrench` |
| System | 톱니바퀴 | `Settings` |
| Print | 레이어 스택 | `Layers` |
| Manual | 4방향 화살표 | `Move` |
| Exposure | 사각형 안 사각형 | `Square` (커스텀) |
| Clean | 절반 사각형 | `SquareHalf` (커스텀) |
| Stop | 원 안 사각형 | `StopCircle` |
| Back | 왼쪽 화살표 | `ArrowLeft` |
| Home | 집 | `Home` |
| Up | 위 화살표 | `ChevronUp` |
| Down | 아래 화살표 | `ChevronDown` |
| Play | 재생 | `Play` |
| Pause | 일시정지 | `Pause` |
| File | 문서 | `FileText` |
| Folder | 폴더 | `Folder` |
| Delete | 휴지통 | `Trash2` |
| Time | 시계 | `Clock` |
| Confirm | 체크 | `Check` |
| Cancel | X | `X` |
| Plus | + | `Plus` |
| Minus | - | `Minus` |
| Info | 정보 | `Info` |
| USB | USB | `Usb` |
| Reset | 새로고침 | `RefreshCw` |
| Edit | 연필 | `Pencil` |
| Volume | 스피커 | `Volume2` |
| Light | 전구 | `Lightbulb` |
| Temperature | 온도계 | `Thermometer` |

---

## 7. 페이지 구조

### 7.1 전체 페이지 맵

```
Main (L0)
│
├── Tool (L1)
│   ├── Manual (L2) ─────────────────── Z/X축 수동 제어
│   │   ├── Z Axis Control
│   │   └── X Axis Control (Blade)
│   │
│   ├── Exposure Test (L2) ──────────── LED 노출 테스트
│   │   └── Pattern Selection + Time Setting
│   │
│   ├── Tray Clean (L2) ─────────────── 트레이 청소
│   │   └── Pattern Selection + Time Setting
│   │
│   ├── Set Z=0 (L2) ────────────────── Z축 영점 설정
│   │
│   └── STOP (즉시 실행) ─────────────── 비상 정지
│
├── System (L1)
│   ├── Device Info (L2) ────────────── 장치 정보
│   │   └── 해상도, 인쇄 크기, ID 등
│   │
│   └── Settings (L2) ───────────────── 환경 설정
│       ├── LED 파워 설정
│       ├── 블레이드 속도
│       ├── 평탄화 횟수
│       └── Z축 속도
│
└── Print (L1)
    ├── File List (L2) ──────────────── 파일 목록
    │   └── USB 스캔 + 폴더 탐색
    │
    ├── File Preview (L2) ───────────── 파일 미리보기
    │   └── 썸네일 + 정보 + 시작/삭제
    │
    └── Print Progress (L2) ─────────── 인쇄 진행
        ├── 미리보기 + 프로그레스
        ├── 정보 패널
        ├── Pause/Resume
        ├── Stop → [Confirm Dialog]
        └── Settings (L3) ───────────── 인쇄 중 설정
            ├── 노출 설정 탭
            ├── 층수/높이 탭
            └── 기타 탭

[공용 컴포넌트]
├── Confirm Dialog ──────────────────── 확인 다이얼로그
├── Number Dial ─────────────────────── 숫자 입력
└── Toast/Alert ─────────────────────── 알림 메시지
```

### 7.2 페이지별 상세

#### Main Page
| 요소 | 설명 |
|------|------|
| 헤더 | 타이틀만 (Back 없음) |
| 콘텐츠 | 3개 메인 버튼 (Tool, System, Print) |
| 버튼 크기 | 200×200px |
| 정렬 | 중앙 |

#### Tool Page
| 요소 | 설명 |
|------|------|
| 헤더 | "Tool" + Back |
| 콘텐츠 | 3×2 그리드 |
| 버튼 | Manual, Exposure, Clean, STOP, Set Z=0, Back |
| STOP | 빨간색 강조 |

#### Manual Page
| 요소 | 설명 |
|------|------|
| 헤더 | "Manual Control" + Back |
| 콘텐츠 | Z축/X축 2개 패널 |
| 각 패널 | 현재값, 거리선택(0.1/1/10mm), 방향버튼, STOP |

#### File Preview Page (NEW)
| 요소 | 설명 |
|------|------|
| 헤더 | 파일명 + Back |
| 좌측 | 3D 썸네일 미리보기 |
| 우측 | 파일 정보 (해상도, 레이어 수, 예상 시간) |
| 하단 | 삭제 버튼, 시작 버튼 |

#### Print Progress Page (NEW)
| 요소 | 설명 |
|------|------|
| 헤더 | 없음 (풀스크린) |
| 좌측 | 레이어 미리보기 |
| 중앙 | 프로그레스 (원형 또는 선형) |
| 우측 | 정보 패널 (노출시간, 높이, 레이어 등) |
| 하단 | Pause, Stop, Settings 버튼 |

#### Exposure Test Page (NEW)
| 요소 | 설명 |
|------|------|
| 헤더 | "Exposure Test" + Back |
| 콘텐츠 | 패턴 선택 (전체, 사각형, 원형 등) |
| 하단 | 시간 슬라이더 (10s~40s) + 시작 버튼 |

#### Tray Clean Page (NEW)
| 요소 | 설명 |
|------|------|
| 헤더 | "Tray Clean" + Back |
| 콘텐츠 | 패턴 선택 + 시간 설정 |
| 하단 | 시간 슬라이더 + 시작 버튼 |

#### Device Info Page (NEW)
| 요소 | 설명 |
|------|------|
| 헤더 | "Device Info" + Back |
| 콘텐츠 | 정보 리스트 |
| 항목 | 인쇄 크기, 해상도, 장치 ID, SW 버전 |

#### Settings Page (NEW)
| 요소 | 설명 |
|------|------|
| 헤더 | "Settings" + Back |
| 콘텐츠 | 설정 항목 리스트 |
| 컨트롤 | Toggle, Slider |
| 항목 | LED 파워, 블레이드 속도, 평탄화 횟수 등 |

### 7.3 새 페이지 추가 시 체크리스트
```
□ Header 포함 (56px)
□ Back 버튼 기능 연결
□ 타이틀 설정
□ Content 영역 padding 20px
□ 컬러 시스템 준수
□ 폰트 크기 체계 준수
□ 최소 터치 영역 48px 확보
□ 상태별 스타일 적용 (hover, pressed, disabled)
□ go_back 시그널 연결
□ 라즈베리파이에서 테스트 (transparent 주의)
```

---

## 8. 상태 스타일

### 8.1 버튼 상태

#### Normal (기본)
```css
background: #F8FAFC
border: 2px solid #E2E8F0
```

#### Pressed (눌림)
```css
background: #E2E8F0
border-color: #1E3A5F
```

#### Active/Selected (활성/선택)
```css
background: rgba(6, 182, 212, 0.1)
border-color: #06B6D4
color: #06B6D4
```

#### Disabled (비활성)
```css
background: #F1F5F9
border-color: #E2E8F0
color: #94A3B8
```

### 8.2 라즈베리파이 주의사항 ⚠️
```
❌ 피해야 할 것:
- background-color: transparent
- rgba 투명도 (일부 케이스)

✅ 권장:
- 명시적 배경색 지정 (#FFFFFF, #F8FAFC 등)
- 부모-자식 배경색 일치
```

---

## 9. TODO 리스트

### 9.1 구현 완료 ✅

#### 스타일 시스템
- [x] 컬러 팔레트 정의 (Navy + Cyan)
- [x] 버튼 스타일 결정 (플랫, 그림자 없음)
- [x] 아이콘 스타일 결정 (선형, outlined)
- [x] 기본 레이아웃 구조 설계
- [x] HTML 목업 제작

#### PySide6 구현
- [x] 프로젝트 구조 설계 (vgui/)
- [x] styles/ 패키지 (colors, fonts, icons, stylesheets)
- [x] components/ 패키지
  - [x] Header
  - [x] IconButton, ControlButton, HomeButton
  - [x] MainMenuButton, ToolButton
  - [x] NumberDial, DistanceSelector
- [x] pages/ 패키지
  - [x] BasePage
  - [x] MainPage
  - [x] ToolPage
  - [x] ManualPage (Z/X축)
  - [x] PrintPage (파일 선택)
- [x] main.py (메인 윈도우, 네비게이션)
- [x] 라즈베리파이 투명 배경 이슈 수정

---

### 9.2 구현 예정 📋

#### Phase 1: 핵심 컴포넌트 (우선순위 높음)
| 항목 | 설명 | 상태 |
|------|------|------|
| Confirm Dialog | 정지/삭제 확인 팝업 | ❌ |
| Toggle Switch | ON/OFF 설정용 | ❌ |
| Slider | 범위 값 조절용 | ❌ |
| Setting Item | 설정 행 컴포넌트 | ❌ |

#### Phase 2: 핵심 페이지
| 페이지 | 설명 | 우선순위 |
|--------|------|----------|
| File Preview | 파일 미리보기 + 시작 | ⭐⭐⭐ |
| Print Progress | 인쇄 진행 모니터링 | ⭐⭐⭐ |
| Exposure Test | LED 노출 테스트 | ⭐⭐ |
| Tray Clean | 트레이 청소 | ⭐⭐ |

#### Phase 3: 부가 페이지
| 페이지 | 설명 | 우선순위 |
|--------|------|----------|
| Device Info | 장치 정보 표시 | ⭐ |
| Settings | 환경 설정 | ⭐ |
| Print Settings | 인쇄 중 설정 (탭 UI) | ⭐ |

#### Phase 4: 하드웨어 연동
| 항목 | 설명 | 상태 |
|------|------|------|
| Moonraker API | 모터 제어 연동 | ❌ |
| NVR2+ I2C | LED/프로젝터 제어 | ❌ |
| USB 자동 감지 | 파일 스캔 | ⭐ 기본 구현됨 |
| 실시간 상태 | 위치/온도 업데이트 | ❌ |

#### Phase 5: 고급 기능
| 항목 | 설명 | 상태 |
|------|------|------|
| 레이어 미리보기 | 인쇄 중 현재 레이어 표시 | ❌ |
| 에러 핸들링 | 오류 알림 및 복구 | ❌ |
| 설정 저장 | JSON 파일로 설정 유지 | ❌ |
| 부팅 자동 실행 | systemd 서비스 등록 | ❌ |

---

### 9.3 제외 항목 (오프라인 환경)
- ~~네트워크 설정~~
- ~~클라우드 서비스~~
- ~~시스템 업데이트~~
- ~~가열/예열~~ (Top-Down 방식에서 불필요)

---

### 9.4 이슈 및 고려사항 ⚠️

| 이슈 | 상태 | 해결 방법 |
|------|------|-----------|
| 투명 배경 검은색 | ✅ 해결 | 명시적 배경색 지정 |
| Pretendard 폰트 | ⚠️ 확인 필요 | Noto Sans KR 폴백 |
| 터치 반응성 | ⚠️ 테스트 필요 | 최소 48px 준수 |
| 성능 최적화 | ⚠️ 모니터링 | QTimer 사용, 불필요 업데이트 제거 |

---

## 10. 코드 컨벤션

### 10.1 파일 구조
```
vgui/
├── main.py                 # 진입점
├── README.md               # 프로젝트 설명
├── styles/
│   ├── __init__.py
│   ├── colors.py           # 컬러 상수
│   ├── fonts.py            # 폰트 설정
│   ├── icons.py            # SVG 아이콘
│   └── stylesheets.py      # QSS 스타일시트
├── components/
│   ├── __init__.py
│   ├── header.py
│   ├── icon_button.py
│   ├── number_dial.py
│   ├── toggle_switch.py    # NEW
│   ├── slider.py           # NEW
│   ├── confirm_dialog.py   # NEW
│   └── setting_item.py     # NEW
├── pages/
│   ├── __init__.py
│   ├── base_page.py
│   ├── main_page.py
│   ├── tool_page.py
│   ├── manual_page.py
│   ├── print_page.py
│   ├── file_preview_page.py    # NEW
│   ├── print_progress_page.py  # NEW
│   ├── exposure_page.py        # NEW
│   ├── clean_page.py           # NEW
│   ├── device_info_page.py     # NEW
│   └── settings_page.py        # NEW
├── controllers/
│   ├── motor_controller.py
│   ├── led_controller.py
│   └── file_controller.py
└── assets/
    └── icons/
```

### 10.2 명명 규칙
```python
# 클래스: PascalCase
class MainPage(QWidget):
    pass

# 함수/메서드: snake_case
def go_to_page(self, page_name):
    pass

# 상수: UPPER_SNAKE_CASE
NAVY = "#1E3A5F"
BUTTON_HEIGHT = 50

# 위젯 변수: btn_, lbl_, etc.
self.btn_start = QPushButton()
self.lbl_title = QLabel()
```

### 10.3 시그널 명명
```python
# 동작_대상 형태
go_back = Signal()
go_home = Signal()
file_selected = Signal(str)
value_changed = Signal(float)
```

---

## 11. 레이아웃 변경 검토

### 11.1 UniFormation vs VERICOM 비교

| 항목 | UniFormation | VERICOM (현재) | 권장 |
|------|-------------|----------------|------|
| 테마 | 다크 (네이비/블랙) | 라이트 (화이트) | ✅ 유지 |
| 네비게이션 | 하단 탭바 고정 | 헤더 + Back | 🔶 검토 |
| 파일 목록 | 리스트 뷰 | 그리드 뷰 | 🔶 검토 |
| 프로그레스 | 원형 (%) | 직선 바 | 🔶 검토 |
| STOP 버튼 | 원형, 별도 위치 | 그리드 내 | 🔶 검토 |
| Z축 제어 | 거리별 버튼 8개 | 거리 선택 + 방향 | ✅ 유지 |

### 11.2 변경 검토 옵션

#### 옵션 A: 하단 탭바 도입
```
장점: 어느 페이지에서든 빠른 이동
단점: 화면 공간 ~60px 감소
결정: ❓ 추후 검토
```

#### 옵션 B: 파일 리스트 뷰 변경
```
장점: 긴 파일명 표시, 폴더 구조 탐색 용이
단점: 한 화면 파일 수 감소
결정: 🔶 고려 가능
```

#### 옵션 C: 원형 프로그레스
```
장점: 시각적 임팩트, 공간 효율
단점: 구현 복잡도 증가
결정: ⭐ 선택적 구현
```

### 11.3 유지할 것
- ✅ 라이트 테마 (흰 배경 + Navy/Cyan)
- ✅ 현재 Manual 페이지의 축별 패널 구조
- ✅ 플랫 디자인 + 선형 아이콘
- ✅ Header + Back 버튼 네비게이션

---

## 📎 참고 자료

- [Lucide Icons](https://lucide.dev/) - 아이콘 라이브러리
- [Tailwind CSS Colors](https://tailwindcss.com/docs/colors) - 컬러 참고
- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [Pretendard Font](https://cactus.tistory.com/306) - 한글 폰트

---

## 📜 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2024-12 | 초기 버전 |
| 2.0 | 2024-12 | UniFormation 분석 반영, 새 컴포넌트 추가, TODO 업데이트 |

---

> **Note:** 이 가이드는 프로젝트 진행에 따라 업데이트됩니다.  
> 변경 사항이 있을 경우 Version과 변경 이력을 갱신해주세요.
