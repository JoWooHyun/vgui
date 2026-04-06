# MAZIC CERA GUI

MAZIC CERA DLP 3D 프린터를 위한 터치스크린 GUI 애플리케이션입니다.

## 현재 상태

**Z축 리프트 복원** (2026-04-06)

- LED 노광 후 Z축 +5mm 리프트 추가 (블레이드 복귀 공간 확보)
- 불필요한 "다음 레이어 높이 이동" 제거 (다음 레이어 시작 시 자동 이동)

**소재 프리셋 시스템** (2026-04-06)

- Material 페이지 추가: 소재별 프린트 파라미터 프리셋 관리
- 프린트 플로우 변경: 파일 선택 → 소재 선택(팝업) → 미리보기(읽기전용)
- 기본 소재: Zirconia, Alumina, Hydroxyapatite

**Y축 자동 레진 토출** (2026-02)

- 레이어당 자동 레진 공급 (시린지 펌프, Y축 모터)
- 80mm 한계 도달 시 레진 부족 알림 + 사용자 선택
- Y축 50cc 보정 (홈 후 6mm 오프셋)

**프린트 시퀀스 고도화** (2026-01~02)

- 블레이드 Oneway 모드 (140→0)
- Klipper 장시간 일시정지 → 자동 firmware restart 복구
- Leveling 페이지 3단계 가이드 시퀀스
- Exposure + Clean 통합 (5패턴)

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

## 프린터 특징

- **Top-Down 방식** DLP 프린터
- **Z축**: 빌드 플레이트 상하 이동
- **X축**: 블레이드 수평 이동 (레진 평탄화)
- **Y축**: 시린지 펌프 자동 레진 토출
- **LED 노출**: NVR2+ 모듈을 통한 UV LED 제어

## 프로젝트 구조

```
vgui/
├── main.py                     # 메인 진입점, 윈도우 관리
├── components/                 # 재사용 UI 컴포넌트
│   ├── header.py               # 페이지 헤더
│   ├── icon_button.py          # 아이콘 버튼
│   ├── number_dial.py          # ±버튼 숫자 다이얼
│   └── numeric_keypad.py       # 터치 숫자 키패드
├── controllers/                # 하드웨어 컨트롤러
│   ├── motor_controller.py     # Moonraker 모터 제어
│   ├── dlp_controller.py       # NVR2+ DLP/LED 제어
│   ├── gcode_parser.py         # ZIP/G-code 파싱
│   ├── settings_manager.py     # 설정 저장/로드
│   └── theme_manager.py        # 테마 관리
├── workers/                    # 백그라운드 워커
│   └── print_worker.py         # 프린팅 시퀀스 실행 (QThread)
├── windows/                    # 추가 윈도우
│   └── projector_window.py     # 프로젝터 출력 윈도우
├── pages/                      # GUI 페이지 (15개)
│   ├── main_page.py            # 메인 홈
│   ├── tool_page.py            # 도구 메뉴
│   ├── manual_page.py          # Z/X/Y축 수동 제어
│   ├── print_page.py           # 파일 목록
│   ├── file_preview_page.py    # 파일 미리보기 + 소재 선택
│   ├── print_progress_page.py  # 프린트 진행 상황
│   ├── exposure_page.py        # LED 노출 테스트 (Clean 통합)
│   ├── leveling_page.py        # 3단계 레벨링 가이드
│   ├── system_page.py          # 시스템 설정
│   ├── setting_page.py         # LED/블레이드/Y축 설정
│   ├── material_page.py        # 소재 프리셋 관리
│   ├── theme_page.py           # 테마 선택
│   ├── device_info_page.py     # 장치 정보
│   ├── language_page.py        # 언어 설정
│   └── service_page.py         # 서비스 정보
├── styles/                     # 스타일 정의
│   ├── colors.py               # 컬러 팔레트 (동적 테마)
│   ├── fonts.py                # 폰트 설정
│   ├── icons.py                # SVG 아이콘
│   └── stylesheets.py          # Qt 스타일시트
└── utils/                      # 유틸리티
    ├── usb_monitor.py          # USB 모니터링
    ├── zip_handler.py          # ZIP 파일 처리
    └── time_formatter.py       # 시간 포맷팅
```

## 설치

### Raspberry Pi (실제 환경)

```bash
# 저장소 클론
git clone https://github.com/JoWooHyun/vgui.git
cd vgui

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### Windows (개발 환경)

```bash
git clone https://github.com/JoWooHyun/vgui.git
cd vgui
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 실행

### 실제 하드웨어 모드

```bash
python main.py
```

### 시뮬레이션 모드 (하드웨어 없이 테스트)

```bash
python main.py --sim
```

### 실행 옵션

| 옵션 | 설명 |
|------|------|
| `--kiosk` | 키오스크 모드 (전체화면, 커서 숨김) |
| `--windowed` | 윈도우 모드 (개발용) |
| `--sim` | 시뮬레이션 모드 |
| `--no-sim` | 실제 하드웨어 모드 |

## 프린팅 워크플로우

