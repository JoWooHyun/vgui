# VERICOM DLP 3D Printer GUI

VERICOM DLP 3D 프린터를 위한 터치스크린 GUI 애플리케이션입니다.

> **Note**: 현재 GUI 프로토타입 단계입니다. UI만 구현되어 있으며, 실제 하드웨어 제어 기능은 추후 추가 예정입니다.

## 개요

- **프레임워크**: PySide6 (Qt for Python)
- **해상도**: 800 x 480 (라즈베리파이 터치스크린)
- **디자인 테마**: Navy + Cyan

## 프로젝트 구조

```
vgui/
├── main.py                 # 메인 진입점
├── components/             # 재사용 컴포넌트
│   ├── header.py           # 상단 헤더
│   ├── icon_button.py      # 아이콘 버튼
│   ├── number_dial.py      # 숫자 다이얼
│   └── numeric_keypad.py   # 숫자 키패드
├── pages/                  # 페이지 화면
│   ├── main_page.py        # 메인 홈
│   ├── tool_page.py        # 도구 메뉴
│   ├── manual_page.py      # 수동 제어
│   ├── print_page.py       # 파일 선택
│   ├── file_preview_page.py    # 파일 미리보기
│   ├── print_progress_page.py  # 프린트 진행
│   ├── exposure_page.py    # 노출 테스트
│   ├── clean_page.py       # 클리닝
│   ├── system_page.py      # 시스템 설정
│   ├── device_info_page.py # 장치 정보
│   ├── language_page.py    # 언어 설정
│   └── service_page.py     # 서비스 정보
├── styles/                 # 스타일 정의
│   ├── colors.py           # 컬러 팔레트
│   ├── fonts.py            # 폰트 설정
│   ├── icons.py            # 아이콘 (SVG)
│   └── stylesheets.py      # Qt 스타일시트
└── assets/                 # 이미지, 리소스
```

## 설치

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/vgui.git
cd vgui

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

## 페이지 구성

| 페이지 | 설명 |
|--------|------|
| Main | 메인 홈 (Tool, System, Print 메뉴) |
| Tool | 도구 메뉴 (Manual, Exposure, Clean) |
| Manual | Z축/X축 수동 제어 |
| Print | USB 파일 목록 |
| File Preview | 선택 파일 미리보기 및 파라미터 설정 |
| Print Progress | 프린트 진행 상태 |
| Exposure | LED 노출 테스트 |
| Clean | 레진 클리닝 |
| System | 시스템 설정 메뉴 |
| Device Info | 장치 정보 확인 |
| Language | 언어 설정 |
| Service | 서비스/고객지원 정보 |

## TODO

- [ ] Moonraker API 연동 (모터 제어)
- [ ] NVR2+ LED 제어 연동
- [ ] 실제 프린트 워커 구현
- [ ] USB 파일 탐색 기능
- [ ] 다국어 지원

## 라이선스

Private
