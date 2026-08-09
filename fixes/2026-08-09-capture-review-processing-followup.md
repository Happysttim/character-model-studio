# 캡처 미리보기·처리 로그·Shape 검토 후속 수정 보고서

## 확인 결과

### 검은 캡처 미리보기

캡처가 끝난 뒤 화면의 큰 검은 영역은 저장된 `thumbnail.jpg` 자체가 아니라, 재생을 시작하지 않은 `QVideoWidget`의 기본 검은 화면이었다.

- 완료 직후에는 실제로 저장한 썸네일을 포스터로 표시한다.
- `Play capture preview`를 누를 때만 비디오 위젯으로 전환하고 MP4 재생을 시작한다.
- 썸네일 파일을 열 수 없으면 성공처럼 보이지 않고 보존 안내가 포함된 오류를 표시한다.

### 처리 로그 가독성

`QPlainTextEdit`는 처리 화면의 밝은 유리 패널과 대비되지 않는 어두운 기본 스타일을 일부 환경에서 상속받았다.

- 처리 로그에 밝은 warm surface 배경, 검은색 본문, 테두리와 선택 색상을 명시했다.
- `Noto Sans KR` → `Noto Sans` → Windows 한글 sans-serif 순서의 폰트 fallback을 적용했다.
- 진행 막대도 같은 밝은 surface 위에 amber chunk가 보이도록 명시했다.

### Diffusion/Volume 실제 진행도

기존 구현은 Hunyuan Shape 호출 전후에만 상태를 보냈으므로, Diffusion Sampling과 Volume Decoding 중에는 무한 진행 표시만 보였다.

- 로컬 Hunyuan3D 2.0 Shape 구현의 `tqdm` 반복 횟수를 실행 중에 관찰한다.
- `Diffusion Sampling n/total`, `Volume Decoding n/total`을 작업 로그에 기록한다.
- 진행 막대는 이 실제 완료 반복 수로 갱신한다. 모델 로딩처럼 정확한 총량이 없는 구간은 계속 indeterminate 상태로 남긴다.
- 외부 Hunyuan 소스 파일은 수정하지 않으며, 제공자 호출 동안에만 관찰기를 설치하고 즉시 복원한다.

### 모델 색상과 평면 형상

현재 설치·다운로드된 가중치는 `hunyuan3d-dit-v2-0` Shape 전용이다. Texture 가중치와 Texture 단계는 설치·실행하지 않았다. 따라서 이 경로가 생성하는 GLB는 색/텍스처가 없는 Shape 결과이며, 이를 텍스처 생성 성공으로 표시할 수 없다.

- 뷰어는 GLB에 실제 vertex color가 있으면 보존해서 표시한다.
- 색 데이터가 없는 Shape-only GLB는 중립 clay 색으로 표시하고 `untextured Shape`로 명시한다.
- Texture 생성은 별도 Hunyuan Texture 가중치와 CUDA capability 검증 후에만 추가할 수 있다.
- 첨부 화면의 큰 판자/배경 조각은 뷰어 grid가 아니라 실제 Shape GLB 형상일 가능성이 높다. 현재 캡처 입력의 character isolation/segmentation은 아직 제공자에 연결되어 있지 않으므로, 배경을 포함한 입력을 Shape-only 모델에 보내면 이러한 결과가 생길 수 있다. 이를 뷰어 렌더링 문제로 위장해 삭제하거나 임의의 메시를 숨기지 않는다.

## 검증

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 format
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 lint
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 typecheck
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-capture
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-ui
```

추가로 viewer GLB parsing/vertex-color 테스트와 Hunyuan progress observer의 실제 로컬 import smoke test를 수행한다.

## 수동 확인 항목

1. 캡처를 종료하면 검은 비디오 위젯 대신 선택된 썸네일 포스터가 먼저 보이는지 확인한다.
2. `Play capture preview`를 누르면 MP4가 재생되는지 확인한다.
3. 실제 Hunyuan Shape 실행에서 Processing 로그에 `Diffusion Sampling`과 `Volume Decoding`의 완료/전체 횟수가 표시되는지 확인한다.
4. 색상 없는 Shape 결과가 `untextured Shape`으로 명시되는지, 색 데이터가 있는 GLB는 vertex color로 보이는지 확인한다.
5. 배경이 포함된 게임 캡처에서 판자/배경 조각이 나오면 Texture가 아닌 segmentation 입력 품질 이슈로 분류하고, 생성 전 입력 frame과 기술 검증 결과를 함께 확인한다.