1. **파일 선택**: USB에서 ZIP 파일 선택 + 자동 검증
2. **소재 선택**: MaterialSelectDialog 팝업에서 소재 프리셋 선택
3. **미리보기**: 썸네일, 레이어 수, 노출 시간, 소재 설정값 확인 (읽기전용)
4. **프린트 시작**: 자동 시퀀스 실행
   - Z축/X축/Y축 홈 이동
   - Y축 50cc 보정 (6mm 오프셋)
   - 레진 평탄화 (블레이드 레벨링)
   - 레이어별: Z이동 → Y토출 → 블레이드 스윕(140→0) → LED 노출 → Z리프트(+5mm) → 블레이드 복귀(0→140)
5. **완료 또는 에러**: LED OFF, 이미지 클리어, GUI홈/Z축홈 선택

## 에러 처리

### 이미지 로드 실패
- 3회 재시도 후 실패 시 프린트 자동 중지
- 에러 다이얼로그로 사용자 알림

### 모터 에러
- Z축/X축 이동 실패 시 프린트 자동 중지
- 안전을 위해 Z축은 현재 위치 유지

### 정지/에러 시 동작
1. LED OFF
2. 프로젝터 OFF
3. X축만 홈 복귀 (Z축 위치 유지)
4. 에러 다이얼로그 표시 (에러 시)
5. 메인 페이지로 이동

## ZIP 파일 형식

프린트 파일은 다음 구조의 ZIP 파일이어야 합니다:

```
print_file.zip
├── run.gcode             # 프린트 파라미터 (필수)
├── preview.png           # 썸네일 이미지 (필수)
├── preview_cropping.png  # 크롭된 썸네일 (필수)
├── 1.png                 # 레이어 1
├── 2.png                 # 레이어 2
├── ...
└── N.png                 # 레이어 N (연속된 숫자)
```

### ZIP 파일 검증 조건

| 조건 | 설명 | 실패 시 메시지 |
|------|------|----------------|
| run.gcode 존재 | 필수 파일 | "run.gcode 파일이 없습니다" |
| 머신 설정 일치 | 아래 5개 값 필수 | "지원하지 않는 프린터 파일입니다" |
| preview.png 존재 | 필수 파일 | "미리보기 이미지가 없습니다" |
| preview_cropping.png 존재 | 필수 파일 | "미리보기 이미지가 없습니다" |
| 레이어 이미지 연속 | 1.png, 2.png... 중간 빠짐 없이 | "레이어 이미지가 손상되었습니다" |

### 필수 머신 설정 (run.gcode 내)

```gcode
;resolutionX:1920
;resolutionY:1080
;machineX:124.8
;machineY:70.2
;machineZ:80
```

### run.gcode 파라미터 예시

```gcode
;totalLayer:100
;layerHeight:0.05
;normalExposureTime:3.0
;bottomLayerExposureTime:30.0
;bottomLayerCount:8
;normalLayerLiftHeight:5.0
;normalLayerLiftSpeed:65
;estimatedPrintTime:3600
;resolutionX:1920
;resolutionY:1080
;machineX:124.8
;machineY:70.2
;machineZ:80
```

## 문서

| 문서 | 내용 |
|------|------|
| [TODO.md](TODO.md) | 미해결 이슈 및 향후 작업 |
| [CODE_REVIEW.md](CODE_REVIEW.md) | 코드 리뷰 및 아키텍처 분석 |
| [FEATURE_SPEC.md](FEATURE_SPEC.md) | 페이지별 기능 정리 |
| [WIREFRAME.md](WIREFRAME.md) | 페이지별 와이어프레임 (ASCII) |
| [DEVELOPMENT_DIARY.md](DEVELOPMENT_DIARY.md) | 개발 다이어리 |

## 개발 가이드

### 블레이드 속도 단위

- **UI 표시**: mm/s (1-15)
- **내부 저장**: mm/s × 60 = Gcode F-value (mm/min)
- **예시**: 5 mm/s → F300

### 테마 시스템

- `ThemeManager` 싱글톤으로 테마 관리
- `Colors` 메타클래스로 동적 색상 변경
- `get_*_style()` 함수로 동적 스타일 적용
- `main.py`에서 다른 모듈 임포트 전 ThemeManager 초기화 (저장된 테마 적용)
- 테마 변경 시 `_rebuild_pages()`로 모든 페이지 새로 생성

### 새 개발자를 위한 테마 가이드

**중요**: 새로운 다이얼로그나 컴포넌트 추가 시:

1. 배경색은 `Colors.WHITE` 대신 `Colors.BG_PRIMARY` 사용
2. 정적 스타일시트 상수 대신 `get_*_style()` 동적 함수 사용
3. 인라인 스타일이 많은 경우 `_update_*_style()` 헬퍼 메서드 작성

```python
# 올바른 예:
self.setStyleSheet(f"""
    QDialog {{
        background-color: {Colors.BG_PRIMARY};  # 테마에 따라 변경됨
        ...
    }}
""")

# 잘못된 예:
self.setStyleSheet(f"""
    QDialog {{
        background-color: {Colors.WHITE};  # 항상 흰색 고정
        ...
    }}
""")

## 라이선스

Private - VERICOM
