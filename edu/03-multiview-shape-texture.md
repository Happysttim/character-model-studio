# 03. 다중 시점 Shape + Texture 파이프라인

## 단일 프레임의 한계

단일 이미지 Shape 재구성은 보이지 않는 후면·측면을 추정해야 하므로, 캐릭터 일부만 남거나 배경 평면이 모델에 섞일 수 있다. 캐릭터를 회전하며 촬영한 영상에서는 여러 시점을 선택하는 것이 더 적절하다.

## 파이프라인

```text
영상 → 후보 프레임 추출 → CUDA 배경 분리 → 시간 구간별 대표 시점 선택
→ front/left/back/right RGBA 입력 → Multi-view Shape → 임시 GLB 저장
→ Shape unload → Delight → Paint → UV Bake → 텍스처 GLB
```

## 핵심 설계

| 단계 | 책임 | 주의점 |
| --- | --- | --- |
| Frame selection | 시간 구간마다 완전한 캐릭터 프레임 선택 | 시점 이름은 촬영 순서 가정임을 provenance에 기록 |
| Segmentation | RGBA와 alpha mask 저장 | CUDA ONNX provider만 허용 |
| Shape | 다중 시점 메시 생성 | Shape 모델 파라미터가 `cuda:*`인지 확인 |
| Texture | Delight와 Paint를 순차적으로 CUDA에 올림 | 무거운 모델을 동시에 상주시켜서는 안 됨 |
| Export | GLB 저장 | Shape GLB와 최종 텍스처 GLB를 구분 |

## 로컬 경로 문제

일부 upstream 로더는 Windows 절대 경로를 Hugging Face repo ID로 잘못 처리한다. 해결은 로더가 `isdir()`인 명시적 체크포인트 디렉터리를 먼저 처리하게 하고, 그 경우 다운로드 API를 호출하지 않도록 하는 것이다.

