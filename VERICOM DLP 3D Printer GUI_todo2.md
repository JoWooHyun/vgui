# VERICOM DLP 3D 프린터 GUI - 페이지별 요구사항 분석

> **분석 기반:** gui5.py, dlp_simple_slideshow.py, VERICOM_GUI_Design_Guide_v6.md  
> **분석일:** 2025-12-16  
> **목적:** 기존 코드에서 유추한 기능 요구사항을 Design Guide v6 기준으로 정리

---

## 🖥️ 하드웨어 환경 (수정됨)

| 항목 | 스펙 |
|------|------|
| 디스플레이 | 7인치 HDMI Touch LCD |
| **해상도** | **1024 × 600 px** |
| 입력방식 | 터치 전용 (마우스/키보드 없음) |
| **화면 모드** | **키오스크/전체화면 (작업표시줄 없음)** |
| 보드 | CM4 + Manta M8P 2.0 통합보드 |
| 프로젝터 | Young Optics NVR2+ |

### 전체화면 구현 요구사항
```python
# PySide6 전체화면 설정
self.setWindowFlags(Qt.FramelessWindowHint)  # 타이틀바 제거
self.showFullScreen()                         # 전체화면
self.setFixedSize(1024, 600)                 # 고정 해상도
```

### 레이아웃 재계산 (1024×600 기준)
```
┌─────────────────────────────────────────────────────────────┐
│                      Header (56px)                           │
│  [Back]              Title                         [Action]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    Content Area                              │
│                     (524px)                                  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                Footer/Navigation (20px padding)              │
└─────────────────────────────────────────────────────────────┘

전체: 1024 × 600px
Header: 56px 높이
Content: 524px (600 - 56 - 20)
좌우 패딩: 20px
```

---

## 📊 전체 구조 요약

```
┌─ MainPage (0) ─────────────────────────────────────────┐
│  메인 홈 화면                                           │
│  ├─ Tool 버튼 → ToolPage                               │
│  ├─ System 버튼 → SystemPage                           │
│  └─ Print 버튼 → PrintPage                             │
└────────────────────────────────────────────────────────┘

┌─ ToolPage (1) ──────────────────────────────────────────┐
│  도구 메뉴 (6버튼 그리드)                                │
│  ├─ Manual → ManualPage (Z/X축 수동제어)                 │
│  ├─ Exposure → ExposurePage (LED 테스트)                │
│  ├─ Clean → CleanPage (트레이 청소)                     │
│  ├─ (미사용) Calibration, Settings                     │
│  └─ Back → MainPage                                    │
└────────────────────────────────────────────────────────┘

┌─ SystemPage (6) ─────────────────────────────────────────┐
│  시스템 메뉴 (4버튼)                                     │
│  ├─ Device Info → DeviceInfoPage                        │
│  ├─ Language → LanguagePage                            │
│  ├─ Service → ServicePage                              │
│  └─ Network → 알림창 "구현중"                           │
└─────────────────────────────────────────────────────────┘

┌─ Print Flow ────────────────────────────────────────────┐
│  PrintPage (3) → FilePreviewPage (10) → PrintProgressPage (11)
└─────────────────────────────────────────────────────────┘
```

---

## 🏠 PAGE 0: MainPage (메인 홈)

### 현재 구현 (gui5.py HomeMenu 참조)
| 항목 | gui5.py 구현 | Design Guide v6 |
|------|-------------|-----------------|
| 버튼 | Print, System, Tools | Tool, System, Print (3개) |
| 버튼 크기 | 200×80px | 200×200px (MainMenuButton) |
| 레이아웃 | 가로 배치 | 가로 배치 (중앙 정렬) |
| 타이틀 | "DLP 3D 프린터" | - |

### TODO - 기능 요구사항
- [ ] **Layout**: 3개 MainMenuButton 가로 배치 (200×200px)
- [ ] **Buttons**: 
  - Tool 버튼 → ToolPage 이동
  - System 버튼 → SystemPage 이동  
  - Print 버튼 → PrintPage 이동
