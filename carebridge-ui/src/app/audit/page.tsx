"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { analyzeRejection, analyzeRejectionFromFile } from "../lib/api";
import { AuditReport } from "../types/audit";
import HelpSupport from "../components/audit/Helpsupport";

/* ─────────────────────────────────────────────────────────────────
   COLOUR CONFIGS
───────────────────────────────────────────────────────────────── */
const APPEAL_CFG: Record<string, { color: string; bg: string; border: string; track: string }> = {
  "Strong":   { color: "#1e5c2e", bg: "#d6eddc", border: "#9dd0aa", track: "#c8e4ce" },
  "Moderate": { color: "#7a4e08", bg: "#faecd0", border: "#e0b870", track: "#ead4a0" },
  "Weak":     { color: "#8c1f14", bg: "#f5d0cc", border: "#e08070", track: "#e8b8b0" },
};

const ALIGN_CFG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  "Strong":       { color: "#8c1f14", bg: "#f5d0cc", border: "#e08070", label: "Strongly aligned — insurer's position is well-grounded" },
  "Partial":      { color: "#7a4e08", bg: "#faecd0", border: "#e0b870", label: "Partially aligned — grounds for appeal may exist" },
  "Weak":         { color: "#1e5c2e", bg: "#d6eddc", border: "#9dd0aa", label: "Weakly aligned — potential misapplication detected" },
  "Not Detected": { color: "#1e5c2e", bg: "#d6eddc", border: "#9dd0aa", label: "No clause identified — insurer's position may lack basis" },
};

/* ─────────────────────────────────────────────────────────────────
   REPORT CHAT
───────────────────────────────────────────────────────────────── */
interface ChatMsg { role: "user" | "assistant"; content: string; sources?: string[] }

function buildLocalAnswer(question: string, r: AuditReport): string {
  const q   = question.toLowerCase();
  const pct = r.appeal_strength.percentage;
  const lbl = r.appeal_strength.label;

  if (q.includes("direction") || q.includes("strong") || q.includes("appeal case") || q.includes("how strong") || q.includes("chance")) {
    return `The appeal direction is rated ${lbl} at ${pct}%. ${r.appeal_strength.reasoning} ${
      pct >= 70 ? "This is a favourable direction — consider challenging the rejection formally."
      : pct >= 40 ? "There are grounds worth pursuing — address the documentation gaps first."
      : "The insurer's position appears well-grounded. Focus on the IRDAI moratorium if the policy is 8+ years old."
    } This is a directional indicator only — not a legal prediction.`;
  }
  if (q.includes("overturn") || q.includes("evidence") || q.includes("what could") || q.includes("strengthen") || q.includes("reverse")) {
    const weak = r.weak_points?.slice(0, 2).join("; ") || "documentation gaps";
    return `To strengthen your case: address ${weak}. Obtain a physician's letter confirming the exact diagnosis date, gather all records showing when the condition first manifested, and compare the rejection clause wording against IRDAI's standardised definitions. If the policy is 8+ years old, invoke the IRDAI moratorium — pre-existing exclusions cannot apply after that point.`;
  }
  if (q.includes("moratorium") || q.includes("8 year")) {
    return "The IRDAI 8-year moratorium: after 8 continuous years on any health policy, the insurer cannot reject citing pre-existing disease — even if not disclosed at inception. If your policy (or ported predecessor) is 8+ years old, this is your strongest regulatory argument.";
  }
  if (q.includes("weak") || q.includes("why is") || q.includes("why appeal")) {
    const pts = r.weak_points?.join("; ") || r.appeal_strength.reasoning;
    return `The direction is rated ${lbl} because: ${pts}. The clause alignment is ${r.clause_alignment.toLowerCase()} — ${ALIGN_CFG[r.clause_alignment]?.label || "review the clause carefully"}.`;
  }
  if (q.includes("next step") || q.includes("what should") || q.includes("what do i do")) {
    const steps = r.reapplication_steps?.slice(0, 3);
    if (steps?.length) return `${steps.map((s, i) => `${i + 1}. ${s}`).join(" ")} If unresolved in 15 days, escalate to IRDAI IGMS. The Ombudsman handles claims up to ₹50 lakhs free of charge.`;
    return "1. File a written complaint with the insurer's GRO. 2. Escalate to IRDAI IGMS (igms.irda.gov.in) if no response in 15 days. 3. File before the Insurance Ombudsman within 1 year of the final reply.";
  }
  if (q.includes("ombudsman") || q.includes("escalat") || q.includes("igms")) {
    return "File with IRDAI IGMS first. If unresolved in 30 days, approach the Insurance Ombudsman (cioins.co.in). Eligibility: claims up to ₹50 lakhs, within 1 year of the insurer's final reply. Free and binding.";
  }
  if (q.includes("document") || q.includes("what do i need")) {
    return "For appeal: (1) full policy document with schedule, (2) original rejection letter, (3) all medical records submitted with the claim, (4) hospital discharge summary and bills, (5) doctor's certificate with exact diagnosis date, (6) all prior insurer correspondence.";
  }
  if (q.includes("clause") || q.includes("exclusion")) {
    return `Clause invoked: "${r.policy_clause_detected}". Rejection basis: "${r.why_rejected}". Alignment: ${r.clause_alignment} — ${ALIGN_CFG[r.clause_alignment]?.label || "review carefully"}.`;
  }
  return `Rejection: "${r.why_rejected}". Clause: "${r.policy_clause_detected}" (${r.clause_alignment.toLowerCase()} alignment). Direction: ${lbl} (${pct}%). ${r.appeal_strength.reasoning}`;
}

function extractCitations(text: string): string[] {
  const refs: string[] = [];
  if (/moratorium/i.test(text))     refs.push("IRDAI 8-Year Moratorium Rule");
  if (/IRDAI|irdai/i.test(text))    refs.push("IRDAI Policyholders' Regulations 2017");
  if (/[Oo]mbudsman/i.test(text))   refs.push("Insurance Ombudsman Rules 2017");
  if (/waiting period/i.test(text)) refs.push("IRDAI Waiting Period Regs");
  return refs.slice(0, 2);
}

