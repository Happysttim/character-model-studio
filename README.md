# Character Model Studio

Character Model Studio는 **Codex 하네스(Harness)를 기준으로 생성한 Greenfield Windows 로컬 데스크톱 프로젝트**입니다. Python과 PySide6로 구성된 단일 애플리케이션이며, HTTP 서버·별도 프론트엔드·클라우드 백엔드를 사용하지 않습니다.

현재 상태는 **Reconstruction MVP 통과 단계**입니다. 즉, 영상 캡처 또는 기존 영상 불러오기부터 캐릭터 분리, 로컬 CUDA 기반 3D 생성, GLB 검증 및 검토까지의 흐름을 제공합니다.

## 제공 기능

- 화면 영역 선택 및 `Alt + /` 녹화 시작/종료
- MP4/MOV/MKV/AVI 기존 영상 불러오기
- 녹화·불러오기 영상의 썸네일 및 미리보기
- CUDA ONNX Runtime 기반 `isnet-anime` 배경 제거
- 캡처 영상에서 재구성 후보 프레임 추출 및 다중 시점 입력 선택
- Hunyuan3D 2.0 Standard Shape 재구성
- Stable Fast 3D 실험적 텍스처 GLB 생성
- Hunyuan3D-2GP 실험적 다중 시점 Shape + Texture GLB 생성
- GLB 기술 검증, 내장 3D 검토, Accept/Reject/Regenerate
- Processing 화면의 진행 상태와 날짜·시각 포함 작업 로그
- SQLite 및 프로젝트 폴더 기반 로컬 데이터 보관

Hunyuan3D-2GP Texture는 메인 UI 응답성을 보존하기 위해 앱이 소유한 별도 로컬 Python 자식 프로세스에서 실행됩니다. 네트워크 서버는 사용하지 않습니다.

## 모델과 로컬 캐시

모델 경로는 하드코딩하지 않습니다. `CHARACTER_MODEL_STUDIO_DATA_DIR` 또는 각 모델 환경 변수를 우선 사용하며, 개발 실행 스크립트는 프로젝트의 `.local`을 데이터 루트로 설정합니다.

| 용도 | 모델 | 기본 프로젝트 상대 캐시 경로 |
| --- | --- | --- |
| Standard Shape | Hunyuan3D 2.0 | `.local/cache/hunyuan3d-2/` |
| 실험적 다중 시점 Shape | Hunyuan3D-2GP / Hunyuan3D-2mv | `.local/cache/hunyuan3d-2gp/tencent/Hunyuan3D-2mv/hunyuan3d-dit-v2-mv/` |
| 실험적 Texture | Hunyuan3D-2GP Delight/Paint | `.local/cache/hunyuan3d-2gp/tencent/Hunyuan3D-2/` |
| 실험적 Texture | Stable Fast 3D | `.local/cache/sf3d/` |
| 캐릭터 분리 | rembg `isnet-anime` | `.local/cache/segmentation/rembg/isnet-anime.onnx` |

가중치 다운로드는 명시적인 사용자 작업입니다. 추론 중에는 `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`을 적용해 예기치 않은 다운로드를 막습니다.

## 최소 권장 사양과 GPU Capability

- 운영체제: Windows 11 x64 (Windows 10은 일부 시각 효과 폴백)
- Python: CPython 3.11
- GPU: NVIDIA CUDA 지원 GPU
- Standard Shape: 공식 참고치 VRAM 약 6GB
- Standard Shape + Texture: 공식 참고치 VRAM 약 16GB
- Hunyuan3D-2GP 실험적 Shape + Texture: 검증된 실험 경로 기준 VRAM 12GB 이상 권장
- 디스크: 애플리케이션·Python 환경·모델 캐시·프로젝트 결과를 위해 최소 30GB 여유 공간 권장. 여러 제공자 가중치를 함께 보관하면 더 많은 공간이 필요합니다.
- 시스템 메모리: 대형 텍스처 GLB 검토를 위해 32GB 이상 권장

Capability는 단일 `GPU_SUPPORTED` 값이 아니라 CUDA, Segmentation, Standard Shape, Standard Texture, 실험적 SF3D Texture, 실험적 Hunyuan3D-2GP Texture, High Quality Shape/Texture, Rigging, Skeleton Editing, Animation Editing/Playback으로 독립 판정됩니다. 앱은 시작 시 모델 파일·CUDA·VRAM·네이티브 확장을 검사하고, 준비되지 않은 제공자는 이유와 함께 비활성화합니다.

## 주요 라이브러리

- UI: PySide6
- CUDA AI: PyTorch, Torchvision, ONNX Runtime GPU, rembg
- 영상·이미지: DXcam, PyAV, OpenCV, Pillow
- 3D: trimesh, PyVista, VTK, pyvistaqt, pygltflib
- 로컬 저장: SQLite, Python 표준 파일 시스템
- 개발: uv, pytest, ruff, mypy, PyInstaller

## 설치

PowerShell에서 프로젝트 루트로 이동합니다.

```powershell
uv venv --python 3.11 .venv
uv sync --group dev
```

각 AI 제공자의 외부 소스·가중치·네이티브 확장은 해당 제공자 안내에 따라 별도로 준비해야 합니다. 모델 가중치는 Git에 포함하지 않습니다.

프로젝트 루트의 `download-model-to-project-cache.ps1`은 필수 `isnet-anime` 세그멘테이션 모델을 기본으로 준비하며, Hunyuan3D 2.0 Shape, SF3D, Hunyuan3D-2GP Shape/Texture는 명시적으로 선택할 때만 프로젝트 로컬 캐시에 다운로드합니다.

## 실행과 사용

PowerShell 실행 정책 때문에 스크립트가 차단되면 다음처럼 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 run
```

1. Capture 화면에서 화면 영역을 지정하고 녹화하거나 `Import existing video`로 기존 영상을 선택합니다.
2. 준비 상태가 `READY`인 Reconstruction Provider를 선택합니다.
3. `Generate Standard Shape` 또는 `Generate Textured Model`을 실행합니다.
4. Processing에서 단계와 로그를 확인합니다.
5. Review에서 GLB를 확인한 뒤 Accept, Reject 또는 Regenerate를 선택합니다.
