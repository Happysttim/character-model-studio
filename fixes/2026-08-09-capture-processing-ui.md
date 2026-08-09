# Capture·Processing·UI 수정 보고서

## 처리한 문제

### 1. 영역 선택 후 자동 녹화

- 영역 드래그 후 마우스를 놓으면 영역만 잠금 처리한다.
- 잠금 뒤에는 `Alt + /` 또는 `Start recording` 버튼으로만 녹화를 시작한다.
- 녹화 중 `Alt + /` 또는 `Stop recording` 버튼은 종료 요청을 보낸다.
- 영역 선택 overlay는 잠금 즉시 닫히므로 추가 클릭으로 Bounds가 다시 바뀌지 않는다.

### 2. 검은 썸네일

- 녹화 중 화면 밝기와 선명도를 기준으로 가장 적합한 프레임을 썸네일로 선택한다.
- 모든 프레임이 검은색이면 검은 썸네일을 저장하지 않고 게임 창/선택 영역을 확인할 수 있는 오류를 표시한다.

### 3. Preview 파일 점유

- Discard 전에 미디어 재생과 source를 해제한다.
- Windows가 파일을 아직 점유한 경우 삭제를 강제하지 않고, 해당 capture를 안전하게 보존한 뒤 안내한다.

### 4. 비어 있던 Processing 화면

- 실제 Hunyuan3D Standard Shape attempt를 시작하면 Processing 화면으로 이동한다.
- 진행률을 알 수 있는 단계는 determinate progress bar로, CUDA inference처럼 단계 비율을 제공하지 않는 구간은 indeterminate progress bar로 표시한다.
- preprocessing, provider load, shape generation, validation, 완료/오류 메시지를 화면 로그에 누적한다.

### 5. 창 및 시각 구성

- Windows 기본 타이틀 프레임을 제거하고 앱 내부 title bar와 최소화/최대화/닫기 제어를 추가했다.
- 메인 workspace surface의 border radius를 제거했다.
- 밝은 Cream, Apricot, Coral, Terracotta 계열의 다색 배경과 warm glass surface로 테마를 조정했다.

## 검증

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-capture
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-ui
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

- Capture 테스트: 9건 통과
- UI 테스트: 4건 통과
- 전체 검증은 source format, lint, typecheck, unit/UI 테스트를 포함한다.

## 수동 확인 항목

- 실제 게임 창에서 선택 영역 잠금 후 `Alt + /`로 시작되는지 확인한다.
- 녹화 중 동일 Hotkey로 종료되는지 확인한다.
- Preview와 썸네일이 검은색이 아닌지 확인한다.
- Processing에서 단계 로그와 진행 표시가 업데이트되는지 확인한다.
- Frameless 창의 이동 및 창 제어 버튼 동작을 확인한다.
