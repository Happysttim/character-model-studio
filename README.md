# Character Model Studio

> Codex Harness 기반으로 생성한 Windows 전용 로컬 캐릭터 3D 제작 애플리케이션입니다.

Character Model Studio는 화면/영상의 캐릭터를 로컬에서 분리하고, CUDA 기반 3D 재구성·텍스처 생성·GLB 검증·자동 리깅·포즈 편집·애니메이션 미리보기까지 연결하는 Python 데스크톱 프로그램입니다.

PySide6와 Qt Widgets로 구성된 단일 Windows 앱이며, 웹 프런트엔드, HTTP API, 별도 백엔드, 클라우드 서비스 또는 Docker 런타임을 사용하지 않습니다. 모델 가중치와 프로젝트 파일은 사용자가 지정한 로컬 저장소에만 보관합니다.

## 주요 기능

### 캡처와 프로젝트

- 화면 영역 선택 후 `Alt + /`로 녹화 시작·종료
- MP4, MOV, MKV, AVI 기존 영상 가져오기
- 프로젝트 생성, 목록 조회, 재열기
- 녹화/가져온 영상의 썸네일 및 미리보기
- SQLite + 로컬 프로젝트 폴더 기반 저장

### 캐릭터 3D 재구성

- CUDA ONNX Runtime 기반 `isnet-anime` 캐릭터/배경 분리
- 영상 후보 프레임 평가 및 단일·다중 시점 입력 선택
- Hunyuan3D 2.0 Standard Shape GLB 생성
- Stable Fast 3D(SF3D) 단일 이미지 텍스처 GLB 생성
- Hunyuan3D-2GP 다중 시점 Shape + Delight/Paint Texture GLB 생성
- 생성 단계, 실제 진행 상태, 날짜·시각이 포함된 작업 로그 표시
- GLB 구조·geometry·material·viewer 로드 검증

### 검토, 리깅, 애니메이션

- 내장 PyVista/VTK 3D 뷰어: 카메라 프리셋, 와이어프레임, 그리드, 축, bounds, turntable
- 생성 GLB 또는 기존 GLB를 Review로 불러와 Accept / Reject / Regenerate
- UniRig 기반 CUDA Skeleton + Skinning 생성 및 텍스처 GLB 보존 병합
- 리그 계층·관절·가중치·inverse bind matrix 독립 검증
- GLB `JOINTS_0`/`WEIGHTS_0`/inverse bind matrix를 읽는 CPU Linear Blend Skinning 미리보기
- 본 선택, local rotation, bind pose reset
- From/To Pose 저장, quaternion SLERP 보간, 타임라인 seek, 재생·일시정지·루프
- 저장한 포즈·애니메이션의 재열기
- 한국어/영어 UI 언어 선택

## 아키텍처

```text
Capture / Import
  → CUDA Segmentation
  → Reconstruction / Texture
  → Static GLB Validation + Review
  → UniRig Skeleton + Skinning
  → Rig Validation
  → Pose / Animation Preview
```

무거운 CUDA 작업은 UI 스레드에서 실행하지 않습니다. 특히 Hunyuan3D-2GP Texture와 UniRig는 앱이 소유한 로컬 자식 Python 프로세스에서 실행될 수 있으며, 이는 서버가 아니라 앱이 시작·취소·종료·검증하는 단발성 로컬 작업입니다.

## 요구 사항

| 항목 | 기준 |
| --- | --- |
| 운영체제 | Windows 11 x64 권장, Windows 10 일부 시각 효과 폴백 |
| Python | CPython 3.11 |
| GPU | NVIDIA CUDA 지원 GPU — 실제 AI 추론에 필수 |
| 메모리 | 대형 텍스처 GLB 검토를 위해 32GB 이상 권장 |
| 디스크 | 기본 앱·가상환경·선택 모델·프로젝트 결과를 위해 최소 30GB 이상의 여유 공간 권장 |
| 개발 도구 | `uv`, Git, Hugging Face CLI(`hf`) |

### GPU Capability 기준

앱은 단일 `GPU supported` 값이 아니라 CUDA, Segmentation, Shape, Texture, Rigging, Skeleton Editing, Animation Editing/Playback을 각각 판정합니다. 준비되지 않은 기능은 비활성화되며 그 이유를 UI에 표시합니다.

| 작업 | 공급자 | VRAM 기준 |
| --- | --- | --- |
| Standard Shape | Hunyuan3D 2.0 | 공식 참고치 약 6GiB |
| Standard Shape + Texture | Hunyuan3D 2.0 | 공식 참고치 약 16GiB |
| 실험적 단일 이미지 Texture | Stable Fast 3D | 로컬 CUDA/모델/네이티브 확장 준비 필요 |
| 실험적 다중 시점 Shape + Texture | Hunyuan3D-2GP | 검증된 공급자 경로 기준 총 12GiB 이상 |
| High Quality Shape | Hunyuan3D 2.1 | 공식 참고치 약 10GiB + 별도 런타임 호환성 |
| High Quality Shape + Texture | Hunyuan3D 2.1 | 공식 참고치 약 29GiB + 별도 런타임 호환성 |
| 자동 리깅 | UniRig | 프로젝트에서 검증한 공급자 기준 총 8GiB 이상 + 격리 런타임 |