- [ ] **Style**: Navy 배경 + 흰 텍스트 + 아이콘

### 하드웨어 연동
- [ ] 없음 (네비게이션 전용)

---

## 🔧 PAGE 1: ToolPage (도구 메뉴)

### 현재 구현 (gui5.py ToolsMenu 참조)
| 항목 | gui5.py 구현 | Design Guide v6 |
|------|-------------|-----------------|
| 버튼 | Move Z, Calibration, Settings, Back | Manual, Exposure, Clean + 3개 여유 |
| 레이아웃 | 2×2 그리드 | 2×3 그리드 (6버튼) |
| 버튼 크기 | 180×60px | ToolButton 스타일 |

### TODO - 기능 요구사항
- [ ] **Layout**: 2×3 그리드 (6개 ToolButton)
- [ ] **Buttons**:
  - Manual → ManualPage (Z/X축 수동제어)
  - Exposure → ExposurePage (LED 테스트)
  - Clean → CleanPage (트레이 청소)
  - (예비 3개 슬롯)
- [ ] **Header**: "Tools" + Back 버튼

### 하드웨어 연동
- [ ] 없음 (네비게이션 전용)

---

## 🎮 PAGE 2: ManualPage (수동 제어)

### 현재 구현 (gui5.py MoveZMenu 참조)
| 항목 | gui5.py 구현 | Design Guide v6 |
|------|-------------|-----------------|
| 기능 | Z축만 제어 | Z축 + X축(블레이드) 제어 |
| 스텝 선택 | 0.1mm, 1mm, 10mm | 동일 |
| 버튼 | UP, DOWN, HOME, Back | Z/X 각각 UP/DOWN/HOME |

### TODO - 기능 요구사항

#### Z축 제어 패널
- [ ] **스텝 선택**: 0.1mm / 1mm / 10mm 버튼 (토글)
- [ ] **방향 버튼**: 
  - ↑ UP: G91 → G1 Z+{step} F300 → G90
  - ↓ DOWN: G91 → G1 Z-{step} F300 → G90
- [ ] **HOME 버튼**: G28 Z
- [ ] **현재 위치 표시**: Z: 0.000 mm (실시간)

#### X축(블레이드) 제어 패널
- [ ] **스텝 선택**: 1mm / 10mm / 50mm 버튼
- [ ] **방향 버튼**:
  - ← LEFT: G91 → G0 X-{step} F{blade_speed} → G90
  - → RIGHT: G91 → G0 X+{step} F{blade_speed} → G90
- [ ] **HOME 버튼**: G28 X
- [ ] **END 버튼**: G0 X125 F{blade_speed} (끝점 이동)
- [ ] **현재 위치 표시**: X: 0.0 mm

### 하드웨어 연동
- [ ] **Moonraker API**: `/printer/gcode/script` POST 요청
- [ ] **타임아웃**: 기본 5초, X축 이동은 5분
- [ ] **속도**: Z축 300mm/min, X축 사용자 설정값 (기본 4500mm/min)

### 참조 코드 (gui5.py 494-516)
```python
def _move_up(self):
    step_value = float(self.selected_step.replace("mm", ""))
    self._send_z_command(f"G91\nG1 Z{step_value} F300\nG90")

def _send_z_command(self, gcode):
    url = f"{MOONRAKER_URL}/printer/gcode/script"
    data = {"script": gcode}
    response = requests.post(url, json=data, timeout=5)
```

---

## 📁 PAGE 3: PrintPage (파일 선택)

### 현재 구현 (gui5.py PrintMenu 참조)
| 항목 | gui5.py 구현 | Design Guide v6 |
|------|-------------|-----------------|
| 그리드 | 2×3 (6개 파일) | 3×2 그리드 |
| USB 폴링 | 2초마다 | 동일 |
| 썸네일 | preview_cropping.png | 동일 |
| 선택 방식 | 클릭 → 선택 버튼 | 클릭 → Open 버튼 |

### TODO - 기능 요구사항

