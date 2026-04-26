"use client";

import { useState } from "react";

const SUPPORT_ORGS = [
  {
    name:        "Insurance Ombudsman",
    type:        "Regulatory",
    description: "Free, binding dispute resolution for claim rejections up to ₹50 lakhs. Must be approached within 1 year of insurer's final reply. No lawyers required.",
    action:      "File a complaint",
    url:         "https://cioins.co.in/",
    phone:       null,
    tags:        ["Free", "Binding", "₹50L limit"],
    priority:     1,
  },
  {
    name:        "IRDAI Consumer Helpline",
    type:        "Regulatory",
    description: "Toll-free helpline for immediate guidance on insurance grievances and policyholder rights.",
    action:      "Call now",
    url:         "https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo253&flag=1",
    phone:       "155255 / 1800 4254 732",
    tags:        ["Free", "Toll-free"],
    priority:     2,
  },
  {
    name:        "IRDAI Bima Bharosa Portal",
    type:        "Regulatory",
    description: "File and track your insurance complaint officially. Insurers must respond within 15 days.",
    action:      "File complaint",
    url:         "https://bimabharosa.irdai.gov.in/",
    phone:       null,
    tags:        ["Official record", "15-day deadline"],
    priority:     3,
  },
  {
    name:        "National Consumer Helpline",
    type:        "Consumer Rights",
    description: "Government-run consumer grievance centre. Available in multiple languages.",
    action:      "Get help",
    url:         "https://consumerhelpline.gov.in/",
    phone:       "1800-11-4000",
    tags:        ["Free", "Multilingual"],
    priority:     4,
  },
  {
    name:        "NALSA — Free Legal Aid",
    type:        "Legal Aid",
    description: "Free legal aid for economically weaker sections. Assists with insurance disputes and appeal documentation.",
    action:      "Find legal aid",
    url:         "https://nalsa.gov.in/",
    phone:       "15100",
    tags:        ["Free", "Low income"],
    priority:     5,
  },
  {
    name:        "Consumer Forum (NCDRC)",
    type:        "Legal",
    description: "National Consumer Disputes Redressal Commission for disputes above ₹1 crore. File online.",
    action:      "File online",
    url:         "https://ncdrc.nic.in/",
    phone:       null,
    tags:        ["Online filing"],
    priority:     6,
  },
];

const TYPE_CFG: Record<string, { color: string; bg: string }> = {
  "Regulatory":      { color: "#1e5c2e", bg: "#d6eddc" },
  "Consumer Rights": { color: "#2d3a7a", bg: "#dce4f5" },
  "Legal Aid":       { color: "#7a4e08", bg: "#faecd0" },
  "Legal":           { color: "#4a1a7a", bg: "#ede4f5" },
};

export default function HelpSupport() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <>
      <style>{`
        .hs-wrap { background: white; border: 1px solid #c8c2b4; border-radius: 4px; overflow: hidden; }
        .hs-head { padding: 14px 20px; border-bottom: 1px solid #e8e3d8; display: flex; justify-content: space-between; align-items: center; }
        .hs-head-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: .16em; text-transform: uppercase; color: #5a7060; }
        .hs-row { border-bottom: 1px solid #f0ece3; }
        .hs-row:last-child { border-bottom: none; }
        .hs-trigger { width: 100%; padding: 11px 20px; background: none; border: none; cursor: pointer;
          display: flex; align-items: center; gap: 10px; text-align: left; transition: background .15s; }
        .hs-trigger:hover { background: #faf8f3; }
        .hs-num { font-family: 'DM Mono', monospace; font-size: 9px; color: #b0a898; flex-shrink: 0; }
        .hs-name { font-size: 12.5px; font-weight: 500; color: #0a0f0d; flex: 1; }
        .hs-badge { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .06em;
          text-transform: uppercase; padding: 2px 6px; border-radius: 2px; flex-shrink: 0; }
        .hs-chevron { font-size: 9px; color: #b0a898; flex-shrink: 0; transition: transform .2s; }
        .hs-chevron.open { transform: rotate(180deg); }
        .hs-body { padding: 0 20px 14px 39px; display: flex; flex-direction: column; gap: 8px; }
        .hs-desc { font-size: 11.5px; color: #5a6560; line-height: 1.65; }
        .hs-phone { font-family: 'DM Mono', monospace; font-size: 11px; color: #1e5c2e; }
        .hs-tags { display: flex; flex-wrap: wrap; gap: 4px; }
        .hs-tag { font-family: 'DM Mono', monospace; font-size: 8px; letter-spacing: .05em;
          padding: 2px 7px; background: #f0ece3; color: #5a7060; border-radius: 2px; }
        .hs-link { display: inline-flex; align-items: center; gap: 5px; font-family: 'DM Mono', monospace;
          font-size: 9px; letter-spacing: .1em; text-transform: uppercase; color: #1e5c2e; text-decoration: none; }
        .hs-link:hover { opacity: .7; }
        .hs-fn { padding: 10px 20px; background: #faf8f3; border-top: 1px solid #e8e3d8;
          font-family: 'DM Mono', monospace; font-size: 9px; color: #b0a898; line-height: 1.6; letter-spacing: .03em; }
      `}</style>

      <div className="hs-wrap">
        <div className="hs-head">
          <span className="hs-head-label">Support &amp; Escalation</span>
          <span className="hs-head-label">{SUPPORT_ORGS.length} resources</span>
        </div>

        {SUPPORT_ORGS.map((org, i) => {
          const cfg = TYPE_CFG[org.type] ?? TYPE_CFG["Legal"];
          const isOpen = open === i;
          return (
            <div key={i} className="hs-row">
              <button className="hs-trigger" onClick={() => setOpen(isOpen ? null : i)}>
                <span className="hs-num">{String(i + 1).padStart(2, "0")}</span>
                <span className="hs-name">{org.name}</span>
                <span className="hs-badge" style={{ color: cfg.color, background: cfg.bg }}>{org.type}</span>
                <span className={`hs-chevron${isOpen ? " open" : ""}`}>▼</span>
              </button>
              {isOpen && (
                <div className="hs-body">
                  <p className="hs-desc">{org.description}</p>
                  {org.phone && <div className="hs-phone">{org.phone}</div>}
                  <div className="hs-tags">
                    {org.tags.map((t, j) => <span key={j} className="hs-tag">{t}</span>)}
                  </div>
                  <a href={org.url} target="_blank" rel="noopener noreferrer" className="hs-link">
                    {org.action} ↗
                  </a>
                </div>
              )}
            </div>
          );
        })}

        <div className="hs-fn">
          All resources are government bodies or statutory regulators. CareBridge does not endorse any specific service.
        </div>
      </div>
    </>
  );
}