각 기준은 공급자별 독립 기준입니다. 예를 들어 UniRig 기준이 Hunyuan3D의 텍스처 기준을 낮추지 않으며, 현재 남은 VRAM이 아닌 **총 물리 VRAM**으로 Tier를 분류합니다.

## 설치

프로젝트 루트 PowerShell에서 실행합니다.

```powershell
uv venv --python 3.11 .venv
uv sync --group dev
```

Hugging Face CLI가 없다면 설치합니다.

```powershell
uv tool install huggingface_hub
```

접근 권한이 필요한 모델을 받을 경우에는 먼저 로그인합니다.

```powershell
hf auth login
```

> 모델 가중치는 Git에 포함하지 않습니다. 모든 다운로드는 프로젝트의 `.local/cache` 아래에 저장되고, 앱 실행 중에는 예상하지 못한 온라인 재다운로드를 막기 위해 로컬 캐시만 사용합니다.

## 모델·가중치 다운로드

루트의 [`download-model-to-project-cache.ps1`](download-model-to-project-cache.ps1)는 선택한 가중치를 프로젝트 로컬 캐시에 저장합니다. 실행이 끝나면 앱을 다시 시작해 Readiness를 새로 고치세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model <모델-이름>
```

### 필수 모델

캡처·영상에서 캐릭터를 분리해 재구성하려면 아래 모델이 필요합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model required
```

| 모델 | 용도 | 캐시 위치 |
| --- | --- | --- |
| rembg `isnet-anime` | CUDA 배경 분리와 RGBA/alpha mask 생성 | `.local/cache/segmentation/rembg/isnet-anime.onnx` |

### 재구성 모델

```powershell
# 기본 Standard Shape
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model hunyuan2-shape

# 실험적 Hunyuan3D-2GP 다중 시점 Shape
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model hunyuan2gp-shape

# 실험적 Hunyuan3D-2GP Delight/Paint Texture
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model hunyuan2gp-texture

# 실험적 Stable Fast 3D 기본 checkpoint
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model sf3d
```

| 선택 값 | Hugging Face 저장소 | 다운로드 범위 | 기본 캐시 위치 |
| --- | --- | --- | --- |
| `hunyuan2-shape` | `tencent/Hunyuan3D-2` | `hunyuan3d-dit-v2-0/*` | `.local/cache/hunyuan3d-2/` |
| `hunyuan2gp-shape` | `tencent/Hunyuan3D-2mv` | `hunyuan3d-dit-v2-mv/*` | `.local/cache/hunyuan3d-2gp/tencent/Hunyuan3D-2mv/` |
| `hunyuan2gp-texture` | `tencent/Hunyuan3D-2` | `hunyuan3d-delight-v2-0/*`, `hunyuan3d-paint-v2-0/*` | `.local/cache/hunyuan3d-2gp/tencent/Hunyuan3D-2/` |
| `sf3d` | `stabilityai/stable-fast-3d` | `config.yaml`, `model.safetensors` | `.local/cache/sf3d/stable-fast-3d/` |

SF3D와 Hunyuan3D-2GP는 가중치 외에도 `external/` 아래의 공급자 소스와 해당 네이티브 확장/런타임 준비가 필요합니다. 앱의 Readiness가 `READY`가 아닌 경우 Diagnostics에서 누락된 항목을 확인하세요. 가중치만 내려받았다고 기능이 자동 활성화되지는 않습니다.

### UniRig 리깅 모델

```powershell
# Skeleton + Skinning checkpoint와 필요한 transformer metadata를 함께 다운로드
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model unirig

# 필요한 항목만 개별 다운로드
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model unirig-skeleton
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model unirig-skinning
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -Model unirig-transformer
```

UniRig는 기본 앱의 Python 환경과 분리된 Python 3.11 런타임을 사용합니다. 이 런타임, `external/UniRig` 소스, 로컬 checkpoint, 네이티브 확장이 모두 준비되어야 Create Rig가 활성화됩니다. 원본 텍스처 GLB는 유지하고, 생성된 스키닝 정보를 병합한 별도 rigged GLB를 만듭니다.

### 모든 선택 모델 다운로드

충분한 디스크 공간이 있을 때에만 실행하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\download-model-to-project-cache.ps1 -AllOptional
```

`-AllOptional`은 필수 Segmentation 모델과 현재 스크립트가 지원하는 Hunyuan3D 2.0 Shape, Hunyuan3D-2GP Shape/Texture, SF3D, UniRig 가중치를 함께 요청합니다. 이후 공급자별 외부 소스 및 런타임 준비는 별도로 완료해야 합니다.

## 실행

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 run
```