#### USB 파일 감지
- [ ] **폴링 주기**: 2초마다 `/media/user/device/` 스캔
- [ ] **3단계 스캔**: /media → user 폴더 → device 폴더
- [ ] **파일 필터**: .zip, .dlp, .photon, .ctb 확장자
- [ ] **USB 상태 표시**: "USB 감지됨: N개 장치" / "장치 없음"

#### 파일 목록 그리드
- [ ] **레이아웃**: 3×2 그리드 (6개 FileItem)
- [ ] **FileItem 구조**:
  - 썸네일 (100×100px) - ZIP 내 preview_cropping.png
  - 파일명 (아래 중앙 정렬)
- [ ] **선택 표시**: Cyan 테두리 3px + 파일명 Cyan 색상

#### 페이지네이션
- [ ] **이전/다음 버튼**: 6개 단위 페이지 전환
- [ ] **Open 버튼**: 선택된 파일 → FilePreviewPage 이동
- [ ] **선택 상태 유지**: 페이지 전환 시 선택 인덱스 보존

### 하드웨어 연동
- [ ] **USB 폴링 시작/중지**: 페이지 진입/이탈 시
- [ ] **파일시스템**: os.listdir, zipfile 모듈

### 참조 코드 (gui5.py 695-718)
```python
def detect_usb_devices(self):
    media_path = "/media"
    for user in os.listdir(media_path):
        user_path = os.path.join(media_path, user)
        for device in os.listdir(user_path):
            device_path = os.path.join(user_path, device)
            current_devices.append(device_path)
```

---

## 💡 PAGE 4: ExposurePage (노출 테스트)

### 현재 구현 (Design Guide v6 기준)
| 항목 | 기능 |
|------|------|
| 패턴 선택 | Ramp / Checker 버튼 |
| Flip 제어 | Horizontal / Vertical 토글 |
| 노출 시간 | NumberDial (±1/±10초) |
| 제어 | START / STOP 버튼 |

### TODO - 기능 요구사항

#### 테스트 패턴 선택
- [ ] **Ramp 버튼**: 그라데이션 패턴 (PATTERN_RAMP 아이콘)
- [ ] **Checker 버튼**: 체커보드 패턴 (PATTERN_CHECKER 아이콘)
- [ ] **선택 표시**: Cyan 테두리 (활성화)

#### Flip 제어
- [ ] **Horizontal 토글**: 좌우 반전
- [ ] **Vertical 토글**: 상하 반전
- [ ] **NVR2+ I2C 명령**: 해당 레지스터 설정

#### 노출 시간 설정
- [ ] **NumberDial 컴포넌트**: 기본 3.0초
- [ ] **범위**: 0.5초 ~ 60초
- [ ] **조절 버튼**: -10, -1, +1, +10

#### 제어 버튼
- [ ] **START 버튼** (Cyan):
  1. 프로젝터 ON
  2. 선택된 패턴 이미지 투영
  3. LED ON (설정된 시간)
  4. LED OFF
- [ ] **STOP 버튼** (Red):
  1. LED OFF
  2. 프로젝터 OFF

### 하드웨어 연동
- [ ] **DLPController**:
  - `projector_on()` / `projector_off()`
  - `led_on(brightness)` / `led_off()`
- [ ] **ProjectorWindow**: 테스트 패턴 이미지 투영

### 참조 코드 (dlp_simple_slideshow.py 96-189)
```python
def projector_on(self):
    result = self.cy_lib.CySetGpioValue(self.handle, 2, 1)

def led_on(self, brightness=None):
    # 0x54: LED 밝기 설정
    brightness_result = self.send_i2c(0x54, brightness_data)
    # 0x52: LED ON
    result = self.send_i2c(0x52, [0x07])
```

---

## 🧹 PAGE 5: CleanPage (트레이 청소)

### 현재 구현 (Design Guide v6 기준)
| 항목 | 기능 |
|------|------|
| 시간 설정 | NumberDial (초 단위) |
| 제어 | START / STOP 버튼 |
| 타이머 | 남은 시간 카운트다운 |

### TODO - 기능 요구사항

