# 05. 대형 텍스처 GLB 검증 메모리 문제

## 문제

대형 생성 메시에서 `trimesh.split(only_watertight=False)`는 연결 요소마다 메시와 노멀 데이터를 복제한다. GLB가 기술적으로 유효해도 검증 단계의 CPU 메모리 부족으로 `MemoryError`가 발생할 수 있다.

## 해결 방법

| 검사 | 처리 방식 |
| --- | --- |
| 파일 존재, 삼각형 토폴로지, 인덱스, Bounds, 퇴화 삼각형 | 항상 수행 |
| 연결 요소 진단 | face 수가 큰 메시에서는 생략하고 `PASS_WITH_WARNINGS` 기록 |
| Viewer 변환 | `MemoryError`이면 앱 실패 대신 경고 기록 |

## 중요한 구분

이 문제는 GPU Shape·Texture 추론 실패가 아니다. GPU가 GLB를 생성한 뒤, CPU 기반 기술 검증이 과도한 임시 메모리를 사용한 문제다. 따라서 핵심 검증을 유지하면서 비용이 큰 진단만 조건부로 건너뛰는 방식이 적절하다.
