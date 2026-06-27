import * as D from "../demoData.js";
import {
  amlOf, flagKo, fmtAPR, fmtKRW, fmtNum, fmtPct, fmtVND, fxOf, gateCell,
  GATE_NAME, statusMeta,
} from "../format.js";

// ── 공용 조각 ─────────────────────────────────────────────────
function Bi({ vi, ko }) {
  return (
    <div>
      <div className="vi">{vi}</div>
      {ko && <div className="ko">{ko}</div>}
    </div>
  );
}

function GatePills({ outcome }) {
  return (
    <div className="gates">
      {["A", "B", "C"].map((g) => {
        const c = gateCell(outcome, g);
        return (
          <span key={g} className={`gate-pill ${c.cls}`}>
            Gate {g} {GATE_NAME[g]} · {c.text}
          </span>
        );
      })}
    </div>
  );
}

function FlagChips({ flags }) {
  if (!flags?.length) return null;
  return (
    <div className="flags">
      {flags.map((f) => <span key={f} className="flag-chip">{flagKo(f)}</span>)}
    </div>
  );
}

// ── ① 위임장 카드 ────────────────────────────────────────────
function MandateCard({ item, actions }) {
  return (
    <div className="card">
      <div className="card-head navy">
        Giấy ủy quyền chuyển tiền
        <span className="sub">송금 위임장 (전자서명·건별통지·철회권)</span>
      </div>
      <div className="card-body">
        <div className="kv">
          <div className="k">Người nhận<br />수취인</div>
          <div className="v">{D.MOTHER.nameVi} (Mẹ / 어머니)<br />
            <span className="ko">{D.MOTHER.bank} {D.MOTHER.masked}</span></div>
        </div>
        <div className="kv">
          <div className="k">Hạn mức<br />한도</div>
          <div className="v">2.000.000 KRW / lần · 1 lần / tháng
            <div className="ko">1회 200만원 · 월 200만원 (1회/월)</div></div>
        </div>
        <div className="kv">
          <div className="k">Điều kiện tỷ giá<br />환율 조건</div>
          <div className="v">Tốt hơn ≥ 1% so với trung bình 7 ngày
            <div className="ko">7일평균 대비 ≥1% 유리할 때만 실행</div></div>
        </div>
        <div className="kv">
          <div className="k">Kích hoạt<br />트리거</div>
          <div className="v">Khi nhận lương
            <div className="ko">급여 입금 감지 시</div></div>
        </div>
        <div className="kv">
          <div className="k">Quyền hủy<br />철회권</div>
          <div className="v">Hủy bất cứ lúc nào, vô điều kiện
            <div className="ko">언제든 무조건 철회 가능</div></div>
        </div>
        <div className="divider" />
        <div className="note">
          Mỗi giao dịch đều được thông báo bằng tiếng Việt. ·
          모든 실행은 건별로 베트남어 통지됩니다. (전금법 거래지시 3요건 모의)
        </div>
        {item.signed ? (
          <span className="done-chip">Đã ký · 서명 완료</span>
        ) : (
          <button className="btn btn-primary" disabled={item.signing}
            onClick={() => actions.sign(item.id)}>
            {item.signing ? "Đang ký…" : "Xác nhận & Ký"}
            <span className="ko-btn">재확인 후 서명</span>
          </button>
        )}
      </div>
    </div>
  );
}

// ── 서명 완료 카드 ───────────────────────────────────────────
function SignedCard({ item }) {
  return (
    <div className="card">
      <div className="card-head ok">
        Đã ký điện tử <span className="sub">전자서명 완료</span>
      </div>
      <div className="card-body">
        <div className="kv">
          <div className="k">Mã ủy quyền<br />위임장 ID</div>
          <div className="v"><span className="mono">{item.mandateId}</span></div>
        </div>
        <div className="kv">
          <div className="k">Chữ ký điện tử<br />전자서명</div>
          <div className="v"><span className="mono">{item.hash}</span></div>
        </div>
        <div className="note">
          Xác nhận lại bằng tiếng Việt hoàn tất. "Không đọc được thì không ký" ·
          모국어 재확인을 마쳤습니다. 읽을 수 있는 언어로 확인한 뒤에만 서명합니다.
        </div>
      </div>
    </div>
  );
}

