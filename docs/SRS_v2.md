# 마중(Majung) v2: 요구사항 분석서 (SRS)

> 본선 스토리 v2 기준 요구사항 명세. 1차 출처: `README.md`, `docs/diagrams.md`,
> `docs/usecase.puml`, 본 문서의 v2 서사. 평가 용어 그대로 사용:
> **판단 → 행동 → 검증/개선** / **수집 → 검색 → 판단 → 생성 → 검증 → 후속액션**.

## 1. 배경과 범위

### 1.1 v1 → v2 서사 전환
- **v1**: 단일 외국인 근로자(E-9) · 활성계좌 전제 · 모국으로의 송신 송금 1단계 + 사채 대환 가심사 2단계.
- **v2**: JB가 외국인 금융 인프라(가계좌·한도계좌·심사엔진)를 **이미 깔아** 두었고, 마중은 그 위에서 동작하는 **활성화 레이어(Activation Layer)** 다. 두 세그먼트를 같은 엔진으로 흡수한다.
  - **근로자(E-9)**: 급여 트리거 자동 송금 + 신용 사다리(기존 1·2단계, 무수정).
  - **유학생(D-2)**: 등록금 외화 송금 + 한도계좌 해제 코치 + 재학중 신용형성 + 졸업전환 가심사.
- **핵심 명제**: "같은 엔진, 두 입구." 근로자와 유학생은 **동일한 위임장·3중 게이트**를 공유한다. 유학생 등록금 송금은 기존 `run_remittance`를 `fx_pair="KRW/CNY"`로 그대로 재사용한다(신규 송금 엔진 없음).

### 1.2 불변 원칙 (v1에서 승계, 절대 불변)
> **"LLM은 송금 실행 경로에 없다."** 의도 파싱만 LLM, 판정·실행은 전부 결정적 코드.
> Gate A(위임검증) → Gate B(Rule 한도·FX) → Gate C(AML) 순서는 단일 실행 경로다.

### 1.3 동결 구역 (수정 금지)
`backend/app/orchestrator.py`(3중 게이트·단일 실행 경로·통지 MSG), `backend/app/rules.py`(FX/AML/대환 임계값·시그니처). 프론트의 lock/busyRef·healthRef 폴백·paced 타이밍·suppressNotifs·api.js throw 금지 계약. 교차 고정 수치(18.12/18.45=+1.82%, 연 13.59%·연 246만, AML 40/70 임계치).

## 2. 액터 (Actors)

| 액터 | 유형 | v1/v2 | 설명 |
|---|---|---|---|
| 외국인 근로자 (E-9) | 1차 | v1 | 급여 트리거 자동 송금·대환 가심사 |
| **유학생 (D-2)** | 1차 | **v2 신규** | 등록금 송금·한도해제 코치·신용형성·졸업전환 |
| 보호자/관리자 (JB) | 1차 | v1 | 감사로그·STR 큐·사업가치 콘솔 |
| LLM | 보조 | v1 | 의도 파싱만 (실행권한 없음) |
| 환율 피드 | 외부 | v1 | KRW/VND · **KRW/CNY(v2)** 7일 이동평균 |
| 한패스 레일(모의) | 외부 | v1 | 송금 실행 레일 |
| JB 심사엔진(모의) | 외부 | v1 | 대환·가심사 최종 승인의 배타적 권한 |
| **가계좌 온보딩** | 외부 | **v2 신규** | 생체인증 가계좌 개설(인상, JB 인프라) |
| 스테이블코인 정산망 | Future Work | 로드맵 | 등록금 스테이블코인 정산 (미구현) |
| CB(외국인 신용평가) | Future Work | 로드맵 | 재학 이력 기반 신용평가 연계 (미구현) |

## 3. 기능 요구사항 (FR)

### 3.1 근로자 (v1, 무수정, 회귀 보존만)
- FR-W1 위임장 발급·전자서명, FR-W2 급여 트리거 자동 송금, FR-W3 의심거래 자동 보류+STR, FR-W4 사기 수취인 차단, FR-W5 무조건 철회권, FR-W6 사채 대환 가심사. (상세는 v1 기능명세서 참조.)

### 3.2 유학생 (v2 신규)

| ID | 요구사항 | 구현 등급 | 상세 |
|---|---|---|---|
| **FR-S1** | 등록금 위임 송금 | **실동작** | 대학(화이트리스트) 대상 외화 등록금을 환율 조건 충족 시 자동 송금. 기존 3중 게이트 그대로 재사용(`fx_pair=KRW/CNY`). 통지는 中文 |
| **FR-S2** | 한도해제 코치 | **실동작(read-only)** | 한도계좌 → 정식계좌 승급 조건(연속 급여 ≥3개월)을 결정적으로 판정·안내. 자금 이동 없음 |
| **FR-S3** | 재학중 신용형성 | 인상 | 연속 급여·정시 거래를 신용 이력 스냅샷으로 제시(read-only) |
| **FR-S4** | 졸업전환 가심사 | 인상(재사용 준비) | 졸업·취업비자 전환 시 대환 가심사 즉시 진행 준비. 기존 `/refi/*` 재사용. **원화 절약 헤드라인 미노출**(고정 246만과 충돌 회피), 적격·가등급만 표시 |
| **FR-A** | 계좌 생애주기 연계 | 실동작(코치)+인상(stepper) | 가계좌(생체인증·인상) → 한도계좌(현재) → 정식계좌(해제). 마중은 "언제 해제 가능한지"를 코치 |

