# 마중(Majung) 다이어그램 모음

> 기능명세서 §2(시스템 구성도)·§4(주요 기능 흐름도)에 캡처해 삽입.
> GitHub에서 그대로 렌더됨. UML 정식 유스케이스는 [`usecase.puml`](./usecase.puml) 참고.
> 평가 라벨을 자구 그대로 사용: **판단 → 행동 → 검증/개선** / **수집 → 검색 → 판단 → 생성 → 검증 → 후속액션**

---

## 1. 유스케이스 (§4)

```mermaid
flowchart LR
    User(["👤 외국인 근로자<br/>(E-9, 모국어)"])
    Student(["🎓 유학생<br/>(D-2, 中文)"])
    Admin(["👤 보호자/관리자"])
    FX["⏱ 환율 피드<br/>KRW/VND·KRW/CNY"]
    JB["🏦 JB 심사엔진(모의)"]
    HP["🔁 한패스 레일(모의)"]
    LLM["🧠 LLM (의도 파싱)"]

    subgraph 마중["마중 (Majung): 같은 엔진, 두 입구"]
        UC1["위임장 발급<br/>모국어 재확인+전자서명"]
        UC2["위임 송금 자동 실행<br/>(급여 트리거)"]
        UC3["의심거래 자동 보류<br/>+모국어 질문"]
        UC4["사기 수취인 차단<br/>(블랙리스트)"]
        UC5["위임 철회<br/>(무조건 철회권)"]
        UC7["사채 대환 가심사<br/>연 약 250만 원 절약"]
        UC8["JB 심사엔진 회부<br/>(승인 아님)"]
        UC9["감사로그·STR 큐 조회"]
        SUC1["🎓 등록금 위임 송금<br/>(KRW/CNY, 대학 화이트리스트)"]
        SUC2["🎓 한도해제 코치<br/>(가계좌→정식계좌)"]
        SUC3["🎓 재학중 신용형성"]
        SUC4["🎓 졸업전환 가심사"]
    end

    User --- UC1
    User --- UC5
    User --- UC7
    Student --- SUC1
    Student --- SUC2
    Student --- SUC3
    Student --- SUC4
    Admin --- UC9
    FX --> UC2
    FX --> SUC1
    UC2 -. 송금 .-> HP
    SUC1 -. 송금 .-> HP
    LLM -. 의도 파싱 .-> UC1
    UC2 -. extend .-> UC3
    UC2 -. extend .-> UC4
    SUC1 -. include 3중 게이트 .-> UC2
    SUC4 -- include --> UC8
    UC7 -- include --> UC8
    UC8 --> JB
```

> **v2 핵심**: 유학생 등록금 송금(SUC1)은 근로자 자동 송금(UC2)과 **동일한 위임장·3중 게이트**를
> `fx_pair=KRW/CNY`로 그대로 재사용한다(새 송금 엔진 없음). CB·스테이블코인은 Future Work.

---

## 2. 시스템 구성도: 3중 게이트 (§2)

```mermaid
flowchart TD
    A["사용자 발화 / 급여입금 이벤트<br/>(모국어 자연어)"]
    B["🧠 LLM 의도 파싱<br/>자연어만 담당 · 금액/실행 결정 못 함"]
    A --> B
    B -->|구조화된 intent| GA

    subgraph GATE["3중 게이트: 전부 결정적 코드"]
        GA["Gate A · 위임장 검증<br/>전자서명·유효기간·철회·범위"]
        GB["Gate B · Rule 한도·조건<br/>FX Rule + 금액 한도"]
        GC["Gate C · 화이트리스트 + AML<br/>structuring·신규×고액×심야·블랙리스트"]
        GA -->|통과| GB --> |통과| GC
    end

    GC -->|PASS| EXE["실행 엔진<br/>송금 → 건별 모국어 통지 + 철회 버튼"]
    GC -->|HOLD / STR| HOLD["보류 + 모국어 질문<br/>STR 후보 큐"]
    GC -->|블랙리스트| BLK["즉시 차단"]
    EXE --> VR["검증/개선<br/>사후 성과 → 위임 임계값 조정 제안"]

    style GATE fill:#eef5ff,stroke:#9cc2e5
    style EXE fill:#e8f6ee,stroke:#1a7f37
    style BLK fill:#fdecea,stroke:#cf222e
```

---

## 3. 핵심 기능 흐름: 1단계 위임 송금 e2e (§4)

