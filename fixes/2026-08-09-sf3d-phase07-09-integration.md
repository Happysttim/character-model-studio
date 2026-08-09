# SF3D 실험적 텍스처 Provider 통합 보고서

## 결과

Stable Fast 3D를 Hunyuan3D 2.0 Standard 기본 경로를 대체하지 않는 선택형 텍스처 Provider로 연결했다. 실제 제공 캡처를 로컬 CUDA에서 처리해 텍스처 GLB를 생성했고, 모델 검증과 Viewer 변환을 통과했다.

## 처리 흐름

`Capture → CUDA 배경 분리 → alpha 정규화 → SF3D Shape+Texture → GLB 검증 → Review`

SF3D, DINOv2, CLIP은 모두 프로젝트 로컬 캐시에서만 해석한다. 추론 중 온라인 다운로드와 CPU fallback은 허용하지 않는다.

## 검증

- 실제 캡처 기반 attempt: `READY_FOR_REVIEW`
- GLB 검증: `PASS_WITH_WARNINGS`
- Viewer 변환: 성공
- 모델 검증 테스트: 통과
- UI 테스트: 통과
- 전체 자동 테스트: 31개 통과

## 주의 사항

SF3D는 실험적 옵션이며 Hunyuan3D 2.0 Standard 기본 선택을 변경하지 않는다. 마스크가 너무 약하거나 전경이 화면 전체로 퍼지면 SF3D 실행 전 오류로 안내해야 하며, 사용자는 더 분명한 캐릭터 전경을 촬영해야 한다.
