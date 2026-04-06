# MAZIC CERA GUI - 페이지별 기능 정리 (2025-04-06)

## 페이지 네비게이션 구조

```
Main Page (MAZIC CERA)
├── TOOL
│   ├── Manual       (Z/X/Y축 수동 제어)
│   ├── Exposure     (LED 노출 테스트 + 트레이 클리닝)
│   ├── Leveling     (3단계 레벨링 가이드)
│   ├── Setting      (LED/Blade/Y축 빠른 설정)
│   └── Material     (소재 프리셋 관리)
├── PRINT
│   → 파일 선택 → 소재 선택(팝업) → 파일 미리보기 → 프린트 진행
└── SYSTEM
    ├── Device Info   (장치 사양)
    ├── Language      (언어 선택)
    ├── Service       (연락처)
    └── Theme         (Light/Dark 테마)
```

---

## 1. Main Page (홈)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/main_page.py` |
| 인덱스 | PAGE_MAIN = 0 |

### UI 구성
- 타이틀: "MAZIC CERA" (중앙, Navy 색상)
- 3개 메뉴 버튼 (200x200px): TOOL, SYSTEM, PRINT
- VERICOM 로고 (우하단, 클릭 시 관리자 모드 트리거)

### 기능
- TOOL 버튼 → Tool 페이지 이동
- SYSTEM 버튼 → System 페이지 이동
- PRINT 버튼 → Print(파일 선택) 페이지 이동
- 로고 5회 클릭 (3초 내) → 관리자 모드 활성화

---

## 2. Tool Page (도구 메뉴)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/tool_page.py` |
| 인덱스 | PAGE_TOOL = 1 |

### UI 구성
- 5개 도구 버튼 (수평 배열):
  1. **Manual** - 수동 축 제어
  2. **Exposure** - 노출 패턴 테스트
  3. **Leveling** - 레벨링 가이드
  4. **Setting** - LED/Blade/Y축 설정
  5. **Material** - 소재 프리셋 관리

### 기능
- 각 버튼 클릭 시 해당 페이지로 이동
- 뒤로가기 → Main Page

---

## 3. Manual Page (수동 제어)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/manual_page.py` |
| 인덱스 | PAGE_MANUAL = 2 |

### UI 구성
3개 축 패널 수평 배열:

| 패널 | 축 | 거리 선택 | 버튼 |
|------|-----|-----------|------|
| Z Axis | Z축 (빌드 플레이트) | 0.1 / 1.0 / 10.0 mm | HOME, UP, DOWN |
| X Axis (Blade) | X축 (블레이드) | 1 / 10 / 100 mm | HOME, LEFT, RIGHT |
| Resin Feeder | Y축 (레진 토출) | 0.1 / 1.0 / 10.0 mm | HOME, UP, DOWN |

### 기능
- 각 축 독립적 이동 (거리 선택 → 방향 버튼)
- HOME 버튼: 해당 축 원점 복귀
- 모터 작업 중 버튼 비활성화 (UI 잠금)

---

## 4. Print Page (파일 선택)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/print_page.py` |
| 인덱스 | PAGE_PRINT = 3 |

### UI 구성
- 파일 그리드: 3x2 (페이지당 6개 파일)
- 각 파일: 썸네일(100x100px) + 파일명
- 네비게이션 버튼: UP/DOWN (페이지), OPEN, HOME
- 선택된 파일: Cyan 테두리

### 기능
- USB 자동 감지 (2초 주기 폴링, /media 디렉토리)
- 지원 형식: .zip (기본), .dlp, .photon, .ctb
- 파일 선택 → OPEN → ZIP 검증 → 소재 선택 팝업 → 미리보기

### ZIP 검증 항목
1. `run.gcode` 파일 존재 여부
2. 머신 설정 일치 (해상도, 출력영역)
3. `preview.png`, `preview_cropping.png` 존재
4. 레이어 이미지 연속성 (1.png, 2.png, ... N.png)

---

## 5. File Preview Page (파일 미리보기)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/file_preview_page.py` |
| 인덱스 | PAGE_FILE_PREVIEW = 9 |

### UI 구성

**좌측:**
- 썸네일 프레임 (280x220px)
- 파일명

**우측:**
- 소재 선택 배지 (Cyan, 클릭 시 소재 변경 가능)
- 파일 정보 (읽기 전용):
  - Total Layers
  - Estimated Print Time
  - Layer Height
  - Bottom Layer Exposure Time
  - Normal Exposure Time
