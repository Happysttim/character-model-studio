# 07. 리깅 GLB 검증과 CPU Linear Blend Skinning

> 이 문서는 AI가 프로젝트 개발 과정에서 작성한 기술 학습 기록입니다. 예시는 일반화된 구조만 다루며 개인 데이터와 환경 정보는 포함하지 않습니다.

## 문제

골격 선이 뷰어에 보인다는 사실만으로는 캐릭터가 실제로 포즈를 따라 변형된다는 뜻이 아닙니다. 초기 구현에서 본 회전값과 오버레이는 바뀌더라도, 메쉬 정점이 bind pose에 남아 포즈 편집이 시각적으로 반영되지 않는 문제가 생길 수 있습니다.

정확한 변형에는 다음 glTF 데이터가 모두 필요합니다.

| 데이터 | 목적 |
| --- | --- |
| `POSITION` | bind pose의 원본 정점 위치 |
| `JOINTS_0` | 각 정점에 영향을 주는 관절 인덱스(보통 최대 4개) |
| `WEIGHTS_0` | 각 관절 영향도 |
| `skin.joints` | skin 인덱스에서 실제 node로의 매핑 |
| inverse bind matrices | bind pose와 현재 관절 행렬의 차이를 계산 |
| node 부모 관계 | 부모 회전을 자식 관절에 전파 |

## 해결: GLB accessor → 계층 행렬 → CPU LBS → VTK 갱신

```text
GLB 열기
  → accessor/bufferView 디코딩
  → bind pose 정점과 skin 데이터 확보
  → 현재 local quaternion을 node 행렬로 변환
  → 부모 → 자식 순서로 world 행렬 합성
  → world × inverseBind skin 행렬 계산
  → 각 정점에 가중합(LBS) 적용
  → VTK PolyData point 좌표 교체
```

수식은 다음과 같습니다.

```text
deformedPosition = Σ(weight_i × (jointWorld_i × inverseBind_i) × bindPosition)
```

여기서 회전은 프로젝트 전역 규칙대로 정규화된 `[x, y, z, w]` quaternion입니다. 애니메이션 보간도 Euler 각의 단순 선형 보간이 아니라 shortest-path SLERP를 사용합니다.

## 구현 시 핵심 점검

### accessor 디코딩

glTF accessor는 component type, 요소 개수, byte offset, byte stride를 따릅니다. `JOINTS_0`은 정수형일 수 있고 `WEIGHTS_0`은 정규화된 정수 또는 부동소수점일 수 있으므로, 메쉬 배열로 단순 캐스팅하기 전에 accessor 메타데이터를 해석해야 합니다.

### 행렬 방향

glTF 행렬은 열 우선 저장을 사용합니다. Python/NumPy의 행 우선 배열로 읽을 때 전치 처리와 동차 좌표(`x, y, z, 1`) 처리를 일관되게 하지 않으면 관절이 반대 방향으로 움직이거나 원점으로 붕괴할 수 있습니다.

### 부모-자식 전파

선택 본의 local 회전만 바꾸더라도 자식의 world 행렬은 다시 계산해야 합니다. 이를 누락하면 본 오버레이와 메쉬 변형의 계층 관계가 서로 달라집니다.

### VTK 업데이트

새 메쉬를 매 프레임 다시 생성하는 대신, 검증된 동일 topology의 `PolyData` point 배열을 갱신합니다. 이 방식은 텍스처/actor 설정을 보존하고, UI 뷰어의 선택·카메라 상태가 불필요하게 초기화되는 일을 줄입니다.

## 독립 검증이 필요한 이유

렌더링 성공과 리깅 유효성은 다른 문제입니다.

| 상황 | 뷰어 | Rig Validation | 처리 |
| --- | --- | --- |
| 정적 mesh는 정상, skin 없음 | 표시 가능 | 실패 | 정적 Review만 허용 |
| skeleton 선은 표시, weight가 모두 0 | 표시 가능 | 실패 | Animate 비활성화 |
| weight가 약간 비정규화 | 표시 가능 | 경고/수정 가능 | 정책에 따라 허용 |
| 유효 계층·가중치·IBM | 표시 가능 | 통과 | Pose/Animation 활성화 |

실제 변형 스모크는 bind pose와 다른 회전을 한 번 적용한 뒤, 정점 좌표 변화와 자식 관절의 world transform 변화를 확인합니다. 이 검증은 Dummy mesh나 본 선 표시로 대체할 수 없습니다.

## 성능과 한계

CPU LBS는 초기 구현으로 정확성을 보장하기 좋지만, 매우 큰 메쉬에서는 프레임 시간이 길어질 수 있습니다. 이 경우에도 먼저 실제 프로파일링으로 병목을 기록해야 하며, 기준을 충족하지 못할 때만 기존 Python/VTK 구조 안에서 GPU skinning을 검토합니다. 웹 렌더러나 별도 서버 도입은 해결책이 아닙니다.
