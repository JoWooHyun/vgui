Update Todos

Phase 0: 프로젝트 초기 설정

0-1. 프로젝트 폴더 구조 생성 (main.py, components/, pages/, styles/, assets/)

0-2. styles/colors.py - 컬러 상수 정의 (Navy, Cyan, Red, Amber 등)

0-3. styles/fonts.py - 폰트 크기/굵기 상수 정의

0-4. styles/icons.py - SVG 아이콘 문자열 정의 (ARROW_LEFT, HOME, PLAY 등)

0-5. styles/stylesheets.py - 버튼/위젯 스타일시트 정의

0-6. main.py - 키오스크 전체화면 앱 진입점 (1024x600, FramelessWindowHint)

Phase 1: 공통 컴포넌트 구현

1-1. components/header.py - 페이지 헤더 (Back 버튼, 타이틀, Action 버튼)

1-2. components/icon_button.py - 아이콘 버튼 (SVG 렌더링, hover/pressed 상태)

1-3. components/main_menu_button.py - 메인 메뉴 대형 버튼 (200x200px)

1-4. components/tool_button.py - 도구 메뉴 버튼 (그리드용)

1-5. components/numeric_keypad.py - 숫자 키패드 다이얼로그 (350x420px)

1-6. components/number_dial.py - ±버튼 숫자 조절 다이얼

1-7. components/info_row.py - 정보 표시 행 (라벨: 값)

1-8. components/editable_row.py - 편집 가능 행 (클릭 시 키패드)

1-9. components/file_item.py - 파일 아이템 (썸네일 + 파일명)

1-10. components/confirm_dialog.py - 확인 다이얼로그 (삭제/정지 확인)

1-11. components/completed_dialog.py - 완료 다이얼로그

1-12. components/__init__.py - 컴포넌트 모듈 export

Phase 2: 기본 페이지 구현 (pages/base_page.py)

2-1. pages/base_page.py - BasePage 클래스 (Header 포함, go_back 시그널)

Phase 3: 메인/네비게이션 페이지

3-1. pages/main_page.py - 홈 화면 (Tool, System, Print 버튼 3개)

3-2. pages/tool_page.py - 도구 메뉴 (Manual, Exposure, Clean, Set Z=0, STOP)

3-3. pages/system_page.py - 시스템 메뉴 (Device Info, Language, Service, Network)

Phase 4: Tool 하위 페이지

4-1. pages/manual_page.py - Z축/X축 수동 제어 (스텝 선택, UP/DOWN/HOME)

4-2. pages/exposure_page.py - 노출 테스트 (Ramp/Checker, Flip, 시간설정)

4-3. pages/clean_page.py - 트레이 청소 (시간설정, START/STOP, 타이머)

Phase 5: System 하위 페이지

5-1. pages/device_info_page.py - 장치 정보 (Print Size, Resolution, FW Version 등)

5-2. pages/language_page.py - 언어 설정 (English/한국어 선택)

5-3. pages/service_page.py - 서비스 정보 (Email, Website, Tel)

Phase 6: Print 플로우 페이지

6-1. pages/print_page.py - 파일 목록 (USB 감지, 4x2 그리드, 썸네일, 페이지네이션)

6-2. pages/file_preview_page.py - 파일 미리보기 (파라미터 표시, Blade/LED/Leveling 편집)

6-3. pages/print_progress_page.py - 인쇄 진행 (진행률, 레이어, 시간, PAUSE/STOP)

Phase 7: 페이지 네비게이션 연결

7-1. main.py에 QStackedWidget으로 모든 페이지 등록

7-2. 각 페이지 시그널-슬롯 연결 (go_back, go_home, 페이지 전환)

7-3. Print 플로우 연결 (PrintPage → FilePreviewPage → PrintProgressPage)

7-4. pages/__init__.py - 페이지 모듈 export

Phase 8: 하드웨어 제어 모듈

8-1. controllers/motor_controller.py - Z축/X축 모터 제어 (Moonraker API)

8-2. controllers/dlp_controller.py - NVR2+ LED/프로젝터 제어 (I2C)

8-3. controllers/gcode_parser.py - run.gcode 파라미터 파싱

8-4. controllers/__init__.py - 컨트롤러 모듈 export

Phase 9: 프린트 워커 (핵심)

9-1. workers/print_worker.py - QThread 기반 프린팅 워커

9-2. 프린팅 시퀀스 구현 (Z홈→X홈→평탄화→레이어루프)

9-3. 진행률 시그널 연결 (progress_updated → PrintProgressPage)

9-4. 일시정지/정지 기능 구현 (is_paused, is_stopped 플래그)

9-5. workers/__init__.py - 워커 모듈 export

