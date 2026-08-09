# 로컬 캐릭터 배경 제거 Provider 추가 보고서

## 목적

게임/애니메이션 캐릭터 캡처의 배경이 Shape GLB에 사각형 또는 배경 조각으로 재구성되는 문제를 줄이기 위해, Hunyuan3D Shape 이전에 캐릭터만 분리하는 로컬 CUDA Provider를 추가했다.

## 적용한 구성

- Provider: `rembg` `isnet-anime`
- Runtime: `onnxruntime-gpu` CUDAExecutionProvider
- 모델: `isnet-anime.onnx` (실제 다운로드 크기 176,069,933 bytes)
- 캐시: `U2NET_HOME`으로 설정되는 앱 로컬 cache 하위 경로
- 다운로드: `download-segmentation-model` 명령으로만 수행한다. 재구성 중에는 모델 다운로드를 시도하지 않는다.

## 구현 내용

1. `SegmentationProvider` 계약과 CUDA 전용 `RembgAnimeSegmentationProvider`를 추가했다.
2. ONNX Runtime 세션은 CUDAExecutionProvider만 요청하고 CPU execution-provider fallback을 비활성화한다.
3. 선택 프레임을 원본 PNG, 투명 RGBA 분리 PNG, 알파 마스크 PNG로 attempt artifact에 보존한다.
4. ONNX 세션을 명시적으로 해제하고 garbage collection/CUDA cache cleanup을 수행한 뒤 Hunyuan Shape를 로드한다.
5. Capture 화면은 Shape와 Segmentation Provider가 모두 준비된 경우에만 Standard 생성 버튼을 활성화한다.
6. Provider 호환성 보고와 GPU smoke 결과에 Segmentation 준비 상태를 추가했다.

## 런타임 호환성 수정

처음 설치된 ONNX Runtime 1.28은 CUDA 13 DLL을 요구해 현재 프로젝트의 PyTorch CUDA 12.4 DLL과 함께 실제 CUDA 세션을 만들지 못했다. 해당 버전은 사용하지 않고, CUDA 12.x/PyTorch 2.4+ 호환 범위의 ONNX Runtime GPU 1.26.0으로 고정했다.

실제 `isnet-anime` CUDA session 생성과 분리 이미지/알파 마스크 생성 smoke test는 통과했다. CPU fallback으로 통과 처리하지 않았다.

## 검증

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-segmentation
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-provider-compatibility
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

`test-segmentation`은 생성 fixture를 사용하며 사용자 캡처 이미지를 보관하지 않는다.

## Hunyuan 전체 재검증 상태

Segmentation이 포함된 Hunyuan Shape 전체 smoke는 실행 중 다른 GPU 작업이 이미 메모리를 사용 중인 상태에서 제한 시간을 초과했다. 첫 CUDA Diffusion step은 확인됐지만, 이를 전체 성공으로 기록하지 않는다.

외부 GPU 작업을 정리해 여유 VRAM을 확보한 뒤 아래 명령을 다시 실행해야 한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-reconstruction
```

이 제한은 총 VRAM 기반 Capability Tier를 변경하지 않으며, 실행 시점의 free VRAM 부족에 따른 검증 보류다.

## 수동 확인 항목

1. Capture를 완료한 뒤 `Generate Standard Shape`가 Segmentation readiness와 함께 활성화되는지 확인한다.
2. Processing 로그에 `Removing the capture background on local CUDA`가 먼저 표시되는지 확인한다.
3. 완료 attempt의 `inputs/isolated-character.png`, `inputs/character-mask.png`를 확인한다.
4. 배경이 넓은 게임 장면으로 재생성해 사각형 메시가 줄어드는지 시각 검토한다. 분리 품질은 모델의 실제 결과이며, 기술 검증 PASS가 시각적 충실도를 보장하지는 않는다.