- 소재 프리셋 값 (읽기 전용):
  - Blade Speed (mm/s)
  - LED Power (%)
  - Blade Cycles (회)
  - Y Dispense Distance (mm)
  - Y Dispense Speed (mm/s)
  - Y Dispense Delay (s)
- 버튼: Delete (빨간색), Start (Cyan)

### 기능
- 소재 선택: MaterialSelectDialog 팝업으로 변경
- Start: 선택된 소재 프리셋 값으로 프린트 시작
- Delete: 확인 다이얼로그 후 파일 삭제

---

## 6. Print Progress Page (프린트 진행)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/print_progress_page.py` |
| 인덱스 | PAGE_PRINT_PROGRESS = 10 |

### UI 구성

**상단:**
- 레이어 미리보기 (270x270px)
- 9개 정보 행: Bottom/Normal 노출시간, 레이어 높이, 현재/총 레이어, 바닥 레이어 수, 블레이드 속도, LED 파워, 경과 시간, 총 예상 시간

**하단:**
- 파일명
- 프로그레스 바 (Cyan 그라데이션)
- 퍼센트 표시
- 상태별 버튼:

| 상태 | 버튼 |
|------|------|
| 프린팅 중 | PAUSE (Amber) + STOP (빨간) |
| 일시정지 | RESUME (Cyan) + STOP |
| 완료/에러 | GUI HOME (Cyan) + Z AXIS HOME |

### 기능
- 실시간 레이어 이미지 업데이트
- 경과 시간 1초 단위 업데이트
- PAUSE: 노출 완료 후 일시정지 (Klipper에 PAUSE 알림)
- RESUME: 재개 (Klipper shutdown 시 자동 firmware restart)
- STOP: 확인 다이얼로그 후 정지
- 완료 시: CompletedDialog 팝업
- 에러 시: ErrorDialog 팝업

---

## 7. Exposure Page (노출 테스트)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/exposure_page.py` |
| 인덱스 | PAGE_EXPOSURE = 4 |

### UI 구성
- 5개 패턴 버튼 (100x100px):
  1. **Gradient** - 밝기 램프 (최대 60초)
  2. **Checker** - 체커보드 (최대 60초)
  3. **Logo** - 로고 패턴 (최대 60초)
  4. **20x20** - 20x20mm 정사각형 (최대 60초)
  5. **Clean** - 전체화면 클리닝 (최대 120초)
- 시간 설정 버튼 (클릭 → NumberDial)
- START / STOP 버튼

### 기능
- 패턴 선택 → 시간 설정 → START
- 프로젝터 2차 모니터에 패턴 표시 + LED ON
- 설정 시간 경과 후 자동 STOP
- 수동 STOP 가능

---

## 8. Leveling Page (레벨링)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/leveling_page.py` |
| 인덱스 | PAGE_LEVELING = 13 |

### 3단계 레벨링 시퀀스

| Step | 동작 | 설명 |
|------|------|------|
| 0 | Z축 홈 | 스테이지 설치, 잠금 안 함, 버튼 누르기 |
| 1 | X축 홈 | 블레이드 설치, 잠금 나사 풀기, 버튼 누르기 |
| 2 | X축 75mm 이동 | 블레이드 중앙 이동, 버튼 누르기 |
| 완료 | Done | 블레이드 잠금, 스테이지 잠금 |

### 기능
- 각 단계 버튼 클릭 시 모터 동작
- 모터 완료 후 다음 단계 활성화
- Done 클릭 시 Tool 페이지로 복귀

---

## 9. Setting Page (설정)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/setting_page.py` |
| 인덱스 | PAGE_SETTING = 11 |

### UI 구성 (3패널 수평 배열)

| 패널 | 항목 | 범위 | 기능 |
|------|------|------|------|
| LED SET | LED Power | 9-100% | 값 클릭 → 키패드, ON/OFF 토글 |
| BLADE SET | Blade Speed | 1-15 mm/s | 값 클릭 → 키패드, HOME/MOVE 버튼 |
| Y Axis | 거리 선택 | 0.1/1.0/10.0mm | HOME, UP, DOWN 버튼 |

### 기능
- LED ON: 프로젝터에 테스트 이미지 표시 + LED 켜기
- LED OFF: LED 끄기 + 프로젝터 닫기
- BLADE MOVE: 0mm ↔ 140mm 토글 이동
- Y축: 수동 이동 (Setting 페이지 전용)
- 값 변경 시 자동 저장 (SettingsManager)

---

## 10. Material Page (소재 관리)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/material_page.py` |
| 인덱스 | PAGE_MATERIAL = 14 |