#### 청소 시간 설정
- [ ] **NumberDial**: 기본 30초
- [ ] **범위**: 10초 ~ 300초 (5분)
- [ ] **표시**: "30 sec" 형식

#### 타이머
- [ ] **QTimer**: 1초마다 감소
- [ ] **남은 시간 표시**: 크게 중앙에 표시
- [ ] **완료 시**: CompletedDialog 표시

#### 제어 버튼
- [ ] **START 버튼**:
  1. Z축 홈 이동 (G28 Z)
  2. Z축 0.1mm 상승
  3. LED ON (전체 조사)
  4. 타이머 시작
  5. 타이머 종료 → LED OFF
- [ ] **STOP 버튼**: 즉시 LED OFF + 타이머 중지

### 하드웨어 연동
- [ ] **MotorController**: Z축 홈, 상승
- [ ] **DLPController**: LED ON/OFF

---

## ⚙️ PAGE 6: SystemPage (시스템 메뉴)

### TODO - 기능 요구사항
- [ ] **레이아웃**: 2×2 그리드 (4버튼)
- [ ] **버튼**:
  - Device Info → DeviceInfoPage
  - Language → LanguagePage
  - Service → ServicePage
  - Network → 알림창 "구현중입니다"

### 하드웨어 연동
- [ ] 없음

---

## 📋 PAGE 7: DeviceInfoPage (장치 정보)

### TODO - 기능 요구사항
- [ ] **정보 테이블 표시**:
  - Model: VERICOM DLP Printer
  - Serial Number: (읽어오기)
  - Firmware Version: (Klipper 버전)
  - Board: CM4 + Manta M8P 2.0
  - Projector: NVR2+
  - Resolution: 1440×2560
  - Build Volume: 68×120×150mm

### 하드웨어 연동
- [ ] **Moonraker API**: 펌웨어 버전 조회

---

## 🌐 PAGE 8: LanguagePage (언어 설정)

### TODO - 기능 요구사항
- [ ] **선택지**: English / 한국어
- [ ] **선택 표시**: Cyan 테두리
- [ ] **적용**: 설정 저장 후 재시작 또는 즉시 반영

### 하드웨어 연동
- [ ] **설정 파일**: JSON으로 저장/로드

---

## 📞 PAGE 9: ServicePage (서비스 정보)

### TODO - 기능 요구사항
- [ ] **연락처 정보 표시**:
  - Email: support@vericom.com
  - Website: www.vericom.com
  - Tel: (전화번호)
- [ ] **아이콘**: MAIL, GLOBE, INFO 아이콘 사용

### 하드웨어 연동
- [ ] 없음

---

## 🖼️ PAGE 10: FilePreviewPage (파일 미리보기)

### 현재 구현 (gui5.py FilePreviewPage 참조)
| 항목 | gui5.py 구현 | Design Guide v6 |
|------|-------------|-----------------|
| 썸네일 | 400×300px | 120×100px (컴팩트) |
| 파라미터 | 6개 항목 | InfoRow로 표시 |
| 편집 필드 | 블레이드 속도, 평탄화 횟수, LED 파워 | EditableRow + NumericKeypad |
| 버튼 | Delete, Start, Pause, Stop, Back | Delete, Start |

### TODO - 기능 요구사항

#### 파일 정보 표시
- [ ] **썸네일**: preview_cropping.png (120×100px)
- [ ] **파일명**: 상단 표시

#### 파라미터 표시 (InfoRow)
- [ ] Total Layers: `{totalLayer}개`
- [ ] Normal Exp.: `{normalExposureTime}초`
- [ ] Bottom Exp.: `{bottomLayerExposureTime}초`
- [ ] Bottom Layers: `{bottomLayerCount}개`
- [ ] Lift Height: `{normalLayerLiftHeight}mm`
- [ ] Lift Speed: `{normalLayerLiftSpeed}mm/min`

#### 편집 가능 항목 (EditableRow)
- [ ] **Blade Speed**: 기본 1500 mm/min, 범위 100~10000
- [ ] **LED Power**: 기본 440, 범위 91~1023
- [ ] **Leveling Cycles**: 기본 1, 범위 0~5 (평탄화 횟수)

