# 02. 로컬 AI 런타임과 제공자 호환성

## 문제

여러 AI 제공자는 같은 Python 환경에서 서로 다른 패키지 버전을 요구한다. 설치 여부만 보고 준비 완료로 판단하면 실행 시점에 import 오류, CUDA 확장 오류 또는 모델 로드 오류가 발생한다.

| 항목 | 핵심 원칙 |
| --- | --- |
| CUDA | `torch.cuda.is_available()`뿐 아니라 실제 모델 파라미터와 Tensor 연산을 확인한다. |
| 가중치 | 추론 시 온라인 repo ID를 기본값으로 사용하지 않고, 명시적 로컬 캐시를 해석한다. |
| 의존성 | 제공자가 요구하는 버전과 앱 런타임 버전을 비교해 `PROVIDER_RUNTIME_INCOMPATIBLE`로 표시한다. |
| 네이티브 확장 | 설치 기록이 아니라 프로젝트 Python에서 실제 import로 확인한다. |

## Hunyuan3D-2GP 사례

Hunyuan3D-2GP는 특정 Transformers 버전과 `mmgp`, `mesh_processor`, `custom_rasterizer_kernel`을 요구한다. 이때 패키지 설치기가 CUDA PyTorch를 다른 버전으로 바꿀 수 있으므로, 설치 후에는 다음을 반드시 다시 확인한다.

1. PyTorch, Torchvision, Torchaudio의 CUDA 호환 버전
2. `transformers` 요구 버전
3. `mesh_processor`, `custom_rasterizer_kernel` import
4. 모델 가중치·config·Paint/Delight 체크포인트의 로컬 존재 여부

## 안전한 상태 표현

| 상태 | 의미 |
| --- | --- |
| `READY` | 로컬 파일, CUDA, 확장, 런타임 조건이 모두 충족됨 |
| `NOT_INSTALLED` | 필요한 로컬 모델 또는 확장이 없음 |
| `PROVIDER_RUNTIME_INCOMPATIBLE` | 설치는 되었으나 검증된 런타임 버전과 충돌 |
| `CUDA_UNAVAILABLE` | CPU fallback 없이 해당 AI 기능을 비활성화 |