개발 검증은 다음 명령으로 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

## 사용 방법

### 1. 프로젝트 만들기 또는 열기

1. **Projects**에서 `Create project`를 선택하고 이름을 입력합니다.
2. 기존 항목을 선택해 다시 엽니다.
3. 프로젝트는 앱 설치 위치가 아닌 설정된 로컬 데이터 위치에 저장됩니다.

### 2. 영상 준비

다음 중 하나를 선택합니다.

- **Capture**: 화면에서 한 번 드래그해 캡처 영역을 고정한 다음 `Alt + /` 또는 `Start recording`으로 녹화를 시작/종료합니다.
- **Import existing video**: 기존 MP4/MOV/MKV/AVI를 관리되는 프로젝트 캡처 폴더로 가져옵니다.

캐릭터 전체가 프레임에 보이고, 앞·옆·뒤 방향이 충분히 담긴 영상이 다중 시점 재구성에 유리합니다.

### 3. 재구성 공급자 선택

Capture 화면에서 `READY`인 공급자를 선택합니다.

| UI 선택 | 입력 | 결과 |
| --- | --- | --- |
| Standard — Hunyuan3D 2.0 | 분리된 대표 프레임 1장 | Shape GLB |
| Textured Experimental — Stable Fast 3D | 분리된 대표 프레임 1장 | 텍스처 GLB |
| Textured Experimental — Hunyuan3D-2GP | 시간 순서가 보존된 분리 프레임 3~4장 | 다중 시점 Shape + Texture GLB |
| High Quality — Hunyuan3D 2.1 | 공급자 준비 상태에 따름 | 고품질 Shape/Texture 경로 |

`Generate Standard Shape` 또는 `Generate Textured Model`을 누르면 Processing에서 실제 단계와 로그를 볼 수 있습니다. 작업 중 취소하면 이전에 수용한 모델·리그·포즈는 유지됩니다.

### 4. Review와 리깅

1. **Review**에서 생성 결과와 기술 검증을 확인합니다. 필요하면 `Import existing GLB`로 기존 모델을 검토할 수 있습니다.
2. `Accept`를 누르면 **Rig**로 이동합니다.
3. UniRig가 `READY`이면 `Create Rig`를 선택합니다. 진행 중에는 중복 실행을 막기 위해 버튼이 비활성화됩니다.
4. 리그 검증과 skeleton overlay를 확인합니다. 정적 모델이 유효해도 리그가 유효하지 않으면 Animate는 활성화되지 않습니다.

### 5. 포즈와 애니메이션

1. **Animate**에서 리깅 GLB를 자동으로 불러옵니다.
2. 뷰어에서 관절을 선택하거나 목록에서 본을 선택합니다.
3. local rotation을 바꾸어 포즈를 만들고 `Save From Pose`, `Save To Pose`를 사용합니다.
4. Duration, Seek, Loop를 설정한 뒤 재생합니다.
5. Animation 저장 후 앱을 다시 열어도 포즈·클립을 재사용할 수 있습니다.

### 6. 언어와 진단

- **Settings**에서 한국어/영어를 선택합니다.
- **Diagnostics**에서 CUDA, VRAM Tier, 공급자 모델/런타임 Readiness와 로컬 로그를 확인합니다.

## 주요 라이브러리

| 영역 | 라이브러리 |
| --- | --- |
| Desktop UI | PySide6 |
| CUDA / AI | PyTorch, Torchvision, ONNX Runtime GPU, rembg |
| 캡처·영상 | DXcam, PyAV, OpenCV, Pillow |
| 3D / glTF | trimesh, PyVista, VTK, pyvistaqt, pygltflib |
| 애니메이션 수학 | NumPy, SciPy |
| 로컬 저장 | SQLite, Python 파일 시스템 |
| 개발·배포 | uv, pytest, ruff, mypy, PyInstaller |

## 데이터와 개인정보

- 영상, 프레임, alpha mask, GLB, 리그, 포즈, 애니메이션, 로그는 로컬 저장소에만 보관합니다.
- 앱은 추론을 위해 로컬 HTTP 서버나 원격 백엔드를 실행하지 않습니다.
- 모델 경로, 사용자 이름, 드라이브 문자, 하드웨어 식별자는 코드나 기본 문서에 하드코딩하지 않습니다.
- 모델 캐시와 프로젝트 데이터는 앱을 제거해도 자동 삭제하지 않는 정책입니다. 수동 정리 전 필요한 자산을 백업하세요.

## 라이선스 및 모델 사용 조건

애플리케이션 코드의 라이선스와 별도로, Hunyuan3D·Stable Fast 3D·UniRig·rembg 및 각 Hugging Face checkpoint는 각각의 upstream 라이선스와 사용 조건을 따릅니다. 다운로드·상업적 사용 전에 각 모델 저장소의 라이선스와 접근 조건을 확인하세요.
