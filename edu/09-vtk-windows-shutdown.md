# 09. Windows에서 VTK/OpenGL 종료 오류 다루기

> 이 문서는 AI가 프로젝트 개발 과정에서 작성한 기술 학습 기록입니다. 개인 환경 정보 없이 일반적인 Windows Qt/VTK 종료 순서만 설명합니다.

## 증상

앱 창을 닫을 때 다음과 유사한 VTK 오류가 콘솔에 반복될 수 있습니다.

```text
vtkWin32OpenGLRenderWindow: wglMakeCurrent failed in Clean()
```

이는 모델 데이터나 CUDA 추론 실패가 아니라, Windows OpenGL 컨텍스트의 종료 순서 문제입니다.

## 원인

`pyvistaqt.QtInteractor`는 Qt 위젯 안에서 VTK OpenGL 컨텍스트를 사용합니다. Qt가 위젯과 native OpenGL 컨텍스트를 파괴하기 시작한 뒤 애플리케이션 코드가 다시 `plotter.clear()` 또는 `plotter.close()`를 호출하면, VTK가 이미 유효하지 않은 컨텍스트에 `wglMakeCurrent`를 요청할 수 있습니다.

## 해결

| 잘못된 종료 순서 | 수정한 종료 순서 |
| --- | --- |
| timer 중지 → VTK `clear/close` 강제 호출 → Qt 위젯 종료 | timer 중지 → Python actor 참조 해제 → Qt가 interactor/컨텍스트를 소유 순서대로 폐기 |

뷰포트의 `closeEvent`는 타이머만 중지하고, 늦은 시점의 명시적 VTK OpenGL 정리를 강제하지 않습니다. 이 방식은 VTK 리소스 정리를 생략하는 것이 아니라 Qt/VTK 통합 위젯의 소유권 규칙을 따르는 것입니다.

## 재발 방지 검증

1. 모델 뷰어, Rig, Animate 화면을 연 뒤 앱을 정상 종료합니다.
2. 콘솔/진단 로그에 `wglMakeCurrent failed in Clean()`이 없는지 확인합니다.
3. 종료 전 타이머가 실행 중이어도 종료가 지연되거나 크래시하지 않는지 확인합니다.
4. 앱 재시작 후 뷰포트가 정상 생성되는지 확인합니다.

이 검증은 Windows 네이티브 OpenGL 컨텍스트를 실제로 생성해야 하므로, 자동 단위 테스트와 별도로 수동 종료 스모크를 유지합니다.
