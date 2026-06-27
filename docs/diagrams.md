# 마중(Majung) 다이어그램 모음

> 기능명세서 §2(시스템 구성도)·§4(주요 기능 흐름도)에 캡처해 삽입.
> GitHub에서 그대로 렌더됨. UML 정식 유스케이스는 [`usecase.puml`](./usecase.puml) 참고.
> 평가 라벨을 자구 그대로 사용: **판단 → 행동 → 검증/개선** / **수집 → 검색 → 판단 → 생성 → 검증 → 후속액션**

---

## 1. 유스케이스 (§4)

```mermaid
flowchart LR
    User(["👤 외국인 근로자<br/>(E-9, 모국어)"])
    Admin(["👤 보호자/관리자"])
    FX["⏱ 환율 피드"]
    JB["🏦 JB 심사엔진(모의)"]
    HP["🔁 한패스 레일(모의)"]
    LLM["🧠 LLM (의도 파싱)"]

    subgraph 마중["마중 (Majung)"]
        UC1["위임장 발급<br/>모국어 재확인+전자서명"]
        UC2["위임 송금 자동 실행<br/>(급여 트리거)"]
        UC3["의심거래 자동 보류<br/>+모국어 질문"]
        UC4["사기 수취인 차단<br/>(블랙리스트)"]
        UC5["위임 철회<br/>(무조건 철회권)"]
        UC7["사채 대환 가심사<br/>연 246만원 절약"]
        UC8["JB 심사엔진 회부<br/>(승인 아님)"]
        UC9["감사로그·STR 큐 조회"]
    end

    User --- UC1
    User --- UC5
    User --- UC7
    Admin --- UC9
    FX --> UC2
    UC2 -. 송금 .-> HP
    LLM -. 의도 파싱 .-> UC1
    UC2 -. extend .-> UC3
    UC2 -. extend .-> UC4
    UC7 -- include --> UC8
    UC8 --> JB
```

---

## 2. 시스템 구성도 — 3중 게이트 (§2)

```mermaid
flowchart TD
    A["사용자 발화 / 급여입금 이벤트<br/>(모국어 자연어)"]
    B["🧠 LLM 의도 파싱<br/>자연어만 담당 · 금액/실행 결정 못 함"]
    A --> B
    B -->|구조화된 intent| GA

    subgraph GATE["3중 게이트 — 전부 결정적 코드"]
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

## 3. 핵심 기능 흐름 — 1막 위임 송금 e2e (§4)

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

## 4. 핵심 기능 흐름 — 2막 대환 가심사 (§4)

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
    ORC->>U: 연 246만원 절약 · 4블록 동일비중(금소법 모의) [검증]
    Note right of U: "예상치이며 최종 승인은 JB 심사엔진"
    U->>ORC: [JB에 신청]
    ORC->>JB: refer_to_jb_engine (승인 아님·회부) [후속액션]
    JB-->>U: 접수번호
```