// ── ② 급여 감지 카드 ─────────────────────────────────────────
function SalaryCard({ item }) {
  return (
    <div className="card">
      <div className="card-head navy">
        Phát hiện lương về <span className="sub">급여 입금 감지</span>
      </div>
      <div className="card-body">
        <div>
          <div className="amount-big">+{fmtNum(item.amountKrw)} KRW</div>
          <div className="amount-sub">Lương tháng này · 이번 달 급여</div>
        </div>
        <div className="note">
          Kích hoạt ủy quyền, đang kiểm tra điều kiện tỷ giá… ·
          위임 트리거 발동, 환율 조건(7일 평균 대비 1% 이상) 확인 중
        </div>
      </div>
    </div>
  );
}

// ── 송금 판정 결과 카드 (executed / held / str_hold / blocked / rejected) ──
function OutcomeCard({ item, actions, mandate }) {
  const o = item.outcome;
  const meta = statusMeta(o.status);
  const { score, flags } = amlOf(o);
  const fx = fxOf(o);
  const vnd = fx.rateNow ? item.amountKrw * fx.rateNow : item.amountKrw * D.FX_SEED.now;

  if (o.status === "executed") {
    return (
      <div className="card card-auto">
        <div className="card-head ok">
          Đã chuyển tiền tự động <span className="sub">자동 송금 실행 (고객 개입 없음)</span>
        </div>
        <div className="card-body">
          <div>
            <div className="amount-big">{fmtNum(item.amountKrw)} KRW</div>
            <div className="amount-sub">≈ {fmtVND(vnd)} → {item.bnfLabel}</div>
          </div>
          <div className="apr-compare">
            <span className="apr-chip new">
              Tỷ giá {fmtPct(fx.advantagePct ?? D.FX_SEED.advantagePct)} so TB 7 ngày
            </span>
            <span className="ko">7일평균 {fx.rateMa ?? D.FX_SEED.ma} → 현재 {fx.rateNow ?? D.FX_SEED.now}</span>
          </div>
          <GatePills outcome={o} />
          <Bi vi={o.message_local} ko={o.message_ko} />
          {o.tx_id && (
            <div className="note">TX <span className="mono">{o.tx_id}</span> · 한패스 레일(모의) · 건별 통지 완료</div>
          )}
          <div className="divider" />
          {mandate.status === "active" ? (
            <>
              <button className="btn btn-danger-ghost" onClick={() => actions.revoke()}>
                Hủy ủy quyền
                <span className="ko-btn">위임 철회 (무조건, 즉시 처리)</span>
              </button>
            </>
          ) : (
            <div className="note">Ủy quyền đã hủy · 위임이 철회된 상태입니다.</div>
          )}
        </div>
      </div>
    );
  }

  if (o.status === "held" || o.status === "str_hold") {
    return (
      <div className="card">
        <div className="card-head hold">
          Tạm giữ giao dịch <span className="sub">송금 보류 (의심 탐지가 자동 실행에 우선)</span>
        </div>
        <div className="card-body">
          <div>
            <div className="amount-big">{fmtNum(item.amountKrw)} KRW</div>
            <div className="amount-sub">{item.bnfLabel}</div>
          </div>
          <div className="row" style={{ gap: 8, alignItems: "center" }}>
            {score != null && <span className="score-badge hold">AML score {score}</span>}
            <FlagChips flags={flags} />
          </div>
          <Bi
            vi="Đây có đúng là người bạn muốn gửi không?"
            ko="정말 보내려는 분이 맞습니까?"
          />
          <Bi vi={o.message_local} ko={o.message_ko} />
          {o.status === "str_hold" && (
            <div className="note warn">
              Đã đưa vào hàng đợi STR để JB xem xét. · STR 후보 대기열에 등록되어 JB 담당자의 검토를 기다립니다.
            </div>
          )}
          <GatePills outcome={o} />
          {!item.answered ? (
            <div className="btn-row">
              <button className="btn btn-ghost" onClick={() => actions.holdAnswer(item.id, false)}>
                Không, dừng lại
                <span className="ko-btn">아니요, 중단합니다</span>
              </button>
              <button className="btn btn-ghost" onClick={() => actions.holdAnswer(item.id, true)}>
                Đúng, xác nhận
                <span className="ko-btn">네, 맞습니다</span>
              </button>
            </div>
          ) : (
            <span className="done-chip">Đã trả lời · 응답 완료</span>
          )}
        </div>
      </div>
    );
  }

  if (o.status === "blocked") {
    return (
      <div className="card">
        <div className="card-head block">
          Đã chặn giao dịch <span className="sub">송금 차단</span>
        </div>
        <div className="card-body">
          <div>
            <div className="amount-big">{fmtNum(item.amountKrw)} KRW</div>
            <div className="amount-sub">{item.bnfLabel}</div>
          </div>
          <div className="row" style={{ gap: 8, alignItems: "center" }}>
            <span className="score-badge block">블랙리스트 즉시 차단</span>
            <FlagChips flags={flags} />
          </div>
          <Bi
            vi="Đừng bao giờ đưa mật khẩu / OTP cho bất kỳ ai."
            ko="비밀번호·OTP를 절대 알려주지 마세요."
          />
          <Bi vi={o.message_local} ko={o.message_ko} />
          <GatePills outcome={o} />
          <div className="note warn">
            Yêu cầu OTP / giấy tờ / tiền cọc là lừa đảo. ·
            OTP, 신분증, 선입금을 요구하는 거래는 사기 패턴으로 판정되어 즉시 차단되었습니다.
          </div>
        </div>
      </div>
    );
  }

  // rejected 등
  return (
    <div className="card">
      <div className="card-head gray">
        Không thực hiện <span className="sub">실행 안 함 ({meta.ko})</span>
      </div>
      <div className="card-body">
        <div className="amount-sub">{item.bnfLabel} · {fmtKRW(item.amountKrw)}</div>
        <Bi vi={o.message_local} ko={o.message_ko} />
        <GatePills outcome={o} />
      </div>
    </div>
  );
}

