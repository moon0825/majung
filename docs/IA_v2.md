# 마중(Majung) v2: UX 정보구조도 (Information Architecture)

> v2 화면 구조·내비게이션·상태 모델·컴포넌트 매핑. 각 상태가 **실동작**인지
> **인상(impression)** 인지 명시한다. 동결 동작(lock/paced/health/suppress·키 핸들러)은 무수정.

## 1. 화면 인벤토리 (Top-level)

```
마중 (단일 페이지, 탭 전환)
├── 근로자 화면      [tab=customer]  ← v1, 무수정 (PhoneFrame + CustomerChat + ControlPanel)
├── 유학생 화면 (D-2) [tab=student]   ← v2 신규 (StudentView)
└── 관리자 대시보드   [tab=admin]     ← v1 (AdminDashboard + BusinessValuePanel)
```

- **내비게이션**: topbar `<nav class="tabs">` 3버튼. 기본 `customer`. 우측 health 인디케이터(API 연결됨/오프라인 미리보기).
- **확장 규칙**: 새 세그먼트 = 새 탭 + 새 `<section>` + 전용 surface 컴포넌트. App.jsx는 탭/섹션 추가만(외과적). 근로자 동결 동작에 손대지 않는다.

## 2. 유학생 화면 콘텐츠 위계 (`StudentView`)

```
StudentView
├── 헤더            Wang Wei · D-2 · 中文/한국어 · "같은 엔진, 두 입구"           [인상]
├── 계좌 활성화 단계  AccountLifecycle stepper: 가계좌→한도계좌(현재)→정식계좌      [stepper=인상 / eligible 플래그=실동작]
└── 2×2 그리드
    ├── ① 등록금 자동 송금   금액·환율칩 → [보내기] → 게이트 3핀 + TX            [실동작]
    ├── ② 한도해제 코치      연속급여 미터(3/3) → 메시지 → [전환 신청]           [실동작(read-only) / 신청 버튼=인상]
    ├── ③ 재학중 신용형성    신용 단계 칩 · 연속급여/정시거래 통계               [인상(read-only 스냅샷)]
    └── ④ 졸업 후 신용 전환  적격·가등급 칩 + 안내 (원화 헤드라인 미노출)        [인상]
    └── 푸터: 스테이블코인·CB = Future Work                                    [로드맵 표기]
```

## 3. 상태 모델 (3축): 실동작 / 인상 표기

### 축 A: 페르소나
| 상태 | surface | 등급 |
|---|---|---|
| 근로자(E-9) | CustomerChat | 실동작 (v1) |
| 유학생(D-2) | StudentView | 실동작 ①② / 인상 ③④ |

### 축 B: 계좌 생애주기 (`AccountLifecycle`)
| 단계 | 표현 | 등급 |
|---|---|---|
| 가계좌(생체인증) | stepper `done` | 인상 (JB 인프라 전제) |
| 한도계좌(현재) | stepper `current` | 실동작 (limit-status가 현 단계 판정) |
| 정식계좌(해제) | stepper `ready`(eligible 시) | 실동작 판정(`activation.evaluate_limit_release`) / 전환 신청 클릭=인상 |

### 축 C: 언어
| 언어 | 사용 surface | 비고 |
|---|---|---|
| vi (베트남어) | 근로자 | v1 |
| zh (中文) | 유학생 (메인) | v2. 게이트 통지의 vi 문구는 **유학생 화면에 미노출**. status 기준 zh/ko 카피 자체 렌더 |
| ko (한국어) | 전 surface 병기 | 심사·법적 고지 |

## 4. 컴포넌트 → 파일 매핑

| UI 요소 | 파일 | 데이터 출처 | 등급 |
|---|---|---|---|
| 유학생 탭/섹션 | `frontend/src/App.jsx` (탭·섹션 추가만) | `tab` 상태 | 해당 없음 |
| 유학생 surface | `frontend/src/components/StudentView.jsx` (신규) | api 3종 + `demoData.STUDENT.MOCK` | 실동작+인상 |
| 계좌 생애주기 | `frontend/src/components/AccountLifecycle.jsx` (신규) | props(current·eligible) | 인상+판정 |
| API 창구 | `frontend/src/api.js` (메서드 3종 추가) | `/student/*`, `/account/limit-status` | 실동작 |
| 시드 상수·목 | `frontend/src/demoData.js` (`STUDENT` 블록 추가) | seed.py 미러 | 해당 없음 |
| 스타일 | `frontend/src/styles.css` (`.student-*`·`.acct-*` 추가) | 기존 디자인 토큰만 참조 | 해당 없음 |

## 5. 인터랙션 흐름 (유학생 ① 등록금)

```
[보내기 클릭]
   → (busyRef 로컬 잠금, App 의 lock 과 무관)
   → paced(api.tuitionExecute, 900ms)         ← 오프라인이면 STUDENT.MOCK.tuition
   → 응답 status 로 분기
        executed → 초록 결과 카드 + Gate A/B/C PASS 핀 + TX
        held/str_hold/blocked/rejected → 경고 카드 + 게이트 핀 (zh/ko 카피)
```

- **오프라인 폴백**: `healthy=false` → 초기 로드/송금 모두 `demoData.STUDENT.MOCK` 사용. 화면이 죽지 않는다(api.js throw 금지 계약 유지).
- **단축키 비충돌**: 근로자 Digit1–5 핸들러는 `tab==="customer"` 가드 → 유학생 탭에서 무반응.