function ReportChat({ report }: { report: AuditReport }) {
  const [open,    setOpen]    = useState(false);
  const [msgs,    setMsgs]    = useState<ChatMsg[]>([]);
  const [input,   setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const [sessId,  setSessId]  = useState<string | null>(null);
  const sessRef   = useRef<string | null>(null);
  const inputRef  = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, loading]);

  // Session on mount — not on click — eliminates the race condition where
  // sessRef.current is still null when the first message fires
  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
        if (!apiBase) return;
        const res = await fetch(`${apiBase}/chat-session`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ report_data: report }),
        });
        if (!cancelled && res.ok) {
          const d = await res.json();
          setSessId(d.session_id);
          sessRef.current = d.session_id;
        }
      } catch { /* backend unavailable — local fallback will be used */ }
    }
    init();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const STARTERS = [
    "What does this appeal direction mean?",
    "What evidence could strengthen my case?",
    "What are my next steps?",
    "When should I approach the Ombudsman?",
  ];

  // send() always receives the text as an argument — never reads from React
  // state directly, which would be stale inside the useCallback closure.
  // Both Enter and the Send button pass inputRef.current?.value.
  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setMsgs(prev => [...prev, { role: "user", content: trimmed }]);
    // Clear both state and DOM value immediately so the input feels responsive
    setInput("");
    if (inputRef.current) inputRef.current.value = "";
    setLoading(true);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
      let answer = "";
      let sources: string[] = [];

      if (apiBase) {
        try {
          const sid      = sessRef.current;
          const endpoint = sid ? "/chat" : "/report-chat";
          const payload  = sid
            ? { session_id: sid, question: trimmed }
            : { report_data: report, question: trimmed, context: "audit" };

          const res = await fetch(`${apiBase}${endpoint}`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (res.ok) {
            const d = await res.json();
            if (d.answer && d.answer.length > 15) {
              answer  = d.answer;
              sources = d.sources ?? [];
            }
          }
        } catch { /* fall through to local answer */ }
      }

      if (!answer) {
        answer  = buildLocalAnswer(trimmed, report);
        sources = extractCitations(answer);
      }

      setMsgs(prev => [...prev, { role: "assistant", content: answer, sources }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [loading, report]);

  // Both Enter key and Send button always read from the DOM ref — never stale state
  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(inputRef.current?.value ?? "");
    }
  };
  const handleSendClick = () => send(inputRef.current?.value ?? input);

  return (
    <div className="chat-wrap">
      {!open ? (
        <button className="chat-trigger"
          onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 80); }}>
          <span className="ct-icon">◈</span>
          Ask about this report
          <span className="ct-badge">AI Chat</span>
        </button>
      ) : (
        <div className="chat-panel">
          <div className="chat-hdr">
            <div>
              <div className="chat-hdr-title">Report Assistant</div>
              <div className="chat-hdr-sub">Grounded in your audit data</div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div className="chat-dot"
                title={sessId ? "Session active" : "One-shot mode"}
                style={{ background: sessId ? "#4a9d5f" : "#e0b060" }} />
              <button className="chat-close" onClick={() => setOpen(false)}>×</button>
            </div>
          </div>

          {msgs.length === 0 && (
            <div className="chat-starters">
              <div className="starters-label">Suggested questions</div>
              {STARTERS.map((q, i) => (
                <button key={i} className="starter-btn"
                  onClick={() => send(q)} disabled={loading}>{q}</button>
              ))}
            </div>
          )}

          <div className="chat-msgs">
            {msgs.length === 0 ? (
              <div className="chat-empty">
                <div className="chat-empty-icon">◈</div>
                <div>Ask anything about your audit</div>
                <div className="chat-empty-sub">clauses · evidence · direction · next steps</div>
              </div>
            ) : msgs.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="msg-meta">{m.role === "user" ? "You" : "CareBridge AI"}</div>
                <div className="msg-bubble">{m.content}</div>
                {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                  <div className="msg-sources">
                    {m.sources.map((s, j) => <span key={j} className="msg-chip">{s}</span>)}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="typing-row">
                <div className="typing-meta">Thinking</div>
                <div className="typing"><span /><span /><span /></div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row">
            <input
              ref={inputRef}
              className="chat-input"
              placeholder={loading ? "Thinking..." : "Ask about clauses, steps, evidence..."}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
              autoComplete="off"
            />
            <button className="chat-send"
              onClick={handleSendClick}
              disabled={loading || !input.trim()}>↑</button>
          </div>
          <div className="chat-hint">Enter to send · not legal advice</div>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────
   DEEP ANALYSIS — 4 accordion sections
───────────────────────────────────────────────────────────────── */
function DeepAnalysis({ report }: { report: AuditReport }) {
  const [openIdx, setOpenIdx] = useState<number>(0);

  const sections = [
    { icon: "§",  iconBg: "#d6eddc", iconCol: "#1e5c2e", label: "Clause-Specific Reasoning",              body: <ClauseReasoning report={report} /> },
    { icon: "⊞",  iconBg: "#dce4f5", iconCol: "#2d3a7a", label: "Regulatory Evidence References",         body: <EvidenceRefs    report={report} /> },
    { icon: "▲",  iconBg: "#f5d0cc", iconCol: "#8c1f14", label: `Why the Direction Is ${report.appeal_strength.label}`, body: <WhyDirection report={report} /> },
    { icon: "◆",  iconBg: "#d6eddc", iconCol: "#1e5c2e", label: "Evidence That Could Strengthen Your Case", body: <WhatOverturn  report={report} /> },
  ];

  return (
    <div className="deep-wrap">
      {sections.map((s, i) => (
        <div key={i} className={`deep-section${openIdx === i ? " open" : ""}`}>
          <button className="deep-hdr" onClick={() => setOpenIdx(openIdx === i ? -1 : i)}>
            <div className="deep-icon" style={{ background: s.iconBg, color: s.iconCol }}>{s.icon}</div>
            <span className="deep-label">{s.label}</span>
            <span className={`deep-chevron${openIdx === i ? " open" : ""}`}>›</span>
          </button>
          {openIdx === i && <div className="deep-body">{s.body}</div>}
        </div>
      ))}
    </div>
  );
}

function ClauseReasoning({ report: r }: { report: AuditReport }) {
  const paras: string[] = [];
  if (r.policy_clause_detected && r.policy_clause_detected !== "Not detected") {
    paras.push(`The insurer invoked: "${r.policy_clause_detected}". This is ${r.clause_alignment.toLowerCase()} aligned — ${ALIGN_CFG[r.clause_alignment]?.label || "review carefully"}.`);
  } else {
    paras.push(`No specific clause was cited. Under IRDAI Regulation 9(5), insurers must provide specific reasons with clause references — this absence is itself a procedural weakness you can challenge.`);
  }
  if (r.why_rejected) paras.push(`Stated basis: "${r.why_rejected}". ${getClauseContext(r.why_rejected)}`);
  if (r.case_summary) paras.push(r.case_summary);
  return (
    <div className="reasoning-block">
      {paras.map((p, i) => <p key={i}>{p}</p>)}
    </div>
  );
}

function EvidenceRefs({ report: r }: { report: AuditReport }) {
  return (
    <div className="list-stack">
      {buildEvidenceRefs(r).map((ref, i) => (
        <div key={i} className="ev-item">
          <span className="ev-num">{String(i + 1).padStart(2, "0")}</span>
          <span className="ev-text">{ref}</span>
        </div>
      ))}
    </div>
  );
}

function WhyDirection({ report: r }: { report: AuditReport }) {
  return (
    <div className="list-stack">
      {buildWhyDirection(r).map((item, i) => (
        <div key={i} className="wk-item">
          <span className="wk-icon">▲</span>
          <span className="wk-text">{item}</span>
        </div>
      ))}
    </div>
  );
}

function WhatOverturn({ report: r }: { report: AuditReport }) {
  return (
    <div className="list-stack">
      {buildOverturnList(r).map((item, i) => (
        <div key={i} className="ov-item">
          <span className="ov-icon">◆</span>
          <span className="ov-text">{item}</span>
        </div>
      ))}
    </div>
  );
}

function getClauseContext(reason: string): string {
  const r = reason.toLowerCase();
  if (r.includes("pre-existing") || r.includes("ped"))
    return "IRDAI limits pre-existing exclusions to 48 months. After the 8-year moratorium, no claim can be repudiated for non-disclosure.";
  if (r.includes("waiting period"))
    return "Waiting periods must be clearly disclosed in the Key Features Document. Undisclosed or ambiguous wording violates IRDAI disclosure obligations.";
  if (r.includes("non-disclosure") || r.includes("fraud"))
    return "Non-disclosure grounds require the insurer to prove materiality. After 3 years, non-disclosure claims are time-barred unless deliberate fraud is proven.";
  if (r.includes("exclusion"))
    return "IRDAI's standardisation circular limits which conditions can be permanently excluded. Verify this exclusion is on the permitted list.";
  return "Verify the exact policy wording against IRDAI model clauses to confirm this interpretation is correct.";
}

function buildEvidenceRefs(r: AuditReport): string[] {
  const refs: string[] = [];
  refs.push(`IRDAI Reg 9(5): Insurer must cite the specific policy clause. ${
    r.policy_clause_detected === "Not detected"
      ? "Appears unmet in your case — a direct procedural challenge."
      : "Verify the cited clause matches your policy document exactly."
  }`);
  const reason = (r.why_rejected || "").toLowerCase();
  if (reason.includes("pre-existing") || reason.includes("ped"))
    refs.push("IRDAI Health Insurance Regs 2016: Pre-existing condition must have been diagnosed/treated within 48 months prior to policy commencement. After 8 years of continuous coverage, no claim can be rejected for non-disclosure.");
  if (reason.includes("waiting"))
    refs.push("IRDAI Circular on Waiting Periods: Disease-specific waiting periods must be listed explicitly. If your condition isn't on the disease-specific list, only the general 30-day period applies.");
  if (reason.includes("non-disclosure") || reason.includes("fraud"))
    refs.push("IRDAI Moratorium: For non-disclosure, insurer bears burden of proving fraud. After 3 years of continuous policy, non-disclosure claims are barred unless deliberate fraud is evidenced.");
  refs.push("Ombudsman Rules 2017, Rule 13: If unresolved in 15 days, file before the Ombudsman. Free process, binding awards up to ₹50 lakhs, within 1 year of final rejection.");
  if (r.strong_points?.length > 0)
    refs.push(`Your case has ${r.strong_points.length} identified strong points: ${r.strong_points.slice(0, 2).join("; ")}. Lead with these in your written appeal.`);
  return refs;
}

function buildWhyDirection(r: AuditReport): string[] {
  const items: string[] = [];
  items.push(`Direction rated ${r.appeal_strength.label} at ${r.appeal_strength.percentage}%: ${r.appeal_strength.reasoning}`);
  if (r.weak_points?.length > 0) r.weak_points.forEach(p => items.push(p));
  if (r.clause_alignment === "Strong")
    items.push(`"${r.policy_clause_detected}" is strongly aligned with policy terms. Overturning requires demonstrating procedural errors or that the clause violates IRDAI regulations.`);
  if (r.clause_alignment === "Partial")
    items.push("Partially aligned — gaps exist in how the clause was applied. Focus the appeal on specific misapplications or where the factual basis is unclear.");
  if (!r.reapplication_possible)
    items.push("Reapplication unlikely with current documentation. This changes if you gather specialist opinions that directly contradict the rejection's factual basis.");
  return items;
}

function buildOverturnList(r: AuditReport): string[] {
  const items: string[] = [];
  const reason = (r.why_rejected || "").toLowerCase();
  if (reason.includes("pre-existing") || reason.includes("ped")) {
    items.push("Physician's letter stating the diagnosis date and confirming the condition was not present or known at policy purchase — must cite specific dates of first consultation.");
    items.push("Medical records from before policy start showing no diagnosis, consultation, or treatment for the disputed condition. Directly rebuts the insurer's factual claim.");
    items.push("If policy is 8+ years old: evidence of continuous coverage to invoke the IRDAI moratorium — bars rejection on non-disclosure grounds entirely.");
  } else if (reason.includes("waiting period")) {
    items.push("Proof the condition is acute (sudden onset) not chronic — acute conditions are typically exempt. A specialist letter confirming acute presentation is key.");
    items.push("Exact policy wording showing the applicable waiting period and whether your procedure falls under an exempt category (emergencies and accidents are usually exempt).");
    items.push("Evidence the waiting period had fully elapsed — policy start date vs treatment date calculation.");
  } else if (reason.includes("non-disclosure") || reason.includes("fraud")) {
    items.push("Proof the condition was genuinely unknown at proposal time — a doctor's confirmation it was not diagnosable or symptomatic before the policy start date.");
    items.push("Evidence that proposal form questions were ambiguous, making it objectively unclear whether disclosure was required.");
    items.push("If policy is 3+ years old: invoke the moratorium period under IRDAI regulations.");
  } else {
    items.push("Original policy document with the exclusion clause highlighted — compare exact wording against rejection letter to identify discrepancy.");
    items.push("Independent specialist opinion confirming treatment was medically necessary and within covered scope.");
  }
  items.push("Proof the Key Features Document (KFD) did not clearly disclose this restriction — undisclosed KFD restrictions cannot be enforced under IRDAI regulations.");
  items.push("All prior insurer communications showing any acknowledgement, approval, or inconsistency — particularly any cashless approval later contradicted by rejection.");
  if (r.strong_points?.length > 0)
    items.push(`Lead with your strong points: ${r.strong_points.slice(0, 2).join("; ")} — anchor your appeal letter to the GRO and Ombudsman around these.`);
  return items;
}

/* ─────────────────────────────────────────────────────────────────
   SYNTHETIC SAMPLE TEST CASES (5 real-world patterns)
   Generated from Reddit/forum research — no real data used
───────────────────────────────────────────────────────────────── */
const SAMPLE_CASES = [
  {
    label: "PED + Non-disclosure",
    tag: "Most Common",
    tagColor: "#8c1f14",
    tagBg: "#f5d0cc",
    icon: "🟥",
    policy: `HEALTH INSURANCE POLICY — STANDARD INDIVIDUAL PLAN
Sum Insured: ₹5,00,000 | Policy No: HI/2021/00441
Policyholder: Rajesh Kumar | Inception Date: 12 March 2021

Clause 4.1 — Pre-Existing Diseases (PED):
Any condition, ailment, injury or disease for which the Insured Person had signs, symptoms, was diagnosed or received treatment during the 48 months prior to the first policy issuance date shall be treated as a Pre-Existing Disease and shall not be covered during the waiting period of 48 months from the date of inception.

Clause 4.2 — Duty of Disclosure:
The Proposer is under an obligation to truthfully disclose all material facts at the time of proposal. Failure to disclose, whether deliberate or otherwise, may render this policy voidable at the Company's discretion.`,
    rejection: `Date: 14 February 2025
Claim Reference: CLM/2025/HI/00881
Re: Health Insurance Claim — Rajesh Kumar — Policy No: HI/2021/00441

Dear Mr. Kumar,

We regret to inform you that upon detailed scrutiny of your claim documents submitted on 02 February 2025 pertaining to hospitalisation at Medicity Hospital, New Delhi, we are constrained to repudiate the claim on the following grounds:

1. Based on the medical records and discharge summary submitted, the treating physician has noted a chronic history of Type-2 Diabetes Mellitus spanning approximately 3 years prior to policy inception. This condition is therefore classified as a Pre-Existing Disease under Clause 4.1 of the policy.

2. The said condition was not disclosed at the time of proposal dated 10 March 2021. Material facts were withheld at the time of proposal, rendering the insurer unable to correctly assess the risk at inception.

In view of the above, the claim amounting to ₹1,24,500 is not admissible as per the terms and conditions of the policy.

You may approach our Grievance Redressal Officer within 15 days of receipt of this letter.

Yours sincerely,
Claims Department
HealthGuard Insurance Company Ltd.`,
    medical: `Discharge Summary — Medicity Hospital, New Delhi
Patient: Mr. Rajesh Kumar | Age: 47 | Date of Admission: 28 January 2025
Diagnosis: Diabetic Nephropathy — Stage 3 Chronic Kidney Disease

History of Present Illness:
Patient is a known case of Type-2 Diabetes Mellitus, diagnosed approximately 3–4 years ago and managed on oral hypoglycaemics. No prior hospitalisation on record. Presenting with bilateral pedal edema, fatigue and elevated serum creatinine (3.1 mg/dL).

Treatment: IV fluids, Nephrology consult, started on dialysis support. Discharged after 6 days in stable condition.`,
    explanation: "I purchased this policy in good faith and honestly forgot to mention my diabetes — I thought it was controlled and minor. I had no history of kidney disease before this admission. The doctor confirmed the kidney condition is a new development.",
  },
  {
    label: "Waiting Period — Emergency",
    tag: "Tricky",
    tagColor: "#7a4e08",
    tagBg: "#faecd0",
    icon: "🟧",
    policy: `HEALTH INSURANCE POLICY — FAMILY FLOATER PLAN
Sum Insured: ₹10,00,000 | Policy No: FF/2024/07712
Policyholder: Priya Sharma | Inception Date: 01 November 2024

Clause 3.1 — Initial Waiting Period:
All claims arising within 30 days from the date of commencement of the policy shall not be admissible, except for claims arising due to accidents.

Clause 3.2 — Disease-Specific Waiting Period:
Certain specified diseases including hernia, cataract, joint replacement, and urinary calculi shall have a waiting period of 24 months from the first date of inception.`,
    rejection: `Date: 10 December 2024
Claim Reference: CLM/2024/FF/03341
Re: Cashless Pre-Authorisation Denial — Priya Sharma — Policy No: FF/2024/07712

Dear Ms. Sharma,

This is with reference to your request for pre-authorisation of cashless treatment at Fortis Hospital, Mumbai submitted on 08 December 2024.

We wish to inform you that the claim is not admissible under your current policy as the treatment for cholelithiasis (gallstones) with laparoscopic cholecystectomy has been requested within 30 days of policy commencement on 01 November 2024.

The claim falls within the initial waiting period as stipulated under Clause 3.1 of the policy terms and conditions and is therefore not payable at this stage.

We encourage you to arrange for alternate payment arrangements for the planned procedure.

Yours sincerely,
Pre-Authorisation Desk
Shield Health Insurance`,
    medical: `Consultant Surgeon's Certificate
Patient: Ms. Priya Sharma | Age: 38
Hospital: Fortis Hospital, Mumbai

Diagnosis: Symptomatic Cholelithiasis — acute episode with biliary colic.
Recommendation: Laparoscopic Cholecystectomy (surgical removal of gallbladder) — medically necessary. Patient presenting with acute pain and risk of cholecystitis if surgery delayed. Not an elective procedure in current clinical context.`,
    explanation: "My gallstones were first discovered only 2 months ago — after I bought this policy. The pain became acute and the surgeon says it cannot be delayed. This is not a planned or elective surgery — it is an emergency medical situation.",
  },
  {
    label: "Room Rent + Proportionate Deduction",
    tag: "Partial Rejection",
    tagColor: "#2d3a7a",
    tagBg: "#dce4f5",
    icon: "⚫",
    policy: `HEALTH INSURANCE POLICY — INDIVIDUAL PLAN
Sum Insured: ₹3,00,000 | Policy No: IND/2022/03310
Policyholder: Amit Verma | Inception Date: 5 June 2022

Clause 5.3 — Room Rent Limit:
Room rent (including nursing charges) shall be payable up to 1% of Sum Insured per day (i.e., ₹3,000 per day for a Sum Insured of ₹3,00,000). If room rent exceeds the eligible limit, all associated charges including surgeon fees, OT charges, and ICU charges shall be scaled down proportionately.

The policy shall be liable only to pay that proportion of all such charges which would have been payable had the Insured Person occupied a room within the eligible rent limit.`,
    rejection: `Date: 03 April 2025
Claim Reference: CLM/2025/IND/00934
Re: Partial Claim Settlement — Amit Verma — Policy No: IND/2022/03310

Dear Mr. Verma,

We have processed your claim for hospitalisation at Max Hospital, Delhi from 15 March 2025 to 22 March 2025.

Claim Amount Submitted: ₹1,87,000
Admissible Amount After Deduction: ₹94,500

Reason for Deduction:
You opted for a Private Single AC Room at a rent of ₹7,500 per day, which exceeds your eligible room rent limit of ₹3,000 per day under Clause 5.3 of your policy. As per policy terms, room rent exceeded eligibility, resulting in a proportionate deduction of 60% across all associated hospitalisation charges including surgical fees, anaesthesia, and ICU charges.

The admissible claim of ₹94,500 has been processed for payment.

Yours sincerely,
Claims Processing Team
Star Cover Insurance`,
    medical: `Discharge Summary — Max Hospital, New Delhi
Patient: Mr. Amit Verma | Age: 52
Admission: 15 March 2025 | Discharge: 22 March 2025
Diagnosis: Acute Appendicitis → Laparoscopic Appendectomy (emergency)

Room Type: Private Single AC Room — ₹7,500/day
Surgical Charges: ₹65,000
ICU (1 day post-op): ₹18,000
OT Charges: ₹24,000
Medicine / Consumables: ₹22,000
Total Bill: ₹1,87,000`,
    explanation: "I was admitted as an emergency and the hospital allocated whatever room was available at that time. I was not given a choice of room type during emergency admission. I did not choose a premium room voluntarily.",
  },
  {
    label: "Missing Documents + Delay",
    tag: "Documentation",
    tagColor: "#1e5c2e",
    tagBg: "#d6eddc",
    icon: "🟫",
    policy: `HEALTH INSURANCE POLICY — INDIVIDUAL PLAN
Sum Insured: ₹5,00,000 | Policy No: HI/2020/09981
Policyholder: Sunita Joshi | Inception Date: 22 January 2020

Clause 7.1 — Claim Intimation:
The Company must be intimated of any planned hospitalisation at least 48 hours prior to admission and within 24 hours of any emergency hospitalisation. Failure to intimate within the stipulated time frame may result in rejection of the claim.

Clause 7.2 — Supporting Documents:
The Insured Person shall submit all original documents including but not limited to: Original bills and receipts, discharge summary, investigation reports, doctor's prescription, and indoor case papers within 30 days of discharge.`,
    rejection: `Date: 28 March 2025
Claim Reference: CLM/2025/HI/02218
Re: Claim Repudiation — Sunita Joshi — Policy No: HI/2020/09981

Dear Ms. Joshi,

This letter is in reference to your reimbursement claim of ₹78,500 for hospitalisation at City Hospital, Pune from 14 February 2025 to 19 February 2025.

After review of the documents submitted, we regret to inform you that the claim is hereby repudiated on the following grounds:

1. Delay in Intimation: The hospitalisation was not intimated within 24 hours of emergency admission as required under Clause 7.1. Intimation was received 5 days after admission.

2. Supporting documents were not submitted despite repeated requests sent on 28 February and 12 March 2025. The following documents remain outstanding:
   • Original pharmacy bills (₹12,400)
   • Indoor Case Papers / Nursing Notes
   • Complete investigation reports (MRI report missing)

As the required supporting documentation has not been provided, we are unable to process this claim further. The claim is not payable under the current circumstances.

Yours sincerely,
Claims Department
Blue Cross Insurance`,
    medical: `Discharge Summary — City Hospital, Pune
Patient: Ms. Sunita Joshi | Age: 61
Admission: 14 February 2025 (Emergency) | Discharge: 19 February 2025
Diagnosis: Acute Cerebrovascular Accident (Ischemic Stroke)

Condition at admission: Sudden onset left-sided weakness, slurred speech. Brought to ER by family. Patient unable to communicate at admission.
Treatment: CT Brain (no bleed), thrombolysis, physiotherapy, neurology consult.
Note: Patient's family was in significant distress during admission and managing multiple simultaneous responsibilities.`,
    explanation: "My mother had an emergency stroke. I was alone managing everything with no help. I called the insurance company as soon as I could — I didn't even know about the 24-hour rule. I also couldn't get all the bills immediately because the hospital delayed issuing them.",
  },
  {
    label: "Exclusion + Not Medically Necessary",
    tag: "Combined",
    tagColor: "#4a1a7a",
    tagBg: "#ede4f5",
    icon: "🟪",
    policy: `HEALTH INSURANCE POLICY — INDIVIDUAL PLAN
Sum Insured: ₹7,50,000 | Policy No: IND/2023/11450
Policyholder: Vikram Singh | Inception Date: 1 April 2023

Clause 6.1 — Permanent Exclusions:
The following shall not be covered under this policy under any circumstances:
(a) Cosmetic or aesthetic treatment of any kind unless necessitated by an accident
(b) Dental treatment except requiring hospitalisation for more than 24 hours
(c) Obesity / weight management treatment and related complications
(d) Treatment of alcoholism, drug addiction or any substance abuse

Clause 6.5 — Medically Necessary Treatment:
Only treatment that is medically necessary, i.e., required for the treatment of an illness or injury and could not have been reasonably omitted without adversely affecting the patient's condition, shall be covered. Elective procedures undertaken for convenience or patient preference are excluded.`,
    rejection: `Date: 17 April 2025
Claim Reference: CLM/2025/IND/04450
Re: Cashless Denial — Vikram Singh — Policy No: IND/2023/11450

Dear Mr. Singh,

This is with reference to your pre-authorisation request submitted on 15 April 2025 for septoplasty and functional endoscopic sinus surgery (FESS) at Apollo Hospital, Hyderabad.

After review of the clinical documents provided, we are unable to approve the cashless request on the following grounds:

1. The procedure (septoplasty) partially falls under procedures that are not considered medically necessary as per our policy guidelines, as the severity criteria for surgical intervention per the Lund-Mackay score submitted does not meet our internal threshold.

2. The request includes correction of nasal deviation which could be considered of cosmetic benefit and therefore falls under permanent exclusions of the policy under Clause 6.1(a).

We recommend the treating physician provide additional documentation establishing the functional (not aesthetic) necessity of the procedure for reconsideration.

Yours faithfully,
Medical Review Team
Prime Shield Insurance`,
    medical: `ENT Specialist Report — Apollo Hospital, Hyderabad
Patient: Mr. Vikram Singh | Age: 34
Date: 10 April 2025

Diagnosis: Significant deviated nasal septum (DNS) with bilateral chronic sinusitis.
Symptoms: Severe nasal obstruction (bilateral), recurrent sinusitis episodes (4 in past 12 months), sleep apnoea grade 1, chronic headaches.

Lund-Mackay CT Score: 16/24 — indicates moderate-to-severe sinus disease.
Recommendation: Functional septoplasty + FESS is medically indicated. Not a cosmetic procedure — patient has documented functional impairment confirmed by acoustic rhinometry and sleep study.
Conservative management with nasal steroids and antibiotics has failed over 18 months.`,
    explanation: "My doctor has clearly stated this is a functional surgery needed because I cannot breathe properly and keep getting serious sinus infections. This is NOT cosmetic — it is a medically necessary procedure that I have been putting off for 2 years. Conservative treatments have failed.",
  },
];

/* ─────────────────────────────────────────────────────────────────
   MAIN PAGE
───────────────────────────────────────────────────────────────── */
export default function AuditPage() {
  const [mode, setMode]       = useState<"text" | "upload">("upload");
  const [policyText,      setPolicyText]      = useState("");
  const [rejectionText,   setRejectionText]   = useState("");
  const [medicalText,     setMedicalText]     = useState("");
  const [userExplanation, setUserExplanation] = useState("");
  
  const [policyFile,      setPolicyFile]      = useState<File | null>(null);
  const [rejectionFile,   setRejectionFile]   = useState<File | null>(null);
  const [medicalFile,     setMedicalFile]     = useState<File | null>(null);

  const [activeField,     setActiveField]     = useState<string | null>(null);
  const [report,  setReport]  = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (mode === "text") {
        if (!policyText.trim() || !rejectionText.trim()) {
          setError("Policy wording and rejection letter are required in text mode."); return;
        }
    } else {
        if (!policyFile || !rejectionFile) {
          setError("Policy PDF and Rejection Letter are required in upload mode."); return;
        }
    }
    setLoading(true); setError(null); setReport(null);
    try {
      let data;
      if (mode === "text") {
          data = await analyzeRejection({
            policy_text:            policyText,
            rejection_text:         rejectionText,
            medical_documents_text: medicalText,
            user_explanation:       userExplanation,
          });
      } else {
          data = await analyzeRejectionFromFile({
            policy_file:            policyFile || undefined,
            rejection_file:         rejectionFile || undefined,
            medical_file:           medicalFile || undefined,
            user_explanation:       userExplanation,
          });
      }
      setReport(data);
      setTimeout(() => document.getElementById("audit-results")?.scrollIntoView({ behavior: "smooth" }), 120);
    } catch {
      setError("Audit could not be processed. Ensure files are valid and under the size limit.");
    } finally { setLoading(false); }
  };

  const loadSample = (s: typeof SAMPLE_CASES[0]) => {
    setMode("text");
    setPolicyText(s.policy);
    setRejectionText(s.rejection);
    setMedicalText(s.medical);
    setUserExplanation(s.explanation);
    setReport(null);
    setError(null);
    setActiveField(null);
    setTimeout(() => document.getElementById("audit-form")?.scrollIntoView({ behavior: "smooth" }), 80);
  };

  const appealCfg = report ? (APPEAL_CFG[report.appeal_strength.label] || APPEAL_CFG["Moderate"]) : null;
  const alignCfg  = report ? (ALIGN_CFG[report.clause_alignment]       || ALIGN_CFG["Partial"])   : null;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Mono:wght@400;500&family=Outfit:wght@400;500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #f0ece3; color: #1a2018; font-family: 'Outfit', sans-serif; -webkit-font-smoothing: antialiased; }
        .page { min-height: 100vh; padding-top: 80px; padding-bottom: 120px; }

        /* ── PAGE HEADER ─────────────────────────────── */
        .page-hdr {
          max-width: 1160px; margin: 0 auto; padding: 48px 40px 40px;
          display: flex; justify-content: space-between; align-items: flex-end;
          border-bottom: 1px solid #c8c2b4; gap: 32px;
        }
        .page-eyebrow { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .18em; text-transform: uppercase; color: #5a7060; margin-bottom: 12px; }
        .page-title   { font-family: 'Cormorant Garamond', serif; font-size: clamp(34px,3.5vw,50px); font-weight: 500; line-height: 1.08; color: #0a0f0d; }
        .page-title em { font-style: italic; color: #1e5c2e; }
        .page-sub { font-size: 13px; color: #3a4038; max-width: 360px; line-height: 1.75; text-align: right; }

        /* ── FORM ─────────────────────────────────────── */
        .form-section {
          max-width: 1160px; margin: 0 auto; padding: 40px 40px 0;
          display: grid; grid-template-columns: 1fr 280px; gap: 24px; align-items: start;
        }
        .form-card { background: white; border: 1px solid #c8c2b4; border-radius: 4px; }
        .field-row { border-bottom: 1px solid #e8e3d8; }
        .field-row:last-of-type { border-bottom: none; }
        .field-row.active { background: #faf7f2; }
        .field-header { padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; gap: 12px; }
        .field-label-wrap { display: flex; align-items: center; gap: 12px; min-width: 0; }
        .field-num   { font-family: 'DM Mono', monospace; font-size: 10px; color: #5a7060; letter-spacing: .06em; flex-shrink: 0; }
        .field-label { font-size: 14px; font-weight: 500; color: #0a0f0d; }
        .field-req   { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .1em; text-transform: uppercase; color: #8c1f14; background: #f5d0cc; padding: 2px 7px; border-radius: 2px; flex-shrink: 0; }
        .field-opt   { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .1em; text-transform: uppercase; color: #5a7060; background: #e8e3d8; padding: 2px 7px; border-radius: 2px; flex-shrink: 0; }
        .field-status { font-family: 'DM Mono', monospace; font-size: 10px; color: #1e5c2e; flex-shrink: 0; }
        .field-body { padding: 0 24px 18px; }
        textarea {
          width: 100%; padding: 14px 16px; resize: vertical;
          border: 1px solid #c8c2b4; border-radius: 2px;
          font-family: 'DM Mono', monospace; font-size: 12px; line-height: 1.7;
          color: #0a0f0d; background: #faf8f3; outline: none; transition: border-color .2s;
        }
        textarea:focus { border-color: #1e5c2e; }
        textarea::placeholder { color: #9a9890; }
        .form-footer { padding: 20px 24px; border-top: 1px solid #e8e3d8; }
        .run-btn {
          width: 100%; padding: 16px; background: #1e5c2e; color: #e8f0ea;
          border: none; border-radius: 2px;
          font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
          cursor: pointer; transition: background .2s;
          display: flex; align-items: center; justify-content: center; gap: 10px;
        }
        .run-btn:hover:not(:disabled) { background: #2d7a42; }
        .run-btn:disabled { opacity: .5; cursor: not-allowed; }
        .spinner { width: 13px; height: 13px; border: 2px solid rgba(255,255,255,.3); border-top-color: white; border-radius: 50%; animation: spin .7s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg) } }
        .err-msg { margin-top: 14px; padding: 12px 16px; background: #f5d0cc; border: 1px solid #e08070; border-radius: 2px; font-family: 'DM Mono', monospace; font-size: 11px; color: #8c1f14; }

        /* ── SAMPLE CASES STRIP ───────────────────────────── */
        .samples-section {
          max-width: 1160px; margin: 0 auto; padding: 28px 40px 0;
        }
        .samples-eyebrow {
          font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .16em;
          text-transform: uppercase; color: #5a7060; margin-bottom: 12px;
          display: flex; align-items: center; gap: 10px;
        }
        .samples-eyebrow::after { content: ''; flex: 1; height: 1px; background: #c8c2b4; }
        .samples-scroll { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }
        .samples-scroll::-webkit-scrollbar { height: 3px; }
        .samples-scroll::-webkit-scrollbar-thumb { background: #c8c2b4; border-radius: 2px; }
        .sample-pill {
          flex-shrink: 0; display: flex; align-items: center; gap: 8px;
          padding: 10px 16px; background: white; border: 1px solid #c8c2b4;
          border-radius: 3px; cursor: pointer; transition: all .18s;
          font-family: 'Outfit', sans-serif;
        }
        .sample-pill:hover { border-color: #1e5c2e; background: #f5faf6; transform: translateY(-1px); }
        .sample-pill-icon { font-size: 14px; flex-shrink: 0; }
        .sample-pill-body { display: flex; flex-direction: column; gap: 2px; }
        .sample-pill-label { font-size: 12.5px; font-weight: 500; color: #0a0f0d; white-space: nowrap; }
        .sample-pill-tag {
          font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .07em;
          text-transform: uppercase; padding: 1px 5px; border-radius: 2px;
          align-self: flex-start;
        }

        /* ── UI TABS & UPLOAD ─────────────────────────── */
        .tabs-wrap { display: flex; border-bottom: 1px solid #c8c2b4; background: #faf8f3; }
        .tab-btn { flex: 1; padding: 14px; background: none; border: none; font-family: 'DM Mono', monospace; font-size: 11px; text-transform: uppercase; cursor: pointer; color: #5a7060; border-bottom: 2px solid transparent; transition: all .2s; }
        .tab-btn:hover { background: #f0ece3; }
        .tab-btn.active { color: #1e5c2e; border-bottom-color: #1e5c2e; font-weight: 600; background: white; }
        .file-dropzone { border: 1px dashed #c8c2b4; border-radius: 4px; padding: 24px; text-align: center; cursor: pointer; background: #faf8f3; margin-bottom: 16px; transition: border-color .2s; }
        .file-dropzone:last-of-type { margin-bottom: 0; }
        .file-dropzone:hover { border-color: #1e5c2e; background: white; }
        .dz-content { display: flex; align-items: center; justify-content: center; gap: 12px; }
        .dz-icon { font-size: 18px; }
        .dz-filename { font-size: 13px; color: #0a0f0d; font-family: 'DM Mono', monospace; font-weight: 500; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .dz-remove { background: #f5d0cc; border: none; color: #8c1f14; padding: 4px 8px; font-size: 10px; border-radius: 2px; cursor: pointer; font-family: 'DM Mono', monospace; transition: background .2s; }
        .dz-remove:hover { background: #e08070; color: white; }
        .dz-text { font-size: 13px; color: #5a7060; }
        .dz-req { background: #f5d0cc; color: #8c1f14; padding: 2px 6px; font-size: 9px; font-family: 'DM Mono', monospace; border-radius: 2px; }
        .upload-panel { padding: 32px 40px 18px; }

        /* ── SIDEBAR ──────────────────────────────────── */
        .sidebar { display: flex; flex-direction: column; gap: 14px; }
        .scard { background: white; border: 1px solid #c8c2b4; border-radius: 4px; padding: 20px; }
        .scard-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .16em; text-transform: uppercase; color: #5a7060; margin-bottom: 14px; }
        .scard-item { display: flex; align-items: flex-start; gap: 8px; padding: 7px 0; border-bottom: 1px solid #f0ece3; font-size: 13px; color: #1a2018; line-height: 1.5; }
        .scard-item:last-child { border-bottom: none; }
        .scard-dot { width: 4px; height: 4px; border-radius: 50%; background: #1e5c2e; flex-shrink: 0; margin-top: 5px; }
        .scard-num { font-family: 'DM Mono', monospace; font-size: 9px; color: #5a7060; flex-shrink: 0; }
        .warn-card { background: #faecd0; border: 1px solid #e0b870; border-radius: 4px; padding: 18px 20px; }
        .warn-title { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .14em; text-transform: uppercase; color: #7a4e08; margin-bottom: 8px; }
        .warn-text  { font-size: 13px; color: #5a3808; line-height: 1.6; }

        /* ── RESULTS DIVIDER ──────────────────────────── */
        .res-divider {
          max-width: 1160px; margin: 52px auto 0; padding: 0 40px;
          display: flex; align-items: center; gap: 16px;
        }
        .res-divider-label { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .15em; text-transform: uppercase; color: #5a7060; white-space: nowrap; }
        .res-divider-line  { flex: 1; height: 1px; background: #c8c2b4; }
        .conf-chip { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; padding: 4px 12px; border-radius: 2px; white-space: nowrap; }

        /* ── RESULTS LAYOUT ───────────────────────────── */
.results-section {
  max-width:1160px;
  margin:28px auto 0;
  padding:0 40px;
  display:grid;
  grid-template-columns: 1fr 320px; /* better balance */
  gap:22px;
  align-items:start;
}
        .results-main { display:flex;flex-direction:column;gap:14px; align-items:flex-start;   /*
        .results-side { display: flex; flex-direction: column; gap: 14px; width: 288px; position: sticky; top: 96px; }

        /* ── REPORT CARDS ─────────────────────────────── */
        .rcard { background: white; border: 1px solid #c8c2b4; border-radius: 4px; overflow: hidden; }
        .rcard-hdr {
          padding: 10px 22px; border-bottom: 1px solid #e8e3d8;
          display: flex; justify-content: space-between; align-items: center;
          background: #f5f0e8; flex-shrink: 0; min-height: 0;
        }
        .rcard-title { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .13em; text-transform: uppercase; color: #4a5248; }

        /* ── APPEAL DIRECTION CARD ────────────────────────
           No large percentage ring. Replaced with:
           - a coloured label badge  (left)
           - a slim progress bar     (right)
           - an amber disclaimer box (below)
           - the reasoning text      (bottom)
        ─────────────────────────────────────────────────── */
        .appeal-body { padding: 20px 24px 22px; display: flex; flex-direction: column; gap: 12px; }

        .appeal-top  { display: flex; align-items: center; gap: 16px; }

        .appeal-badge {
          font-family: 'Cormorant Garamond', serif;
          font-size: 20px; font-weight: 600; line-height: 1;
          padding: 8px 18px; border-radius: 3px; flex-shrink: 0;
          white-space: nowrap;
        }

        .appeal-bar-wrap { flex: 1; min-width: 0; }
        .appeal-bar-meta {
          font-family: 'DM Mono', monospace; font-size: 9px;
          letter-spacing: .08em; text-transform: uppercase;
          color: #5a7060; margin-bottom: 6px;
          display: flex; justify-content: space-between;
        }
        .appeal-bar-track { height: 6px; border-radius: 3px; overflow: hidden; }
        .appeal-bar-fill  { height: 100%; border-radius: 3px; transition: width 1.2s ease; }

        .appeal-disclaimer {
          padding: 9px 14px;
          background: #fdf8ec; border: 1px solid #ddd090; border-radius: 3px;
          font-family: 'DM Mono', monospace; font-size: 9px;
          letter-spacing: .04em; color: #7a5c10; line-height: 1.65;
        }

        .appeal-reasoning {
          font-size: 13px; color: #3a4038; line-height: 1.7;
          border-top: 1px solid #f0ece3; padding-top: 12px;
        }

        /* ── CLAUSE ANALYSIS ──────────────────────────── */
        .clause-row { display: flex; flex-direction: column; gap: 5px; padding: 12px 24px; border-bottom: 1px solid #f0ece3; }
        .clause-row:last-child { border-bottom: none; }
        .clause-key   { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; color: #5a7060; }
        .clause-value { font-size: 13px; color: #0a0f0d; line-height: 1.65; }
        .align-badge  { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .08em; text-transform: uppercase; padding: 4px 10px; border-radius: 2px; white-space: nowrap; flex-shrink: 0; }

        /* ── DEEP ANALYSIS ────────────────────────────── */
        .deep-section { border-bottom: 1px solid #f0ece3; }
        .deep-section:last-child { border-bottom: none; }
        .deep-hdr {
          width: 100%; background: none; border: none;
          padding: 13px 24px; display: flex; align-items: center; gap: 12px;
          cursor: pointer; text-align: left; transition: background .15s;
        }
        .deep-hdr:hover { background: #faf7f2; }
        .deep-section.open .deep-hdr { background: #faf7f2; }
        .deep-icon    { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; flex-shrink: 0; }
        .deep-label   { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .08em; text-transform: uppercase; color: #1a2018; flex: 1; line-height: 1.4; }
        .deep-chevron { font-size: 16px; color: #5a7060; transition: transform .2s; line-height: 1; flex-shrink: 0; }
        .deep-chevron.open { transform: rotate(90deg); }
        .deep-body { padding: 4px 20px 16px; }

        /* ── LIST ITEMS ───────────────────────────────── */
        .list-stack { display: flex; flex-direction: column; gap: 8px; }
        .reasoning-block { background: #faf7f2; border: 1px solid #e8e3d8; border-radius: 3px; padding: 16px; font-size: 13px; line-height: 1.8; color: #1a2018; }
        .reasoning-block p + p { margin-top: 10px; }
        .ev-item { display: flex; gap: 10px; padding: 9px 12px; background: white; border: 1px solid #e8e3d8; border-radius: 3px; }
        .ev-num  { font-family: 'DM Mono', monospace; font-size: 9px; color: #5a7060; flex-shrink: 0; margin-top: 2px; }
        .ev-text { font-size: 12.5px; color: #1a2018; line-height: 1.65; }
        .ov-item { display: flex; gap: 10px; padding: 9px 12px; background: #eef8f2; border: 1px solid #9dd0aa; border-radius: 3px; }
        .ov-icon { flex-shrink: 0; color: #1e5c2e; font-size: 11px; margin-top: 2px; }
        .ov-text { font-size: 12.5px; color: #143a1e; line-height: 1.65; }
        .wk-item { display: flex; gap: 10px; padding: 9px 12px; background: #fdf4f3; border: 1px solid #e09090; border-radius: 3px; }
        .wk-icon { flex-shrink: 0; color: #8c1f14; font-size: 10px; margin-top: 3px; }
        .wk-text { font-size: 12.5px; color: #4a1010; line-height: 1.65; }

        /* ── CASE ASSESSMENT ──────────────────────────── */
        .points-grid { display: grid; grid-template-columns: 1fr 1fr; }
        .points-col  { padding: 14px 18px; }
        .points-col + .points-col { border-left: 1px solid #e8e3d8; }
        .points-col-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .14em; text-transform: uppercase; margin-bottom: 12px; }
        .point-item { display: flex; gap: 8px; align-items: flex-start; padding: 7px 0; border-bottom: 1px solid #f0ece3; font-size: 12.5px; color: #1a2018; line-height: 1.55; }
        .point-item:last-child { border-bottom: none; }
        .point-icon { flex-shrink: 0; font-size: 9px; margin-top: 4px; }

        /* ── REAPPLICATION STEPS ──────────────────────── */
        .step-row { display: flex; gap: 14px; align-items: flex-start; padding: 11px 22px; border-bottom: 1px solid #f0ece3; }
        .step-row:last-child { border-bottom: none; }
        .step-num  { font-family: 'DM Mono', monospace; font-size: 9px; color: #5a7060; flex-shrink: 0; margin-top: 3px; min-width: 18px; }
        .step-text { font-size: 13px; color: #1a2018; line-height: 1.65; }

        /* ── REGULATORY BODY ──────────────────────────── */
        .reg-body { padding: 14px 22px; font-size: 12.5px; line-height: 1.75; color: #3a4038; white-space: pre-line; max-height: 200px; overflow-y: auto; }
        .reg-body::-webkit-scrollbar { width: 4px; }
        .reg-body::-webkit-scrollbar-thumb { background: #c8c2b4; border-radius: 2px; }

        /* ── LOW CONFIDENCE BANNER ────────────────────── */
        .low-conf { padding: 14px 20px; background: #faecd0; border: 1px solid #e0b870; border-radius: 3px; display: flex; gap: 12px; align-items: flex-start; font-size: 13px; color: #5a3808; line-height: 1.65; }

        /* ── SIDE COLUMN ──────────────────────────────── */
        .dark-card { background: #0a0f0d; border-radius: 4px; padding: 18px; }
        .dark-card-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .14em; text-transform: uppercase; color: rgba(255,255,255,.3); margin-bottom: 14px; }
        .dark-row { padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,.07); display: flex; justify-content: space-between; align-items: center; gap: 8px; }
        .dark-row:last-child { border-bottom: none; }
        .dark-key { font-size: 12px; color: rgba(255,255,255,.45); }
        .dark-val { font-family: 'DM Mono', monospace; font-size: 10px; color: #d8eedd; letter-spacing: .04em; text-align: right; }

        /* ── CHAT ─────────────────────────────────────── */
        .chat-wrap { width: 100%; }
        .chat-trigger {
          width: 100%; padding: 13px 20px; background: #0a0f0d; color: #e8f0ea;
          border: 1px solid #2d5a3d; border-radius: 4px;
          font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .14em; text-transform: uppercase;
          cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;
          transition: all .2s;
        }
        .chat-trigger:hover { background: #1a2018; border-color: #4a7c5f; }
        .ct-icon  { font-size: 14px; color: #4a9d5f; }
        .ct-badge { font-size: 8px; letter-spacing: .08em; padding: 2px 7px; background: rgba(74,157,95,.15); border: 1px solid rgba(74,157,95,.3); border-radius: 10px; color: #4a9d5f; }
        .chat-panel { background: white; border: 1px solid #c8c2b4; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; }
        .chat-hdr   { padding: 12px 18px; background: #0a0f0d; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .chat-hdr-title { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: #d8eedd; }
        .chat-hdr-sub   { font-size: 11px; color: rgba(255,255,255,.3); margin-top: 2px; }
        .chat-close { background: none; border: none; color: rgba(255,255,255,.4); cursor: pointer; font-size: 20px; line-height: 1; padding: 0; transition: color .2s; }
        .chat-close:hover { color: white; }
        .chat-dot { width: 6px; height: 6px; border-radius: 50%; }
        .chat-starters { padding: 10px 14px; background: #f5f0e8; border-bottom: 1px solid #e8e3d8; flex-shrink: 0; }
        .starters-label { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .12em; text-transform: uppercase; color: #5a7060; margin-bottom: 7px; }
        .starter-btn { display: block; width: 100%; text-align: left; padding: 7px 11px; margin-bottom: 5px; background: white; border: 1px solid #c8c2b4; border-radius: 2px; font-size: 12px; color: #1a2018; cursor: pointer; transition: all .15s; line-height: 1.4; }
        .starter-btn:last-child { margin-bottom: 0; }
        .starter-btn:hover { background: #eef5f0; border-color: #1e5c2e; color: #1e5c2e; }
        .starter-btn:disabled { opacity: .4; cursor: not-allowed; }
        .chat-msgs { overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; min-height: 180px; max-height: 260px; background: #faf8f3; }
        .chat-msgs::-webkit-scrollbar { width: 3px; }
        .chat-msgs::-webkit-scrollbar-thumb { background: #c8c2b4; border-radius: 2px; }
        .chat-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 6px; text-align: center; padding: 20px; }
        .chat-empty-icon { font-size: 20px; color: #5a7060; margin-bottom: 4px; }
        .chat-empty > div { font-family: 'Cormorant Garamond', serif; font-size: 16px; font-style: italic; color: #5a7060; }
        .chat-empty-sub { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .07em; color: #b0a898; font-style: normal !important; text-transform: uppercase; }
        .msg { display: flex; flex-direction: column; gap: 3px; max-width: 92%; }
        .msg.user      { align-self: flex-end;   align-items: flex-end; }
        .msg.assistant { align-self: flex-start; }
        .msg-meta { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .06em; text-transform: uppercase; color: #9a9690; padding: 0 2px; }
        .msg-bubble { padding: 10px 13px; border-radius: 3px; font-size: 12.5px; line-height: 1.7; word-break: break-word; }
        .msg.user .msg-bubble      { background: #1e5c2e; color: #e8f0ea; border-bottom-right-radius: 0; }
        .msg.assistant .msg-bubble { background: white;   color: #0a0f0d; border: 1px solid #c8c2b4; border-bottom-left-radius: 0; }
        .msg-sources { display: flex; flex-wrap: wrap; gap: 4px; }
        .msg-chip    { font-family: 'DM Mono', monospace; font-size: 8px; padding: 2px 7px; background: #d6eddc; color: #1e5c2e; border-radius: 10px; }
        .typing-row  { align-self: flex-start; display: flex; flex-direction: column; gap: 3px; }
        .typing-meta { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .06em; text-transform: uppercase; color: #9a9690; }
        .typing { display: flex; gap: 4px; padding: 9px 13px; background: white; border: 1px solid #c8c2b4; border-radius: 3px; border-bottom-left-radius: 0; }
        .typing span { width: 5px; height: 5px; border-radius: 50%; background: #8fa896; animation: bounce 1.2s infinite; }
        .typing span:nth-child(2) { animation-delay: .2s; }
        .typing span:nth-child(3) { animation-delay: .4s; }
        @keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-5px)} }
        .chat-input-row { display: flex; border-top: 1px solid #e8e3d8; background: white; flex-shrink: 0; }
        .chat-input { flex: 1; padding: 11px 14px; border: none; outline: none; font-family: 'Outfit', sans-serif; font-size: 12.5px; color: #0a0f0d; background: transparent; }
        .chat-input::placeholder { color: #9a9890; }
        .chat-send { padding: 0 16px; border: none; border-left: 1px solid #e8e3d8; background: none; cursor: pointer; font-size: 15px; color: #1e5c2e; transition: background .15s; }
        .chat-send:hover:not(:disabled) { background: #eef5f0; }
        .chat-send:disabled { color: #c8c2b4; cursor: not-allowed; }
        .chat-hint { padding: 4px 14px 7px; font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .05em; color: #b0a898; background: white; }

        /* ── FOOTNOTE ─────────────────────────────────── */
        .report-fn {
          max-width: 1160px; margin: 36px auto 0; padding: 18px 40px 40px;
          font-family: 'DM Mono', monospace; font-size: 9px; color: #5a7060;
          letter-spacing: .05em; text-align: center; line-height: 2;
          border-top: 1px solid #e8e3d8;
        }
        .report-fn strong { color: #3a4038; letter-spacing: .08em; }

        /* ── RESPONSIVE ───────────────────────────────── */
        @media(max-width: 960px) {
          .page-hdr,.form-section,.res-divider,.results-section,.report-fn { padding-left: 20px; padding-right: 20px; }
          .page-hdr { flex-direction: column; align-items: flex-start; gap: 14px; }
          .page-sub { text-align: left; max-width: 100%; }
          .form-section,.results-section { grid-template-columns: 1fr; }
          .points-grid { grid-template-columns: 1fr; }
          .points-col + .points-col { border-left: none; border-top: 1px solid #e8e3d8; }
          .results-side { position: static; width: 100%; }
        }
        @media(max-width: 600px) {
          .appeal-top { flex-direction: column; align-items: flex-start; }
          .appeal-bar-wrap { width: 100%; }
        }
      `}</style>

      <div className="page">

        {/* ── HEADER ── */}
        <div className="page-hdr">
          <div>
            <div className="page-eyebrow">Post-Rejection Audit</div>
            <h1 className="page-title">Understand the rejection.<br /><em>Navigate your appeal.</em></h1>
          </div>
          <p className="page-sub">
            Paste the policy wording, rejection letter, and any medical records.
            CareBridge identifies the clause applied, documentation gaps, and the
            appeal direction — with IRDAI regulatory context.
          </p>
        </div>

        {/* ── SAMPLE CASES STRIP ── */}
        <div className="samples-section">
          <div className="samples-eyebrow">Try a sample case</div>
          <div className="samples-scroll">
            {SAMPLE_CASES.map((s, i) => (
              <button key={i} className="sample-pill" onClick={() => loadSample(s)}>
                <span className="sample-pill-icon">{s.icon}</span>
                <div className="sample-pill-body">
                  <span className="sample-pill-label">{s.label}</span>
                  <span className="sample-pill-tag" style={{ color: s.tagColor, background: s.tagBg }}>{s.tag}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* ── FORM ── */}
        <div className="form-section" id="audit-form">
          <div className="form-card" style={{ overflow: "hidden" }}>
            <div className="tabs-wrap">
              <button className={`tab-btn ${mode === "upload" ? "active" : ""}`} onClick={() => setMode("upload")}>
                Upload Documents
              </button>
              <button className={`tab-btn ${mode === "text" ? "active" : ""}`} onClick={() => setMode("text")}>
                Paste Text
              </button>
            </div>

            {mode === "upload" ? (
              <div className="upload-panel">
                {[
                  { label: "Policy Document PDF", file: policyFile, setFile: setPolicyFile, req: true, accept: "application/pdf" },
                  { label: "Rejection Letter (PDF/IMG)", file: rejectionFile, setFile: setRejectionFile, req: true, accept: "application/pdf,image/*" },
                  { label: "Medical Records (PDF)", file: medicalFile, setFile: setMedicalFile, req: false, accept: "application/pdf" },
                ].map((fz, i) => (
                  <div key={i} className="file-dropzone" onClick={() => document.getElementById(`dz-${i}`)?.click()}>
                    <input id={`dz-${i}`} type="file" accept={fz.accept} style={{ display: 'none' }} 
                      onChange={e => {
                        const file = e.target.files?.[0];
                        if (file) fz.setFile(file);
                      }} 
                    />
                    <div className="dz-content">
                      {fz.file ? (
                        <>
                          <span className="dz-icon">📄</span>
                          <span className="dz-filename" title={fz.file.name}>{fz.file.name}</span>
                          <button className="dz-remove" onClick={(e) => { e.stopPropagation(); fz.setFile(null); }}>✕ Remove</button>
                        </>
                      ) : (
                        <>
                          <span className="dz-icon">☁️</span>
                          <span className="dz-text">Click to upload {fz.label}</span>
                          {fz.req && <span className="dz-req">Required</span>}
                        </>
                      )}
                    </div>
                  </div>
                ))}
                
                <div style={{ marginTop: '24px' }}>
                  <div className="field-label-wrap" style={{ marginBottom: "12px" }}>
                    <span className="field-label">Additional Context</span>
                    <span className="field-opt">Optional</span>
                  </div>
                  <textarea rows={4} placeholder="When diagnosed, when policy purchased, any prior communications..." value={userExplanation} onChange={e => setUserExplanation(e.target.value)} />
                </div>
              </div>
            ) : (
              <div>
                {[
                  { id: "policy",    label: "Policy Wording",         req: true,  rows: 7, ph: "Paste the relevant sections of your policy document...",             val: policyText,      set: setPolicyText },
                  { id: "rejection", label: "Rejection Letter",        req: true,  rows: 6, ph: "Paste the insurer's rejection letter or claim repudiation notice...", val: rejectionText,   set: setRejectionText },
                  { id: "medical",   label: "Medical Records Summary", req: false, rows: 5, ph: "Paste discharge summary, diagnosis, treatment dates, doctor notes...", val: medicalText,     set: setMedicalText },
                  { id: "context",   label: "Your Explanation",        req: false, rows: 4, ph: "When diagnosed, when policy purchased, any prior communications...",  val: userExplanation, set: setUserExplanation },
                ].map((f, i) => (
                  <div key={f.id} className={`field-row${activeField === f.id ? " active" : ""}`}>
                    <div className="field-header" onClick={() => setActiveField(activeField === f.id ? null : f.id)}>
                      <div className="field-label-wrap">
                        <span className="field-num">{String(i + 1).padStart(2, "0")}</span>
                        <span className="field-label">{f.label}</span>
                        <span className={f.req ? "field-req" : "field-opt"}>{f.req ? "Required" : "Optional"}</span>
                      </div>
                      {f.val.trim() && <span className="field-status">✓ {f.val.trim().length} chars</span>}
                    </div>
                    {((activeField === f.id) || (f.req && !f.val)) && (
                      <div className="field-body">
                        <textarea rows={f.rows} placeholder={f.ph} value={f.val}
                          onChange={e => f.set(e.target.value)}
                          onFocus={() => setActiveField(f.id)}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            <div className="form-footer">
              <button className="run-btn" onClick={handleAnalyze} disabled={loading}>
                {loading ? <><span className="spinner" />Running audit...</> : "Run Claim Audit"}
              </button>
              {error && <div className="err-msg">{error}</div>}
            </div>
          </div>

          <div className="sidebar">
            <div className="scard">
              <div className="scard-label">What this audit covers</div>
              {[
                "Clause identification from policy text",
                "Pre-existing disease contradiction check",
                "Waiting period evidence analysis",
                "Documentation gap assessment",
                "Appeal direction indicator",
                "IRDAI regulatory references",
                "Step-by-step reapplication guide",
              ].map((t, i) => (
                <div key={i} className="scard-item"><span className="scard-dot" />{t}</div>
              ))}
            </div>
            <div className="warn-card">
              <div className="warn-title">Important</div>
              <p className="warn-text">Results improve significantly with complete policy wording and the full rejection letter — not summaries.</p>
            </div>
          </div>
        </div>

        {/* ── RESULTS ── */}
        {report && (
          <>
            <div className="res-divider" id="audit-results">
              <span className="res-divider-label">Audit Report</span>
              <span className="res-divider-line" />
              <span className="conf-chip" style={{
                background: report.confidence === "High" ? "#d6eddc" : report.confidence === "Low" ? "#f5d0cc" : "#faecd0",
                color:      report.confidence === "High" ? "#1e5c2e" : report.confidence === "Low" ? "#8c1f14" : "#7a4e08",
              }}>
                Confidence: {report.confidence}
              </span>
            </div>

            <div className="results-section">

              {/* ══ MAIN COLUMN ══ */}
              <div className="results-main">

                {/* Low confidence warning — system_notice is now typed, no cast needed */}
                {report.confidence === "Low" && (
                  <div className="low-conf">
                    <span style={{ fontSize: 15, flexShrink: 0 }}>⚠</span>
                    <span>
                      Low confidence — documents may be incomplete. Request written
                      clarification from your insurer before proceeding.
                      {report.system_notice && ` ${report.system_notice}`}
                    </span>
                  </div>
                )}

                {/* APPEAL DIRECTION INDICATOR */}
                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">Status & Verdict</span>
                    <span className="rcard-title" style={{ color: appealCfg?.color }}>
                      {report.appeal_strength.label}
                    </span>
                  </div>
                  <div className="appeal-body">

                    {/* Badge + bar row */}
                    <div className="appeal-top">
                      <div className="appeal-badge" style={{
                        color:      appealCfg?.color,
                        background: appealCfg?.bg,
                        border:     `1px solid ${appealCfg?.border}`,
                      }}>
                        {report.appeal_strength.label}
                      </div>
                      <div className="appeal-bar-wrap">
                        <div className="appeal-bar-meta">
                          <span>Relative position</span>
                          <span>{report.appeal_strength.percentage}%</span>
                        </div>
                        <div className="appeal-bar-track" style={{ background: appealCfg?.track }}>
                          <div className="appeal-bar-fill" style={{
                            width:      `${report.appeal_strength.percentage}%`,
                            background: appealCfg?.color,
                          }} />
                        </div>
                      </div>
                    </div>

                    {/* Explicit disclaimer — always visible */}
                    <div className="appeal-disclaimer">
                      ⚠ Directional indicator only — not a legal prediction or probability of success.
                      Verify all findings with your insurer or a qualified advisor before taking action.
                    </div>

                    <p className="appeal-reasoning">{report.appeal_strength.reasoning}</p>
                  </div>
                </div>

                {/* CLAUSE ANALYSIS */}
                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">Why Rejected (Policy vs Claim Gap)</span>
                    <span className="align-badge" style={{
                      background: alignCfg?.bg,
                      color:      alignCfg?.color,
                      border:     `1px solid ${alignCfg?.border}`,
                    }}>
                      {report.clause_alignment}
                    </span>
                  </div>
                  {[
                    { key: "Rejection Basis", val: report.why_rejected },
                    { key: "Clause Detected", val: report.policy_clause_detected },
                    { key: "Alignment",       val: alignCfg?.label || report.clause_alignment },
                    { key: "Case Summary",    val: report.case_summary },
                  ].filter(r => r.val).map(({ key, val }) => (
                    <div key={key} className="clause-row">
                      <div className="clause-key">{key}</div>
                      <div className="clause-value">{val}</div>
                    </div>
                  ))}
                </div>

                {/* DEEP ANALYSIS */}
                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">Deep Analysis</span>
                    <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 9, letterSpacing: ".1em", textTransform: "uppercase", padding: "3px 9px", background: "#d6eddc", color: "#1e5c2e", borderRadius: 2, border: "1px solid #9dd0aa" }}>
                      4 sections
                    </span>
                  </div>
                  <DeepAnalysis report={report} />
                </div>

                {/* CASE ASSESSMENT */}
                <div className="rcard">
                  <div className="rcard-hdr"><span className="rcard-title">Case Assessment & Missing Documents</span></div>
                  <div className="points-grid">
                    <div className="points-col">
                      <div className="points-col-label" style={{ color: "#1e5c2e" }}>Points in your favour</div>
                      {report.strong_points?.length > 0
                        ? report.strong_points.map((p, i) => (
                            <div key={i} className="point-item">
                              <span className="point-icon" style={{ color: "#1e5c2e" }}>◆</span>{p}
                            </div>
                          ))
                        : <div className="point-item" style={{ color: "#9a9890", fontStyle: "italic" }}>None identified</div>
                      }
                    </div>
                    <div className="points-col">
                      <div className="points-col-label" style={{ color: "#8c1f14" }}>Challenges to address</div>
                      {report.weak_points?.map((p, i) => (
                        <div key={i} className="point-item">
                          <span className="point-icon" style={{ color: "#8c1f14" }}>▲</span>{p}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* REAPPLICATION STEPS */}
                {report.reapplication_possible && report.reapplication_steps?.length > 0 && (
                  <div className="rcard">
                    <div className="rcard-hdr">
                      <span className="rcard-title">What You Should Do Next</span>
                      <span className="rcard-title" style={{ color: "#1e5c2e" }}>
                        {report.reapplication_steps.length} actions
                      </span>
                    </div>
                    {report.reapplication_steps.map((step, i) => (
                      <div key={i} className="step-row">
                        <span className="step-num">{String(i + 1).padStart(2, "0")}</span>
                        <span className="step-text">{step}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* REGULATORY */}
                {report.regulatory_considerations && (
                  <div className="rcard">
                    <div className="rcard-hdr">
                      <span className="rcard-title">IRDAI Regulatory Context</span>
                      <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 9, letterSpacing: ".1em", textTransform: "uppercase", padding: "3px 9px", background: "#d6eddc", color: "#1e5c2e", borderRadius: 2, border: "1px solid #9dd0aa" }}>
                        RAG · IRDAI
                      </span>
                    </div>
                    <div className="reg-body">{report.regulatory_considerations}</div>
                  </div>
                )}

              </div>

              {/* ══ SIDE COLUMN ══ */}
              <div className="results-side">

                {/* Quick summary — "Appeal Strength" renamed to "Direction" */}
                <div className="dark-card">
                  <div className="dark-card-label">Quick Summary</div>
                  {[
                    { k: "Direction",        v: `${report.appeal_strength.label} (${report.appeal_strength.percentage}%)` },
                    { k: "Clause Alignment", v: report.clause_alignment },
                    { k: "Can Reapply",      v: report.reapplication_possible ? "Yes" : "Unlikely" },
                    { k: "Confidence",       v: report.confidence },
                  ].map(({ k, v }) => (
                    <div key={k} className="dark-row">
                      <span className="dark-key">{k}</span>
                      <span className="dark-val">{v}</span>
                    </div>
                  ))}
                </div>

                <ReportChat report={report} />

                <div className="scard">
                  <div className="scard-label">Escalation path</div>
                  {[
                    "File complaint with insurer's GRO",
                    "Escalate to IRDAI IGMS if no reply in 15 days",
                    "File before Insurance Ombudsman within 1 year",
                    "Approach Consumer Forum if needed",
                  ].map((t, i) => (
                    <div key={i} className="scard-item">
                      <span className="scard-num">{String(i + 1).padStart(2, "0")}</span>{t}
                    </div>
                  ))}
                </div>

                <div className="scard">
                  <div className="scard-label">Documents for appeal</div>
                  {[
                    "Policy document with schedule",
                    "Original rejection letter",
                    "All medical records submitted",
                    "Hospital bills & discharge summary",
                    "Doctor's certificate with diagnosis date",
                    "All prior insurer correspondence",
                  ].map((t, i) => (
                    <div key={i} className="scard-item">
                      <span className="scard-dot" />{t}
                    </div>
                  ))}
                </div>

                <HelpSupport />

              </div>
            </div>

            {/* Footer — upgraded to 3-line explicit disclaimer */}
            <p className="report-fn">
              <strong>CareBridge provides interpretative analysis only.</strong><br />
              Not legal advice · Not a prediction of claim outcome · Directional indicators are not probabilities.<br />
              Verify all findings with your insurer or a qualified legal or insurance advisor before taking action.
            </p>
          </>
        )}
      </div>
    </>
  );
}