```mermaid
sequenceDiagram
    autonumber
    participant U as 사용자(모국어)
    participant LLM as LLM(의도파싱)
    participant ORC as 오케스트레이터(MCP 호스트)
    participant DB as 모의 뱅킹 코어
    participant HP as 한패스 레일(모의)

    Note over U,HP: 수집 → 검색 → 판단 → 생성 → 검증 → 후속액션
    U->>LLM: "월급 오면 엄마한테, 환율 좋을 때만, 200만원까지"
    LLM-->>ORC: intent=remit, 파라미터(후보)
    Note right of ORC: LLM은 실행 결정 못 함
    ORC->>DB: 급여입금 감지 / 환율(7일평균) [수집·검색]
    ORC->>ORC: Gate A 위임장 검증 [판단]
    ORC->>ORC: Gate B FX +1.82% & 한도 [판단]
    ORC->>ORC: Gate C AML 화이트리스트 [판단]
    ORC->>HP: execute_remittance (PASS 후에만) [행동]
    HP-->>ORC: tx_id, 영수증(모의)
    ORC->>U: 베트남어 건별 통지 + [철회] [생성·검증]
    ORC->>DB: 감사로그 기록 [후속액션]
```

---

## 4. 핵심 기능 흐름: 2단계 대환 가심사 (§4)

```mermaid
sequenceDiagram
    autonumber
    participant U as 사용자(모국어)
    participant ORC as 대환 Agent
    participant DB as 모의 뱅킹 코어
    participant JB as JB 심사엔진(모의)

    U->>ORC: "사채 부담돼" (대환 의도)
    ORC->>DB: 급여·사채·비자 조회 [수집]
    ORC->>ORC: 적격 필터(비자>만기·DSR≤0.40·다중채무<3·급여≥3개월) [판단]
    ORC->>ORC: 절약액/월상환/총상환/연체가산 계산 [생성]
    ORC->>U: 연 246만 원 절약, 4블록 동일비중(금소법 모의) [검증]
    Note right of U: "예상치이며 최종 승인은 JB 심사엔진"
    U->>ORC: [JB에 신청]
    ORC->>JB: refer_to_jb_engine (승인 아님·회부) [후속액션]
    JB-->>U: 접수번호
```

---

## 5. 핵심 기능 흐름: v2 유학생 등록금 위임 송금 (§4)

> **기존 3중 게이트 그대로 재사용.** 신규는 얇은 엔드포인트 하나(`/student/tuition/execute`)뿐이며,
> 동일 `run_remittance` 를 `fx_pair="KRW/CNY"` 로 호출한다. 오케스트레이터·룰 무수정.

```mermaid
sequenceDiagram
    autonumber
    participant S as 유학생(中文)
    participant SV as StudentView(표시 레이어)
    participant EP as POST /student/tuition/execute
    participant ORC as 오케스트레이터(동결)
    participant DB as 모의 뱅킹 코어
    participant HP as 한패스 레일(모의)

    Note over S,HP: 수집 → 검색 → 판단 → 생성 → 검증 → 후속액션
    S->>SV: "환율 좋을 때 등록금 보내기"
    SV->>EP: mandate_id·대학 bnf_id·등록금액
    EP->>ORC: run_remittance(fx_pair="KRW/CNY")
    ORC->>DB: KRW/CNY 7일평균 / 위임장 조회 [수집·검색]
    ORC->>ORC: Gate A 위임장 검증 [판단]
    ORC->>ORC: Gate B FX +1.846% & 한도 4백만 내 [판단]
    ORC->>ORC: Gate C 대학 화이트리스트 AML PASS [판단]
    ORC->>HP: execute_remittance (PASS 후에만) [행동]
    HP-->>ORC: tx_id, 영수증(모의)
    ORC-->>EP: outcome(executed, gates A/B/C)
    EP-->>SV: status·gates (message_local[vi]는 미전달 가정)
    SV->>S: status 기준 中文/한국어 카피 + 게이트 3핀 [생성·검증]
    Note right of SV: 동결 통지(vi)는 학생 화면에 노출 안 함
```

---

## 6. 핵심 기능 흐름: v2 가계좌 → 한도해제 → 활성화 (§4)

> **자금 이동 없음.** read-only 코치. 한도해제 판정은 신규 결정적 함수
> `activation.evaluate_limit_release`(연속급여 ≥3개월). 송금 경로와 무관.

```mermaid
sequenceDiagram
    autonumber
    participant S as 유학생(中文)
    participant SV as StudentView / AccountLifecycle
    participant LE as GET /account/limit-status
    participant CE as GET /student/credit-profile
    participant AV as activation.evaluate_limit_release
    participant DB as 모의 뱅킹 코어

    Note over S,DB: JB가 깐 가계좌·한도계좌 위의 활성화 레이어
    S->>SV: 유학생 화면 진입
    SV->>LE: user_id
    LE->>DB: get_account_balance (is_limited·연속급여) [수집]
    LE->>AV: 결정적 판정 [판단]
    AV-->>LE: status=eligible(3/3개월) [생성]
    LE-->>SV: 해제 가능 + 中文/한국어 메시지
    SV->>CE: user_id (신용형성 스냅샷)
    CE->>DB: 연속급여·정시거래 집계 [수집]
    CE-->>SV: 신용 단계(인상) [검증]
    SV->>S: 생애주기 stepper(가계좌→한도→정식) + [전환 신청]
    Note right of S: 졸업전환 시 기존 /refi 가심사로 연결(재사용 준비)
```