// ── 위임 철회 완료 카드 ─────────────────────────────────────
function RevokedCard({ item }) {
  return (
    <div className="card">
      <div className="card-head gray">
        Đã hủy ủy quyền <span className="sub">위임 철회 완료</span>
      </div>
      <div className="card-body">
        <Bi
          vi="Mọi lệnh tự động dừng ngay lập tức. Không cần lý do, không mất phí."
          ko="모든 자동 실행이 즉시 중지되었습니다. 사유·수수료 없는 무조건 철회권입니다."
        />
        <div className="note">위임장 <span className="mono">{item.mandateId}</span> 철회 처리 완료</div>
      </div>
    </div>
  );
}

// ── ⑤ 대환 제안 카드, 금소법: 절약액과 불이익을 같은 크기·같은 굵기로 ──
function RefiCard({ item, actions }) {
  const o = item.offer;
  if (!o.eligible) {
    return (
      <div className="card">
        <div className="card-head gray">
          Chưa đủ điều kiện <span className="sub">가심사 부적격</span>
        </div>
        <div className="card-body">
          {(o.reasons || []).map((r) => <div key={r} className="note">{r}</div>)}
        </div>
      </div>
    );
  }
  return (
    <div className="card">
      <div className="card-head ok">
        Đề xuất chuyển nợ sang JB <span className="sub">JB 대환대출 안내 (가심사)</span>
      </div>
      <div className="card-body">
        <div className="apr-compare">
          <span className="apr-chip old">{o.lender} 연 {(o.current_apr * 100).toFixed(1)}%</span>
          <span className="apr-arrow">→</span>
          <span className="apr-chip new">{o.jb_product} 연 {(o.jb_apr * 100).toFixed(2)}%</span>
        </div>

        {/* 4항목 동일 비중 고지, 절약액만 크게 쓰지 않는다 (금소법 설명의무 모의) */}
        <div className="equal-grid">
          <div className="equal-cell">
            <div className="lbl">Tiết kiệm / năm · 연 절약액</div>
            <div className="val">{fmtKRW(o.annual_saving_krw)}</div>
          </div>
          <div className="equal-cell">
            <div className="lbl">Trả góp hàng tháng mới · 새 월상환액</div>
            <div className="val">{fmtKRW(o.new_monthly_krw)}</div>
          </div>
          <div className="equal-cell">
            <div className="lbl">Tổng phải trả ({o.term_months} tháng) · 총상환액</div>
            <div className="val">{fmtKRW(o.new_total_krw)}</div>
          </div>
          <div className="equal-cell">
            <div className="lbl">Lãi phạt quá hạn · 연체가산금리</div>
            <div className="val">{fmtAPR(o.late_fee_apr)}</div>
          </div>
        </div>

        <div className="note">
          Nếu trả chậm, lãi phạt sẽ được cộng thêm và ảnh hưởng tín dụng. ·
          연체 시 가산금리 적용·신용점수 하락 등 불이익이 있습니다. ({o.grade} · {o.decision})
        </div>

        {item.applied ? (
          <span className="done-chip">Đã nộp đơn · 신청 접수됨</span>
        ) : (
          <button className="btn btn-primary" disabled={item.applying}
            onClick={() => actions.refer(item.id, o)}>
            {item.applying ? "Đang nộp…" : "Nộp đơn cho JB"}
            <span className="ko-btn">JB에 신청</span>
          </button>
        )}
        <div className="note">
          Đây không phải là phê duyệt. Phê duyệt cuối cùng thuộc hệ thống thẩm định JB. ·
          본 화면은 가심사 안내이며, <b>최종 승인은 전북은행 심사엔진의 배타적 권한</b>입니다.
        </div>
      </div>
    </div>
  );
}