#### 터치 키패드 (NumericKeypad)
- [ ] 3×4 숫자 버튼 그리드
- [ ] Backspace (Amber), Confirm (Green)
- [ ] 범위 초과 시 빨간 테두리 피드백
- [ ] Cancel/Confirm 버튼

#### 제어 버튼
- [ ] **Delete 버튼** (Red): 파일 삭제 확인 다이얼로그
- [ ] **Start 버튼** (Cyan): PrintProgressPage로 이동 + 프린팅 시작

### 하드웨어 연동
- [ ] **ZIP 파일 파싱**: extract_print_parameters() 함수
- [ ] **파일 삭제**: os.remove()

### 참조 코드 (gui5.py 967-1011)
```python
def show_file(self, file_path: str):
    self.print_params = extract_print_parameters(file_path)
    self.total_layers = self.print_params['totalLayer']
    
    with zipfile.ZipFile(file_path, 'r') as z:
        if "preview_cropping.png" in z.namelist():
            data = z.read("preview_cropping.png")
            pix = QPixmap()
            pix.loadFromData(data)
```

---

## ⏳ PAGE 11: PrintProgressPage (인쇄 진행)

### 현재 구현 (gui5.py FilePreviewPage 내 프린팅 상태)
| 항목 | gui5.py 구현 | Design Guide v6 |
|------|-------------|-----------------|
| 진행 표시 | progress_bar (400×25px) | 별도 페이지로 분리 |
| 버튼 | Pause, Stop | PAUSE, STOP (큰 버튼) |
| 상태 관리 | is_printing, is_paused | 별도 상태 관리 |

### TODO - 기능 요구사항

#### 진행 정보 표시
- [ ] **썸네일**: 120×100px (FilePreviewPage에서 전달)
- [ ] **파일명**: 현재 프린팅 파일
- [ ] **진행률 바**: QProgressBar + 퍼센트 라벨
- [ ] **ProgressInfoRow**:
  - Layer: `562 / 1250`
  - Elapsed: `25:30` (경과 시간)
  - Remaining: `30:15` (예상 남은 시간)
  - Blade Speed: `1500 mm/min`
  - LED Power: `440`

#### 시간 계산
- [ ] **경과 시간**: QTimer 1초마다 업데이트
- [ ] **남은 시간 계산**: `(total - current) × avg_layer_time`

#### 제어 버튼
- [ ] **PAUSE 버튼** (Amber):
  - 프린팅 중 → "PAUSE" 표시, 일시정지
  - 일시정지 중 → "RESUME" 표시 (Cyan), 재개
- [ ] **STOP 버튼** (Red):
  - StopConfirmDialog 표시
  - 확인 시: 프린팅 중지 → MainPage 이동

#### 상태 관리
- [ ] **Printing**: 타이틀 "Printing...", PAUSE/STOP 활성화
- [ ] **Paused**: 타이틀 "Paused", RESUME 버튼으로 변경
- [ ] **Stopping**: 타이틀 "Stopping...", 버튼 비활성화
- [ ] **Completed**: CompletedDialog → 확인 시 홈으로

### 하드웨어 연동
- [ ] **PrintWorker (QThread)**: 별도 스레드에서 프린팅 시퀀스 실행
- [ ] **시그널**: 
  - `pause_requested` / `resume_requested` / `stop_requested`
  - `progress_updated(current, total)`
  - `print_completed` / `print_stopped`

### 참조 코드 (dlp_simple_slideshow.py 654-670)
```python
def pause():
    projector.is_paused = True

def resume():
    projector.is_paused = False

def stop():
    projector.is_stopped = True
    projector.is_paused = False

projector.pause_func = pause
projector.resume_func = resume
projector.stop_func = stop
```

---

## 🔄 핵심 프린팅 시퀀스 (run_slideshow 분석)