Phase 10: 프로젝터 윈도우

10-1. windows/projector_window.py - 두 번째 모니터 전체화면 윈도우

10-2. 이미지 투영 기능 (show_image, clear_screen)

10-3. windows/__init__.py - 윈도우 모듈 export

Phase 11: 유틸리티

11-1. utils/usb_monitor.py - USB 장치 감지 (폴링/이벤트)

11-2. utils/zip_handler.py - ZIP 파일 처리 (썸네일 추출, 이미지 로드)

11-3. utils/time_formatter.py - 시간 포맷 (MM:SS, 예상시간 계산)

11-4. utils/__init__.py - 유틸리티 모듈 export

Phase 12: 테스트 및 통합

12-1. UI 전체 네비게이션 테스트

12-2. 모터 제어 테스트 (Manual 페이지)

12-3. LED/프로젝터 테스트 (Exposure, Clean 페이지)

12-4. 전체 프린팅 플로우 테스트

12-5. 라즈베리파이 실기기 테스트 (투명배경 이슈 등)

Phase 13: 마무리

13-1. Design Guide 업데이트 (1024x600 반영)

13-2. 부팅 자동 실행 설정 (systemd 서비스)

13-3. README.md 업데이트
상세한 TODO 리스트를 작성했습니다. 아래에 정리해서 보여드릴게요:
📋 VERICOM DLP 3D Printer GUI - 상세 TODO 리스트
Phase 0: 프로젝트 초기 설정
#	항목	설명
0-1	폴더 구조 생성	main.py, components/, pages/, styles/, assets/, controllers/, workers/, windows/, utils/
0-2	styles/colors.py	컬러 상수 (Navy, Cyan, Red, Amber, Gray 등)
0-3	styles/fonts.py	폰트 크기/굵기 상수 (H1, H2, Body 등)
0-4	styles/icons.py	SVG 아이콘 문자열 (ARROW_LEFT, HOME, PLAY 등)
0-5	styles/stylesheets.py	버튼/위젯 스타일시트 (Primary, Secondary, Danger 등)
0-6	main.py	키오스크 전체화면 앱 진입점 (1024×600, FramelessWindowHint, BlankCursor)
Phase 1: 공통 컴포넌트 구현
#	항목	설명
1-1	header.py	페이지 헤더 (Back 버튼, 타이틀, Action 버튼)
1-2	icon_button.py	아이콘 버튼 (SVG 렌더링, hover/pressed 상태)
1-3	main_menu_button.py	메인 메뉴 대형 버튼 (200×200px)
1-4	tool_button.py	도구 메뉴 버튼 (그리드용)
1-5	numeric_keypad.py	숫자 키패드 다이얼로그 (350×420px)
1-6	number_dial.py	±버튼 숫자 조절 다이얼
1-7	info_row.py	정보 표시 행 (라벨: 값)
1-8	editable_row.py	편집 가능 행 (클릭 시 키패드 팝업)
1-9	file_item.py	파일 아이템 (썸네일 + 파일명)
1-10	confirm_dialog.py	확인 다이얼로그 (삭제/정지 확인)
1-11	completed_dialog.py	완료 다이얼로그
1-12	__init__.py	컴포넌트 모듈 export
Phase 2: 기본 페이지 클래스
#	항목	설명
2-1	base_page.py	BasePage 클래스 (Header 포함, go_back 시그널)
Phase 3: 메인/네비게이션 페이지
#	항목	설명
3-1	main_page.py	홈 화면 (Tool, System, Print 버튼 3개)
3-2	tool_page.py	도구 메뉴 (Manual, Exposure, Clean, Set Z=0, STOP)
3-3	system_page.py	시스템 메뉴 (Device Info, Language, Service, Network)
Phase 4: Tool 하위 페이지
#	항목	설명
4-1	manual_page.py	Z축/X축 수동 제어 (스텝 선택, UP/DOWN/HOME, 현재위치)
4-2	exposure_page.py	노출 테스트 (Ramp/Checker 패턴, Flip, 시간설정)
4-3	clean_page.py	트레이 청소 (시간설정, START/STOP, 타이머)
Phase 5: System 하위 페이지
#	항목	설명
5-1	device_info_page.py	장치 정보 (Print Size, Resolution, FW Version 등)
5-2	language_page.py	언어 설정 (English / 한국어 선택)
5-3	service_page.py	서비스 정보 (Email, Website, Tel)
Phase 6: Print 플로우 페이지
#	항목	설명
6-1	print_page.py	파일 목록 (USB 감지, 4×2 그리드, 썸네일, 페이지네이션)
6-2	file_preview_page.py	파일 미리보기 (파라미터 표시, Blade/LED/Leveling 편집, Delete/Start)
6-3	print_progress_page.py	인쇄 진행 (진행률, 레이어, 시간, PAUSE/STOP)
Phase 7: 페이지 네비게이션 연결
#	항목	설명
7-1	QStackedWidget 등록	main.py에 모든 페이지 등록 (인덱스 관리)
7-2	시그널-슬롯 연결	go_back, go_home, 페이지 전환 시그널 연결
7-3	Print 플로우 연결	PrintPage → FilePreviewPage → PrintProgressPage
7-4	pages/__init__.py	페이지 모듈 export
Phase 8: 하드웨어 제어 모듈
#	항목	설명
8-1	motor_controller.py	Z축/X축 모터 제어 (Moonraker API, G-code)
8-2	dlp_controller.py	NVR2+ LED/프로젝터 제어 (CyUSBSerial, I2C)
8-3	gcode_parser.py	run.gcode 파라미터 파싱
8-4	__init__.py	컨트롤러 모듈 export
Phase 9: 프린트 워커 (핵심) ⭐
#	항목	설명
9-1	print_worker.py	QThread 기반 프린팅 워커
9-2	프린팅 시퀀스	Z홈 → X홈 → 평탄화 → 레이어루프 (Z위치→X이동→투영→노광→리프트→복귀)
9-3	진행률 시그널	progress_updated(current, total) → PrintProgressPage
9-4	일시정지/정지	is_paused, is_stopped 플래그 처리
9-5	__init__.py	워커 모듈 export
Phase 10: 프로젝터 윈도우
#	항목	설명
10-1	projector_window.py	두 번째 모니터 전체화면 윈도우 (screen_index=1)
10-2	이미지 투영 기능	show_image(pixmap), clear_screen()
10-3	__init__.py	윈도우 모듈 export
Phase 11: 유틸리티
#	항목	설명
11-1	usb_monitor.py	USB 장치 감지 (/media 폴링 또는 이벤트)
11-2	zip_handler.py	ZIP 파일 처리 (썸네일 추출, 이미지 로드)
11-3	time_formatter.py	시간 포맷 (MM:SS, 예상시간 계산)
11-4	__init__.py	유틸리티 모듈 export
Phase 12: 테스트 및 통합
#	항목	설명
12-1	UI 네비게이션 테스트	모든 페이지 전환 확인
12-2	모터 제어 테스트	Manual 페이지에서 Z/X축 동작 확인
12-3	LED/프로젝터 테스트	Exposure, Clean 페이지 동작 확인
12-4	전체 프린팅 테스트	파일 선택 → 프린팅 → 완료 플로우
12-5	라즈베리파이 테스트	실기기 테스트 (투명배경 이슈 등)
Phase 13: 마무리
#	항목	설명
13-1	Design Guide 업데이트	1024×600 해상도 반영
13-2	부팅 자동 실행	systemd 서비스 등록
13-3	README.md 업데이트	설치/실행 가이드
📁 최종 폴더 구조
vgui/
├── main.py                    # 앱 진입점 (키오스크)
├── assets/                    # 이미지 리소스
├── components/                # 재사용 컴포넌트
│   ├── __init__.py
│   ├── header.py
│   ├── icon_button.py
│   ├── main_menu_button.py
│   ├── tool_button.py
│   ├── numeric_keypad.py
│   ├── number_dial.py
│   ├── info_row.py
│   ├── editable_row.py
│   ├── file_item.py
│   ├── confirm_dialog.py
│   └── completed_dialog.py
├── pages/                     # 페이지들
│   ├── __init__.py
│   ├── base_page.py
│   ├── main_page.py
│   ├── tool_page.py
│   ├── system_page.py
│   ├── manual_page.py
│   ├── exposure_page.py
│   ├── clean_page.py
│   ├── device_info_page.py
│   ├── language_page.py
│   ├── service_page.py
│   ├── print_page.py
│   ├── file_preview_page.py
│   └── print_progress_page.py
├── controllers/               # 하드웨어 제어
│   ├── __init__.py
│   ├── motor_controller.py
│   ├── dlp_controller.py
│   └── gcode_parser.py
├── workers/                   # 백그라운드 워커
│   ├── __init__.py
│   └── print_worker.py
├── windows/                   # 추가 윈도우
│   ├── __init__.py
│   └── projector_window.py
├── utils/                     # 유틸리티
│   ├── __init__.py
│   ├── usb_monitor.py
│   ├── zip_handler.py
│   └── time_formatter.py
└── styles/                    # 스타일 정의
    ├── __init__.py
    ├── colors.py
    ├── fonts.py
    ├── icons.py
    └── stylesheets.py