# 04. Texture 중 UI 응답성 보장

## 문제

QThread에서 실행해도 대형 Texture 베이크·인페인팅은 Python GIL과 시스템 메모리를 장시간 점유할 수 있다. 이 경우 추론은 백그라운드여도 Windows가 부모 GUI를 `응답 없음`으로 표시할 수 있다.

## 해결 구조

```text
PySide6 UI 프로세스
  → QThread 작업 제어기
    → 로컬 Python 자식 프로세스
      → Delight / Paint / UV Bake / 텍스처 GLB 저장
```

| 구분 | 부모 앱 | 자식 프로세스 |
| --- | --- | --- |
| 역할 | UI, 취소 요청, 상태 표시, 최종 검증 | 무거운 Texture CUDA 작업 |
| 데이터 | 프로젝트 attempt 경로 | Shape GLB, RGBA 입력, 출력 GLB |
| 통신 | 종료 코드와 결과 파일 확인 | 표준 출력/오류와 종료 코드 |

## 결과 처리

자식 프로세스가 0으로 종료하고 출력 GLB가 존재할 때만 부모 앱이 Model Validation으로 진행한다. 실패 시 오류 출력의 마지막 부분을 사용자에게 전달하고, 서버나 HTTP 통신 없이 로컬 작업만 정리한다.