### 전체 플로우
```
1. 초기화
   ├─ DLPController 초기화
   ├─ MotorController 초기화
   ├─ Z축 홈 (G28 Z)
   └─ X축 홈 (G28 X)

2. 레진 평탄화 (옵션, leveling_cycles > 0)
   ├─ Z축 0.1mm 이동
   ├─ X축 0mm → 125mm 왕복 (N회)
   └─ Z축 홈 복귀

3. 프로젝터 ON

4. 메인 프린팅 루프 (레이어별)
   ├─ 일시정지/정지 체크
   ├─ Z축 레이어 높이 설정
   ├─ X축 0mm → 125mm 이동 (블레이드)
   ├─ 이미지 투영
   ├─ LED ON (노출 시간)
   ├─ LED OFF
   ├─ Z축 리프트 (5mm 상승)
   ├─ X축 125mm → 0mm 복귀
   ├─ Z축 다음 레이어 높이로 하강
   └─ 진행률 콜백

5. 종료
   ├─ LED OFF
   ├─ 프로젝터 OFF
   └─ 리소스 정리
```

### 레이어별 파라미터
| 구분 | 바닥 레이어 | 일반 레이어 |
|------|-----------|-----------|
| 노출 시간 | bottomLayerExposureTime | normalExposureTime |
| 리프트 높이 | bottomLayerLiftHeight | normalLayerLiftHeight |
| 리프트 속도 | bottomLayerLiftSpeed | normalLayerLiftSpeed |
| 레이어 수 | bottomLayerCount | totalLayer - bottomLayerCount |

### 하드웨어 명령 요약
| 동작 | G-code / I2C |
|------|-------------|
| Z축 홈 | `G28 Z` |
| X축 홈 | `G28 X` |
| Z축 이동 | `G0 Z{pos} F{speed}` |
| X축 이동 | `G0 X{pos} F{speed}` |
| 프로젝터 ON | `CySetGpioValue(handle, 2, 1)` |
| 프로젝터 OFF | `CySetGpioValue(handle, 2, 0)` |
| LED ON | I2C 0x52 [0x07] |
| LED OFF | I2C 0x52 [0x00] |
| LED 밝기 | I2C 0x54 [LSB, MSB, LSB, MSB, LSB, MSB] |

---

## 📋 우선순위 정리

### Phase 1: UI 페이지 ✅ (Design Guide v6 기준 완료)
- [x] MainPage, ToolPage, ManualPage
- [x] PrintPage, FilePreviewPage, PrintProgressPage
- [x] ExposurePage, CleanPage
- [x] SystemPage, DeviceInfoPage, LanguagePage, ServicePage

### Phase 2: 핵심 기능 연동 🔥 (최우선)
- [ ] **PrintWorker**: QThread 기반 프린팅 워커
- [ ] **MotorController 통합**: Z축/X축 Moonraker API
- [ ] **DLPController 통합**: NVR2+ I2C 제어
- [ ] **실시간 상태 업데이트**: 위치, 진행률

### Phase 3: 고급 기능
- [ ] 다국어 지원 (영어/한국어)
- [ ] 설정 저장 (JSON)
- [ ] 에러 핸들링 및 복구
- [ ] 부팅 자동 실행 (systemd)

---

## 📝 참고사항

### 화면 모드 요구사항
- **전체화면(키오스크) 모드 필수**: 작업표시줄 없이 깔끔하게
- **다이얼로그/팝업은 예외**: NumericKeypad, ConfirmDialog 등은 오버레이 형태로 표시
- **해상도**: 1024×600px 고정

### 라즈베리파이 주의사항
- `background-color: transparent` 사용 금지
- QFrame 내 QLabel에 `border: none` 명시
- 명시적 배경색 지정 필수

### Moonraker API 엔드포인트
- G-code 전송: `POST /printer/gcode/script`
- 프린터 상태: `GET /printer/objects/query`
- 펌웨어 정보: `GET /printer/info`

### NVR2+ I2C 주소
- Slave Address: `0x1B`
- LED ON: `0x52 [0x07]`
- LED OFF: `0x52 [0x00]`
- LED 밝기: `0x54 [LSB, MSB, LSB, MSB, LSB, MSB]`