### UI 구성

**좌측 패널 (240px):**
- 타이틀: "Presets"
- 스크롤 가능한 프리셋 버튼 리스트
- Add 버튼 (Cyan)
- Delete 버튼 (빨간 테두리)

**우측 패널:**
- 소재 이름 (클릭 시 이름 변경)
- 9개 파라미터 편집 행:

| 파라미터 | 범위 | 단위 |
|----------|------|------|
| Blade Speed | 1-15 | mm/s |
| LED Power | 9-100 | % |
| Blade Cycles | 1-3 | 회 |
| Y Dispense | 0.1-5.0 | mm |
| Y Speed | 1-15 | mm/s |
| Y Delay | 0.5-10.0 | s |
| Leveling Cycles | 0-5 | 회 |
| Lift Height | 1.0-20.0 | mm |
| Drop Speed | 10-300 | mm/min |

### 기능
- 프리셋 추가: MaterialNameDialog로 이름 입력
- 프리셋 삭제: 최소 1개 유지
- 프리셋 선택: 좌측 리스트에서 클릭
- 값 편집: 각 행 클릭 → NumericKeypad 팝업
- 이름 변경: 우측 상단 이름 클릭 → MaterialNameDialog
- 자동 저장: 값 변경 즉시 settings.json에 반영

### 기본 소재
1. **Zirconia** - 지르코니아 (기본 선택)
2. **Alumina** - 알루미나
3. **Hydroxyapatite** - 하이드록시아파타이트

---

## 11. System Page (시스템)

| 항목 | 내용 |
|------|------|
| 파일 | `pages/system_page.py` |
| 인덱스 | PAGE_SYSTEM = 5 |

### UI 구성
- 6개 버튼 (3x2 그리드):
  1. Device Info → 장치 정보
  2. Language → 언어 선택
  3. Service → 서비스 연락처
  4. Network → (미구현, "구현중" 알림)
  5. Theme → 테마 선택
  6. Back → 메인으로

---

## 12. Device Info Page

| 항목 | 내용 |
|------|------|
| 파일 | `pages/device_info_page.py` |
| 인덱스 | PAGE_DEVICE_INFO = 6 |

### 표시 정보
| 항목 | 값 |
|------|-----|
| 모델명 | MAZIC CERA |
| 해상도 | 1920 x 1080 |
| 출력 영역 | 124.8 x 70.2 x 80 mm |
| 픽셀 | 65 μm |
| 펌웨어 ver | V 2.0.0 |

---

## 13. Language Page

| 항목 | 내용 |
|------|------|
| 파일 | `pages/language_page.py` |
| 인덱스 | PAGE_LANGUAGE = 7 |

### UI 구성
- 4개 언어 버튼: 한국어, 中文, 日本語, English
- 선택 시 Cyan 배경으로 하이라이트
- (실제 다국어 전환은 미구현)

---

## 14. Service Page

| 항목 | 내용 |
|------|------|
| 파일 | `pages/service_page.py` |
| 인덱스 | PAGE_SERVICE = 8 |

### 표시 정보
| 항목 | 값 |
|------|-----|
| Email | vericom@vericom.co.kr |
| Website | www.vericom.co.kr |
| Tel | 1661-2883 |

---

## 15. Theme Page

| 항목 | 내용 |
|------|------|
| 파일 | `pages/theme_page.py` |
| 인덱스 | PAGE_THEME = 12 |

### 기능
- Light / Dark 2개 테마 선택
- 선택 즉시 적용 (모든 페이지 재생성)
- 설정 재시작 후에도 유지

---

## 공통 기능

### 키오스크 모드
- Alt+F4, Alt+Tab, Esc, F1-F11, Windows 키 차단
- 관리자 모드: 로고 5회 클릭 (3초 내) 또는 Ctrl+Shift+F12
- 관리자 모드 5분 후 자동 해제
- 관리자 모드 시 커서 표시, 일반 모드 시 커서 숨김

### 테마 시스템
- Colors 메타클래스 기반 동적 색상 변경
- 테마 전환 시 모든 페이지 재생성 (`_rebuild_pages()`)
- Light: 밝은 배경, Navy/Cyan 포인트
- Dark: 어두운 배경, 밝은 Navy/Cyan 포인트

### 설정 영속성
- `data/settings.json`에 저장
- 저장 항목: LED 파워, 블레이드 속도, 소재 프리셋, 선택 소재, 테마, 언어
- 앱 시작 시 자동 로드