### 3.3 판정 규칙 (결정적)
- **FR-S1 게이트 통과 조건**: Gate A 위임장 active·수취인 in-scope, Gate B `KRW/CNY` 7일평균 대비 ≥1% 유리 + 한도 내, Gate C 대학 화이트리스트(AML PASS). → `executed`.
- **FR-S2 한도해제 판정**(`activation.evaluate_limit_release`): `is_limited_account=true` ∧ `salary_months_consecutive ≥ 3` → `eligible`. 미달 시 `in_progress`(남은 개월 안내). 비한도계좌는 `full_account`.

## 4. 비기능 요구사항 (NFR)
- **NFR-1 동결 무손상**: 송금 실행 경로(orchestrator·rules)·프론트 동결 동작 무수정. `git diff` 공백으로 검증.
- **NFR-2 다국어 인상**: 유학생 surface는 中文(zh)+한국어(ko) 병기. 게이트 통지의 베트남어 문구는 유학생 화면에 노출 금지(status 기준 zh/ko 카피 자체 렌더).
- **NFR-3 세그먼트 격리·확장성**: 둘째 페르소나는 user-scoped·별도 FX 페어(`KRW/CNY`)로 추가만. 기존 자동 테스트 20건 무영향. 셋째 세그먼트도 동일 패턴(시드 + surface)으로 확장 가능.
- **NFR-4 오프라인 생존**: 백엔드 미연결 시 유학생 surface도 시드 기준 목 데이터로 레이아웃 유지(healthRef 분기).
- **NFR-5 브라보 비충돌**: 유학생 탭은 근로자 촬영 단축키(Digit1–5)와 충돌하지 않는다(키 핸들러가 `tab==="customer"`로 가드).

## 5. 제약 (Constraints)
- 새 DB 테이블 없이 기존 `accounts.is_limited_account`·`salary_months_consecutive` 필드로 처리.
- 최종 승인은 JB 심사엔진의 배타적 권한(마중은 안내·가심사까지).
- CB·스테이블코인은 **로드맵(Future Work)** 으로만 문서·UI에 표기(현재 비활성 기능).
- 신규 판정 로직은 `rules.py`/`mcp_tools.py` 밖 신규 파일(`activation.py`)로.

## 6. 추적성 매트릭스 (Traceability)

| 요구사항 | 엔드포인트 | 모듈 / 룰 | UI 컴포넌트 | 다이어그램 | 테스트 |
|---|---|---|---|---|---|
| FR-S1 등록금 송금 | `POST /student/tuition/execute` | `orchestrator.run_remittance(fx_pair="KRW/CNY")` **[동결 재사용]** | `StudentView ①` | diagrams §5 | `test_student.py::test_tuition_executes_through_three_gates`, `::test_tuition_out_of_scope_recipient_not_executed` |
| FR-S2 한도해제 코치 | `GET /account/limit-status/{user_id}` | `activation.evaluate_limit_release` **[신규]** | `StudentView ②`, `AccountLifecycle` | diagrams §6 | `test_student.py::test_limit_status_student_eligible`, `::test_limit_release_*` |
| FR-S3 신용형성 | `GET /student/credit-profile/{user_id}` | `main.py` read-only 집계 | `StudentView ③` | diagrams §6 | `test_student.py::test_credit_profile_snapshot` |
| FR-S4 졸업전환 가심사 | `POST /refi/prescreen`, `/refi/refer` **[기존]** | `mcp_tools.get_refi_offer` / `rules.prescreen_refi` | `StudentView ④` (인상) | diagrams §4 | `test_gates.py::test_refi_*` |
| FR-A 계좌 생애주기 | `GET /account/limit-status/{user_id}` | `activation.py` | `AccountLifecycle` stepper | diagrams §6 | `test_student.py::test_limit_release_full_account_when_not_limited` |
| NFR-3 격리 | (둘째 페르소나 시드) | `seed.py::_seed_student` | 없음 | 없음 | `test_student.py::test_worker_remittance_path_unaffected` (+ 기존 20건 그린) |
| 동결 원칙 | `POST /remittance/execute` (무수정) | `orchestrator`·`rules` | 없음 | §2·§3 | `test_gates.py` 전체 |

## 7. 데이터 (시드, `seed.py`)
- 둘째 페르소나 `USR-CN-2050`(Wang Wei, D-2, `language=zh`), 계좌 `is_limited_account=1`·`salary_months_consecutive=3`, 급여 3건.
- `KRW/CNY` 환율: 7일평균 0.5200 vs 현재 0.5296 = **+1.846%** → 게이트 B 통과.
- 등록금 위임장 `MND-2026-CN01`(active), 대학 수취인 `CN-UNIV-01`(화이트리스트), 졸업전환용 소액 채무 1건.
- **기존 `KRW/VND`·근로자 행은 무수정** (테스트 격리).