// ── 접수 완료 카드 ───────────────────────────────────────────
function ReceiptCard({ item }) {
  return (
    <div className="card">
      <div className="card-head navy">
        Đã nộp hồ sơ cho JB <span className="sub">JB 심사엔진 접수 완료</span>
      </div>
      <div className="card-body">
        <div className="kv">
          <div className="k">Số biên nhận<br />접수번호</div>
          <div className="v"><span className="mono">{item.receiptNo}</span></div>
        </div>
        <div className="kv">
          <div className="k">Trạng thái<br />상태</div>
          <div className="v"><span className="mono">{item.status}</span></div>
        </div>
        <div className="note">
          Kết quả sẽ được thông báo bằng tiếng Việt. ·
          심사 결과는 베트남어로 통지됩니다. 최종 승인은 JB 심사엔진 권한입니다.
        </div>
      </div>
    </div>
  );
}

// ── 백엔드 푸시 알림(제네릭) / 에러 카드 ─────────────────────
function NotifCard({ item }) {
  const n = item.notif || {};
  const vi = n.message_local || n.message_vi || n.message || "";
  const ko = n.message_ko || "";
  return (
    <div className="card">
      <div className="card-head navy">
        Thông báo <span className="sub">알림</span>
      </div>
      <div className="card-body">
        <Bi vi={vi || "(thông báo mới)"} ko={ko} />
      </div>
    </div>
  );
}

function ErrorCard({ item }) {
  return (
    <div className="card">
      <div className="card-head gray">
        Mất kết nối tạm thời <span className="sub">일시 연결 오류</span>
      </div>
      <div className="card-body">
        <Bi
          vi="Không thể kết nối máy chủ demo. Thử lại sau giây lát nhé."
          ko={`데모 서버 연결 실패. ${item.message || "잠시 후 다시 시도해 주세요."}`}
        />
      </div>
    </div>
  );
}

// ── 피드 디스패처 ────────────────────────────────────────────
export default function FeedItem({ item, actions, mandate }) {
  switch (item.kind) {
    case "user":
      return (
        <div className="row right">
          <div className="bubble user"><div className="vi">{item.text}</div></div>
        </div>
      );
    case "bot":
      return (
        <div className="row">
          <div className="bubble bot"><Bi vi={item.vi} ko={item.ko} /></div>
        </div>
      );
    case "mandate": return <MandateCard item={item} actions={actions} />;
    case "signed": return <SignedCard item={item} />;
    case "salary": return <SalaryCard item={item} />;
    case "outcome": return <OutcomeCard item={item} actions={actions} mandate={mandate} />;
    case "revoked": return <RevokedCard item={item} />;
    case "refi": return <RefiCard item={item} actions={actions} />;
    case "receipt": return <ReceiptCard item={item} />;
    case "notif": return <NotifCard item={item} />;
    case "error": return <ErrorCard item={item} />;
    default: return null;
  }
}
