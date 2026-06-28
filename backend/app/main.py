"""FastAPI 오케스트레이터 (MCP 호스트).

엔드포인트:
  POST /chat                       , 자연어 → LLM 의도 파싱 → 라우팅 (실행은 게이트가)
  POST /remittance/execute         , 1막: 3중 게이트 통과 시에만 송금
  GET  /fx/{pair}                  , 환율 + 7일 이동평균
  POST /refi/prescreen             , 2막: 대환 가심사 (승인 아님)
  POST /mandate/issue              , 위임장 초안 발급 (pending_sign)
  POST /mandate/{id}/sign          , 위임장 전자서명 (active)
  POST /mandate/{id}/revoke        , 무조건 철회권
  POST /salary/deposit             , 급여 입금 트리거 → 자동 송금 시뮬레이션
  GET  /notifications/{user_id}    , 건별 통지 이력 (최신순)
  GET  /audit/{user_id}            , 감사로그 (설명가능성)
  GET  /str-queue                  , AML STR 후보 큐
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import activation, llm, mcp_tools, orchestrator
from .db import get_conn
from .models import (
    MandateIssueRequest,
    RefiPrescreenRequest,
    RemittanceRequest,
    SalaryDepositRequest,
)

app = FastAPI(title="마중(Majung) API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "majung"}


@app.post("/chat")
def chat(payload: dict) -> dict:
    """LLM은 의도 파싱만. 실행 결정은 절대 못 한다.

    create_mandate 의도 시 mandate_draft·reply_ko·reply_local 추가 반환.
    """
    text = payload.get("text", "")
    parsed = llm.parse_intent(text)
    result: dict = {
        "intent": parsed.intent,
        "params": parsed.params,
        "note": "LLM은 의도 파싱만. 실행은 3중 게이트가 결정합니다.",
    }
    if parsed.intent == "create_mandate":
        result["mandate_draft"] = parsed.mandate_draft
        result["reply_ko"] = parsed.reply_ko
        result["reply_local"] = parsed.reply_local
    return result


@app.post("/remittance/execute")
def remittance_execute(req: RemittanceRequest) -> dict:
    conn = get_conn()
    try:
        outcome = orchestrator.run_remittance(
            conn,
            mandate_id=req.mandate_id,
            bnf_id=req.bnf_id,
            amount_krw=req.amount_krw,
            occurred_at=req.occurred_at,
        )
        return {
            "status": outcome.status,
            "message_ko": outcome.message_ko,
            "message_local": outcome.message_local,
            "tx_id": outcome.tx_id,
            "gates": [
                {"gate": t.gate, "label": t.label, "passed": t.passed, "detail": t.detail}
                for t in outcome.traces
            ],
        }
    finally:
        conn.close()


@app.get("/fx/{base}/{quote}")
def fx(base: str, quote: str, window_days: int = 7) -> dict:
    conn = get_conn()
    try:
        res = mcp_tools.get_fx_rate(conn, f"{base}/{quote}", window_days)
        if not res.get("found"):
            raise HTTPException(404, "환율 데이터 없음")
        return res
    finally:
        conn.close()


@app.post("/refi/prescreen")
def refi_prescreen(req: RefiPrescreenRequest) -> dict:
    conn = get_conn()
    try:
        return mcp_tools.get_refi_offer(conn, req.user_id)
    finally:
        conn.close()


@app.post("/refi/refer")
def refi_refer(payload: dict) -> dict:
    """가심사 결과를 JB 심사엔진(모의)에 회부. 승인 아님."""
    conn = get_conn()
    try:
        return mcp_tools.refer_to_jb_engine(
            conn, payload["user_id"], payload.get("refi_draft", {}))
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# v2 유학생 세그먼트 — 추가 엔드포인트 3종.
# 송금 실행 경로(orchestrator·rules)는 무수정. 등록금 송금은 동일 run_remittance를
# fx_pair=KRW/CNY 로 재사용("같은 엔진, 두 입구"). 나머지 둘은 read-only 코치/스냅샷.
# ─────────────────────────────────────────────────────────────
@app.post("/student/tuition/execute")
def student_tuition_execute(req: RemittanceRequest) -> dict:
    """유학생 등록금 외화 송금. 기존 3중 게이트 100% 재사용(fx_pair만 KRW/CNY)."""
    conn = get_conn()
    try:
        outcome = orchestrator.run_remittance(
            conn,
            mandate_id=req.mandate_id,
            bnf_id=req.bnf_id,
            amount_krw=req.amount_krw,
            fx_pair="KRW/CNY",
            occurred_at=req.occurred_at,
        )
        return {
            "status": outcome.status,
            "message_ko": outcome.message_ko,
            "message_local": outcome.message_local,
            "tx_id": outcome.tx_id,
            "gates": [
                {"gate": t.gate, "label": t.label, "passed": t.passed, "detail": t.detail}
                for t in outcome.traces
            ],
        }
    finally:
        conn.close()


@app.get("/account/limit-status/{user_id}")
def account_limit_status(user_id: str) -> dict:
    """한도계좌 → 정식계좌 승급 코치(read-only). 자금 이동 없음."""
    conn = get_conn()
    try:
        bal = mcp_tools.get_account_balance(conn, user_id)
        if not bal.get("found"):
            raise HTTPException(404, f"계좌 없음: {user_id}")
        res = activation.evaluate_limit_release(
            is_limited_account=bal["is_limited_account"],
            salary_months_consecutive=bal["salary_months_consecutive"],
        )
        return {
            "user_id": user_id,
            "is_limited_account": bal["is_limited_account"],
            "status": res.status,
            "eligible": res.eligible,
            "months_consecutive": res.months_consecutive,
            "min_months": res.min_months,
            "remaining_months": res.remaining_months,
            "min_salary_krw": res.min_salary_krw,
            "message_ko": res.message_ko,
            "message_local": res.message_local,
        }
    finally:
        conn.close()


@app.get("/student/credit-profile/{user_id}")
def student_credit_profile(user_id: str) -> dict:
    """재학중 신용형성 스냅샷(read-only). 연속급여·정시거래 기반 인상 카드용."""
    conn = get_conn()
    try:
        acct = conn.execute(
            "SELECT salary_months_consecutive FROM accounts WHERE user_id = ?", (user_id,),
        ).fetchone()
        if acct is None:
            raise HTTPException(404, f"계좌 없음: {user_id}")
        months = acct["salary_months_consecutive"]
        salary_count = conn.execute(
            "SELECT COUNT(*) AS c FROM salary_events WHERE user_id = ?", (user_id,),
        ).fetchone()["c"]
        tx_count = conn.execute(
            "SELECT COUNT(*) AS c FROM transactions WHERE user_id = ? AND status = 'executed'",
            (user_id,),
        ).fetchone()["c"]
        # 신용 단계(인상): 연속급여 개월수로 단계 라벨링
        step = "형성 시작" if months < 3 else ("신용 형성 중" if months < 6 else "신용 안정")
        return {
            "user_id": user_id,
            "months_consecutive": months,
            "salary_event_count": salary_count,
            "on_time_tx_count": tx_count,
            "on_time_ratio_pct": 100,            # 정시 거래(인상 스냅샷)
            "credit_step": step,
            "message_ko": "꾸준한 급여 입금과 정시 거래가 신용 이력으로 쌓이고 있어요.",
            "message_local": "稳定的工资入账与按时交易正在累积为您的信用记录。",
        }
    finally:
        conn.close()


@app.post("/mandate/issue")
def mandate_issue(req: MandateIssueRequest) -> dict:
    """위임장 초안 → mandates 테이블에 pending_sign 으로 저장.

    전자서명 전 단계, esign_hash 없음. 서명은 POST /mandate/{id}/sign.
    """
    conn = get_conn()
    try:
        draft = req.draft.copy()
        # mandate_id 자동 발급 (초안에 없으면)
        mandate_id = draft.get("mandate_id") or f"MND-{uuid.uuid4().hex[:10].upper()}"
        draft["mandate_id"] = mandate_id
        draft["user_id"] = req.user_id

        # valid_until 기본값
        valid_until = draft.get("valid_until", "2026-12-31T23:59:59Z")

        # esign 필드는 서명 전 비어있음(placeholder)
        draft.setdefault("esign", {
            "signed_at": "", "method": "biometric_or_pin_mock",
            "esign_hash": "", "reconfirmed_in_language": False,
        })

        conn.execute(
            "INSERT INTO mandates(mandate_id, user_id, json_blob, status, valid_until, "
            "esign_hash, revoked) VALUES (?,?,?,?,?,?,?)",
            (mandate_id, req.user_id,
             json.dumps(draft, ensure_ascii=False),
             "pending_sign", valid_until, "", 0),
        )
        conn.commit()

        # 요약문 생성, 한국어·베트남어
        limits = draft.get("limits", {})
        limit_krw = limits.get("limit_per_tx_krw", 0)
        bnf_list = draft.get("beneficiary_whitelist", [])
        bnf_name = bnf_list[0]["name"] if bnf_list else "미지정"
        summary_ko = (
            f"위임장 [{mandate_id}] 생성됨 (서명 대기 중)\n"
            f"• 수취인: {bnf_name}\n"
            f"• 한도: 1회·월 최대 {limit_krw // 10_000}만원\n"
            f"• FX 조건: 7일평균 대비 ≥1% 유리할 때 자동 실행\n"
            f"• 철회권: 언제든 즉시 철회 가능\n"
            f"서명 후 활성화됩니다."
        )
        summary_local = (
            f"Ủy quyền [{mandate_id}] đã tạo (đang chờ ký)\n"
            f"• Người nhận: {bnf_name}\n"
            f"• Hạn mức: tối đa {limit_krw // 1_000_000} triệu / lần và / tháng\n"
            f"• Điều kiện tỷ giá: tự động khi tốt hơn TB 7 ngày ≥1%\n"
            f"• Có thể hủy bất cứ lúc nào\n"
            f"Sẽ kích hoạt sau khi ký."
        )
        mcp_tools.append_audit_log(conn, req.user_id, "mandate_issued",
                                   {"mandate_id": mandate_id, "status": "pending_sign"})
        return {
            "mandate_id": mandate_id,
            "status": "pending_sign",
            "summary_ko": summary_ko,
            "summary_local": summary_local,
        }
    finally:
        conn.close()


@app.post("/mandate/{mandate_id}/sign")
def mandate_sign(mandate_id: str) -> dict:
    """pending_sign 위임장에 esign_hash 기록 → active.

    이미 active 또는 revoked 이면 409 반환.
    esign_hash = sha256(json_blob + signed_at).
    """
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT json_blob, status FROM mandates WHERE mandate_id = ?",
            (mandate_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(404, f"위임장 없음: {mandate_id}")
        if row["status"] in ("active", "revoked"):
            raise HTTPException(409, f"이미 {row['status']} 상태, 재서명 불가")

        signed_at = datetime.now().isoformat(timespec="seconds")
        blob_str = row["json_blob"]
        esign_hash = "sha256:" + hashlib.sha256(
            (blob_str + signed_at).encode("utf-8")
        ).hexdigest()[:16]

        # json_blob 내 esign 필드 갱신
        blob = json.loads(blob_str)
        blob["esign"] = {
            "signed_at": signed_at,
            "method": "biometric_or_pin_mock",
            "esign_hash": esign_hash,
            "reconfirmed_in_language": True,
        }
        new_blob = json.dumps(blob, ensure_ascii=False)

        conn.execute(
            "UPDATE mandates SET status='active', esign_hash=?, json_blob=? "
            "WHERE mandate_id=?",
            (esign_hash, new_blob, mandate_id),
        )
        conn.commit()

        user_id = blob.get("user_id", "")
        mcp_tools.append_audit_log(conn, user_id, "mandate_signed",
                                   {"mandate_id": mandate_id, "esign_hash": esign_hash})
        # 서명 완료 통지 (건별 통지 이력 적재)
        if user_id:
            mcp_tools.notify_user(
                conn, user_id, blob.get("language", "vi"),
                "Ủy quyền đã được ký và kích hoạt.",
                notify_type="system",
                message_ko=f"위임장 [{mandate_id}] 서명 완료, 자동 실행 대기 중.",
                mandate_id=mandate_id,
                revocable=True,
            )

        return {"status": "active", "esign_hash": esign_hash, "signed_at": signed_at}
    finally:
        conn.close()


@app.post("/mandate/{mandate_id}/revoke")
def revoke(mandate_id: str) -> dict:
    conn = get_conn()
    try:
        return mcp_tools.revoke_mandate(conn, mandate_id)
    finally:
        conn.close()


@app.get("/audit/{user_id}")
def audit(user_id: str) -> dict:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT log_id, event_type, payload_json, created_at FROM audit_log "
            "WHERE user_id = ? ORDER BY log_id DESC LIMIT 100", (user_id,),
        ).fetchall()
        return {"logs": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/str-queue")
def str_queue() -> dict:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, tx_id, score, flags, status FROM str_queue ORDER BY id DESC",
        ).fetchall()
        return {"queue": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.post("/salary/deposit")
def salary_deposit(req: SalaryDepositRequest) -> dict:
    """급여 입금 이벤트 기록 → active 위임장 있으면 자동 송금 트리거.

    데모 ② 단계: 급여 감지 → FX +1.82% → 3중 게이트 → 어머니께 자동 송금.
    active 위임장이 없으면 salary_event만 기록하고 remittance: null 반환.
    """
    conn = get_conn()
    try:
        deposited_at = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO salary_events(user_id, amount_krw, deposited_at) VALUES (?,?,?)",
            (req.user_id, req.amount_krw, deposited_at),
        )
        conn.commit()
        salary_event = {
            "user_id": req.user_id,
            "amount_krw": req.amount_krw,
            "deposited_at": deposited_at,
        }
        mcp_tools.append_audit_log(conn, req.user_id, "salary_deposit",
                                   {"amount_krw": req.amount_krw})

        # active 송금 위임장 검색
        mandate_row = conn.execute(
            "SELECT mandate_id, json_blob FROM mandates "
            "WHERE user_id=? AND status='active' AND revoked=0 "
            "AND json_extract(json_blob,'$.mandate_type')='remittance' "
            "ORDER BY mandate_id DESC LIMIT 1",
            (req.user_id,),
        ).fetchone()

        if mandate_row is None:
            return {
                "salary_event": salary_event,
                "remittance": None,
                "note": "active 위임장 없음, 자동 송금 미실행",
            }

        mandate_id = mandate_row["mandate_id"]
        blob = json.loads(mandate_row["json_blob"])

        # 화이트리스트 첫 번째 수취인으로 자동 집행 시도
        whitelist = blob.get("beneficiary_whitelist", [])
        if not whitelist:
            return {
                "salary_event": salary_event,
                "remittance": None,
                "note": "위임장에 수취인 없음",
            }
        bnf_id = whitelist[0]["bnf_id"]
        limit_per_tx = blob["limits"]["limit_per_tx_krw"]

        outcome = orchestrator.run_remittance(
            conn,
            mandate_id=mandate_id,
            bnf_id=bnf_id,
            amount_krw=limit_per_tx,
        )

        remittance_resp = {
            "status": outcome.status,
            "message_ko": outcome.message_ko,
            "message_local": outcome.message_local,
            "tx_id": outcome.tx_id,
            "gates": [
                {"gate": t.gate, "label": t.label, "passed": t.passed, "detail": t.detail}
                for t in outcome.traces
            ],
        }
        return {"salary_event": salary_event, "remittance": remittance_resp}
    finally:
        conn.close()


@app.get("/notifications/{user_id}")
def notifications(user_id: str) -> dict:
    """건별 통지 이력, 전금법 요건 ② (건별 통지). 최신순."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, type, message_ko, message_local, tx_id, mandate_id, "
            "revocable, created_at FROM notifications "
            "WHERE user_id=? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return {"notifications": [dict(r) for r in rows]}
    finally:
        conn.close()
