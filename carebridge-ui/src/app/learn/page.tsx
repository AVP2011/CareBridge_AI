"use client";

import { useState } from "react";
import type { JSX } from "react";

const CATEGORIES = ["All", "IRDAI Regulations", "Claims & Appeals", "Policy Basics", "Grievance", "Ombudsman"] as const;
type Category = typeof CATEGORIES[number];

interface Resource {
  title: string; description: string; source: string;
  type: "Document" | "Portal" | "Guide" | "Circular";
  category: Exclude<Category, "All">; url: string; tags: string[];
}

const RESOURCES: Resource[] = [
  { title:"IRDAI Protection of Policyholders' Interests Regulations 2017", description:"The primary regulation governing how insurers must treat policyholders — covers claim decisions, rejection requirements, timelines, and grievance rights.", source:"IRDAI", type:"Document", category:"IRDAI Regulations", url:"https://www.irdai.gov.in/ADMINCMS/cms/Uploadedfiles/Regulation/PolicyHolderRegulation2017.pdf", tags:["claims","rejection","30-day rule","policyholder rights"] },
  { title:"IRDAI Health Insurance Regulations 2016", description:"Governs health insurance product structure — standardised exclusions, renewability, co-payment disclosure, AYUSH coverage, and mental health parity mandates.", source:"IRDAI", type:"Document", category:"IRDAI Regulations", url:"https://www.irdai.gov.in/ADMINCMS/cms/Uploadedfiles/Regulation/HealthInsuranceRegulations2016.pdf", tags:["health insurance","exclusions","renewability","AYUSH"] },
  { title:"IRDAI Standardisation of Exclusions in Health Insurance", description:"Circular standardising which conditions insurers can and cannot permanently exclude — limits arbitrary exclusions across all health policies.", source:"IRDAI", type:"Circular", category:"IRDAI Regulations", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_NoYearList.aspx?DF=C&mid=3.2", tags:["exclusions","standardisation","permanent exclusions"] },
  { title:"IRDAI Consumer Portal — Policy & Regulation Hub", description:"Official IRDAI portal with all insurance regulations, circulars, and consumer advisories in one place. Start here for any regulatory question.", source:"IRDAI", type:"Portal", category:"IRDAI Regulations", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo246&flag=1", tags:["regulations","circulars","consumer","official"] },
  { title:"How to File a Health Insurance Claim — IRDAI Consumer Guide", description:"Step-by-step official guide covering cashless and reimbursement claim processes, required documents, and what to do if a claim is delayed.", source:"IRDAI", type:"Guide", category:"Claims & Appeals", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo4152&flag=1", tags:["claim process","cashless","reimbursement","documents"] },
  { title:"Pre-existing Disease — Definition and Waiting Period Rules", description:"IRDAI's official definition of pre-existing disease, the 48-month rule, and the moratorium period after which insurers cannot repudiate claims for non-disclosure.", source:"IRDAI", type:"Guide", category:"Claims & Appeals", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo4152&flag=1", tags:["pre-existing disease","waiting period","48 months","moratorium"] },
  { title:"Claim Settlement Ratios — Annual Report", description:"IRDAI publishes insurer-wise claim settlement ratios annually. Use this to evaluate your insurer's track record before purchasing or when appealing.", source:"IRDAI Annual Report", type:"Document", category:"Claims & Appeals", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_NoYearList.aspx?DF=AR&mid=3.2", tags:["claim settlement ratio","CSR","insurer comparison"] },
  { title:"Mental Healthcare Act 2017 — Insurance Parity", description:"The Mental Healthcare Act mandates that health insurance policies cover mental illness on the same basis as physical illness. Rejection of mental health claims is legally challengeable.", source:"Ministry of Law & Justice", type:"Document", category:"Claims & Appeals", url:"https://www.indiacode.nic.in/bitstream/123456789/2249/1/201710.pdf", tags:["mental health","insurance parity","mental healthcare act"] },
  { title:"Key Features Document — What Insurers Must Disclose", description:"IRDAI requires insurers to provide a Key Features Document at point of sale. If a restriction wasn't in your KFD, you can challenge its enforcement.", source:"IRDAI", type:"Guide", category:"Policy Basics", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo4152&flag=1", tags:["KFD","disclosure","point of sale","sublimits"] },
  { title:"Health Insurance Portability — Your Rights When Switching", description:"IRDAI portability rules entitle you to credit for waiting periods already served with a previous insurer. Understand your rights before switching policies.", source:"IRDAI", type:"Guide", category:"Policy Basics", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo4152&flag=1", tags:["portability","switching","waiting period credit"] },
  { title:"Free Look Period — 15 Day Cancellation Right", description:"IRDAI mandates a 15-day free look period for annual policies and 30 days for long-term policies. You can cancel and get a refund within this window.", source:"IRDAI", type:"Guide", category:"Policy Basics", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo4152&flag=1", tags:["free look","cancellation","refund","15 days"] },
  { title:"IRDAI Integrated Grievance Management System (IGMS)", description:"Official portal to file and track insurance complaints. If your insurer hasn't resolved your complaint in 15 days, escalate here. Creates an official paper trail.", source:"IRDAI IGMS", type:"Portal", category:"Grievance", url:"https://igms.irda.gov.in/", tags:["IGMS","complaint","grievance","escalation"] },
  { title:"IRDAI Consumer Helpline", description:"Toll-free helpline for insurance grievances: 155255 or 1800 4254 732. Available for guidance on filing complaints and understanding your rights.", source:"IRDAI", type:"Portal", category:"Grievance", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo253&flag=1", tags:["helpline","toll-free","155255","consumer support"] },
  { title:"Grievance Redressal Officers — Insurer Directory", description:"Every insurer must have a designated GRO. IRDAI maintains a directory of GRO contact details. File your written complaint here first before escalating.", source:"IRDAI", type:"Portal", category:"Grievance", url:"https://www.irdai.gov.in/ADMINCMS/cms/frmGeneral_Layout.aspx?page=PageNo253&flag=1", tags:["GRO","grievance officer","first complaint","written"] },
  { title:"Insurance Ombudsman Rules 2017", description:"The legal framework governing Insurance Ombudsman jurisdiction, eligibility, process, and binding awards. Claims up to Rs 50 lakhs are eligible.", source:"Ministry of Finance", type:"Document", category:"Ombudsman", url:"https://cioins.co.in/PDF/Rules2017.pdf", tags:["ombudsman","Rs 50 lakhs","binding award","rules"] },
  { title:"Council for Insurance Ombudsmen — File a Complaint", description:"Official portal to file a complaint before the Insurance Ombudsman. Must be filed within 1 year of insurer's final reply. No court fees involved.", source:"Council for Insurance Ombudsmen", type:"Portal", category:"Ombudsman", url:"https://cioins.co.in/", tags:["ombudsman complaint","file complaint","CIO","free"] },
  { title:"Ombudsman Office Locations — Jurisdiction Map", description:"17 Ombudsman offices across India. Jurisdiction is based on your residential address or the insurer's registered office. Find your relevant office here.", source:"Council for Insurance Ombudsmen", type:"Portal", category:"Ombudsman", url:"https://cioins.co.in/Ombudsman/1", tags:["ombudsman office","jurisdiction","location","17 offices"] },
];

const TYPE_CONFIG: Record<string, { color: string; bg: string; border: string }> = {
  "Document": { color:"#1e5c2e", bg:"#d6eddc", border:"#9dd0aa" },
  "Portal":   { color:"#2d3f7a", bg:"#d8dff5", border:"#9daade" },
  "Guide":    { color:"#7a4e08", bg:"#faecd0", border:"#e0b870" },
  "Circular": { color:"#8c1f14", bg:"#f5d0cc", border:"#e08070" },
};

export default function LearnPage(): JSX.Element {
  const [activeCategory, setActiveCategory] = useState<Category>("All");
  const [search, setSearch] = useState<string>("");

  const filtered = RESOURCES.filter((r) => {
    const matchCat    = activeCategory === "All" || r.category === activeCategory;
    const matchSearch = !search.trim() ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.tags.some(t => t.toLowerCase().includes(search.toLowerCase())) ||
      r.description.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600&display=swap');

        :root {
          --ink: #070c0a; --ink2: #141f1a; --cream: #f2ede4; --cream2: #ede7dc;
          --paper: #e9e3d7; --sage: #1a5228; --sage2: #246b38;
          --sage-pale: #d3ead9; --gold2: #b88a3a;
          --mist: #4e6655; --mist2: #6a8572; --border: #c4bdb0; --border2: #d8d2c8;
          --border3: #e4ddd4; --radius-sm: 3px; --radius: 4px;
          --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
          --shadow: 0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
          --transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }

        body {
          background: var(--cream); color: var(--ink2);
          font-family: 'Outfit', sans-serif; font-weight: 400;
          -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
          text-rendering: optimizeLegibility; overflow-x: hidden;
        }

        body::after {
          content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 9999;
          opacity: 0.022;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        }

        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: var(--cream); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
        ::selection { background: var(--sage-pale); color: var(--sage); }

        .page { min-height: 100vh; padding: 100px 0 120px; }

        /* ── HEADER ── */
        .page-hdr {
          max-width: 1220px; margin: 0 auto; padding: 52px 64px 44px;
          display: flex; justify-content: space-between; align-items: flex-end;
          border-bottom: 1px solid var(--border); position: relative;
        }
        .page-hdr::after {
          content: ''; position: absolute; bottom: -1px; left: 64px; right: 64px; height: 1px;
          background: linear-gradient(90deg, transparent, rgba(26,82,40,0.3), rgba(138,98,37,0.2), rgba(26,82,40,0.3), transparent);
          pointer-events: none;
        }
        .page-eyebrow {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 500;
          letter-spacing: 0.2em; text-transform: uppercase; color: var(--mist2);
          margin-bottom: 14px; display: flex; align-items: center; gap: 12px;
        }
        .page-eyebrow::before { content: ''; width: 20px; height: 1px; background: var(--mist2); display: block; }
        .page-title {
          font-family: 'Cormorant Garamond', serif; font-size: clamp(36px,3.8vw,54px);
          font-weight: 500; line-height: 1.06; color: var(--ink); letter-spacing: -0.01em;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.1s both;
        }
        .page-title em { font-style: italic; color: var(--sage); font-weight: 400; }
        .page-sub {
          font-size: 14px; font-weight: 400; color: var(--mist); max-width: 380px;
          line-height: 1.82; text-align: right;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.2s both;
        }

        /* ── CONTROLS ── */
        .controls {
          max-width: 1220px; margin: 0 auto; padding: 32px 64px 0;
          display: flex; justify-content: space-between; align-items: flex-start;
          gap: 24px; flex-wrap: wrap;
        }
        .controls-left { display: flex; flex-direction: column; gap: 14px; }

        .cat-tabs { display: flex; gap: 2px; flex-wrap: wrap; }
        .cat-tab {
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
          letter-spacing: 0.12em; text-transform: uppercase; padding: 8px 16px;
          background: white; border: 1px solid var(--border); border-radius: var(--radius-sm);
          cursor: pointer; color: var(--mist); transition: var(--transition);
          box-shadow: var(--shadow-sm);
        }
        .cat-tab:hover { color: var(--sage); border-color: var(--sage); background: #f0f8f2; }
        .cat-tab.active {
          background: var(--sage); color: white; border-color: var(--sage);
          box-shadow: 0 2px 8px rgba(26,82,40,0.25);
        }

        .count-label {
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 400;
          letter-spacing: 0.1em; color: var(--mist2);
        }

        .search-wrap { position: relative; }
        .search-wrap::before {
          content: '◎'; position: absolute; left: 14px; top: 50%;
          transform: translateY(-50%); font-size: 12px; color: var(--mist2);
          pointer-events: none;
        }
        .search-input {
          padding: 10px 16px 10px 36px; border: 1px solid var(--border);
          border-radius: var(--radius-sm);
          font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 400;
          color: var(--ink); background: white; outline: none; width: 280px;
          transition: var(--transition); box-shadow: var(--shadow-sm);
        }
        .search-input:focus {
          border-color: var(--sage);
          box-shadow: 0 0 0 3px rgba(26,82,40,0.06);
        }
        .search-input::placeholder { color: #9a9890; }

        /* ── GRID ── */
        .grid {
          max-width: 1220px; margin: 28px auto 0; padding: 0 64px;
          display: grid; grid-template-columns: repeat(3,1fr);
          gap: 2px; background: var(--border); border: 1px solid var(--border);
          border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm);
        }

        .resource-card {
          background: #faf8f4; padding: 26px;
          display: flex; flex-direction: column; gap: 13px;
          transition: background 0.18s ease; text-decoration: none; color: inherit;
          position: relative; overflow: hidden;
        }
        .resource-card::before {
          content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
          background: linear-gradient(90deg, var(--sage), var(--sage2));
          transform: scaleX(0); transition: transform 0.25s ease;
        }
        .resource-card:hover { background: var(--cream); }
        .resource-card:hover::before { transform: scaleX(1); }

        .card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
        .type-badge {
          font-family: 'DM Mono', monospace; font-size: 8.5px; font-weight: 500;
          letter-spacing: 0.1em; text-transform: uppercase; padding: 3px 9px; border-radius: 2px; flex-shrink: 0;
        }
        .source-label {
          font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 400;
          letter-spacing: 0.06em; color: var(--mist2);
        }

        .card-title {
          font-family: 'Cormorant Garamond', serif; font-size: 18px; font-weight: 500;
          line-height: 1.3; color: var(--ink); letter-spacing: -0.005em;
        }
        .card-desc { font-size: 12.5px; font-weight: 400; line-height: 1.78; color: var(--mist); flex: 1; }

        .card-tags { display: flex; flex-wrap: wrap; gap: 4px; }
        .card-tag {
          font-family: 'DM Mono', monospace; font-size: 8.5px; font-weight: 400;
          letter-spacing: 0.06em; padding: 3px 8px; background: var(--paper);
          color: var(--mist2); border-radius: 2px; border: 1px solid var(--border3);
          transition: var(--transition);
        }
        .resource-card:hover .card-tag { background: var(--cream2); }

        .card-footer {
          display: flex; justify-content: space-between; align-items: center;
          margin-top: 4px; padding-top: 12px; border-top: 1px solid #eee8e0;
        }
        .card-link-label {
          font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 500;
          letter-spacing: 0.1em; text-transform: uppercase; color: var(--sage);
        }
        .card-arrow { color: var(--sage); font-size: 13px; transition: transform 0.2s ease; }
        .resource-card:hover .card-arrow { transform: translate(2px,-2px); }

        /* ── EMPTY STATE ── */
        .empty {
          max-width: 1220px; margin: 80px auto; padding: 0 64px; text-align: center;
          font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 400;
          font-style: italic; color: var(--mist);
        }

        /* ── DISCLAIMER ── */
        .disclaimer {
          max-width: 1220px; margin: 0 auto; padding: 22px 64px;
          display: flex; gap: 14px; align-items: flex-start;
          background: var(--paper); border-top: 1px solid var(--border);
        }
        .disc-icon { font-size: 13px; color: var(--mist2); flex-shrink: 0; margin-top: 2px; }
        .disc-text {
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 400;
          letter-spacing: 0.04em; color: var(--mist2); line-height: 1.75;
        }

        /* ── ANIMATIONS ── */
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── RESPONSIVE ── */
        @media (max-width: 900px) {
          .page-hdr, .controls, .grid, .disclaimer { padding-left: 24px; padding-right: 24px; }
          .page-hdr { flex-direction: column; align-items: flex-start; gap: 16px; }
          .page-sub { text-align: left; max-width: 100%; }
          .grid { grid-template-columns: 1fr; }
          .controls { flex-direction: column; align-items: flex-start; }
          .search-input { width: 100%; }
        }
        @media (min-width: 901px) and (max-width: 1100px) {
          .grid { grid-template-columns: 1fr 1fr; }
        }
      `}</style>

      <div className="page">
        <div className="page-hdr">
          <div>
            <div className="page-eyebrow">Insurance Education</div>
            <h1 className="page-title">Learn insurance.<br /><em>From official sources.</em></h1>
          </div>
          <p className="page-sub">
            Curated regulations, guides, and portals from IRDAI, Ministry of Finance,
            and the Council for Insurance Ombudsmen — no blogs, no opinions.
          </p>
        </div>

        <div className="controls">
          <div className="controls-left">
            <div className="cat-tabs">
              {CATEGORIES.map(cat => (
                <button key={cat}
                  className={`cat-tab ${activeCategory === cat ? "active" : ""}`}
                  onClick={() => setActiveCategory(cat)}>
                  {cat}
                </button>
              ))}
            </div>
            <span className="count-label">{filtered.length} resource{filtered.length !== 1 ? "s" : ""}</span>
          </div>
          <div className="search-wrap">
            <input className="search-input" placeholder="Search by topic, keyword..."
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="empty">No resources match your search</div>
        ) : (
          <div className="grid">
            {filtered.map((r, i) => {
              const tc = TYPE_CONFIG[r.type] ?? TYPE_CONFIG["Guide"];
              return (
                <a key={i} href={r.url} target="_blank" rel="noopener noreferrer" className="resource-card">
                  <div className="card-top">
                    <span className="type-badge" style={{ background: tc.bg, color: tc.color, border:`1px solid ${tc.border}` }}>
                      {r.type}
                    </span>
                    <span className="source-label">{r.source}</span>
                  </div>
                  <div className="card-title">{r.title}</div>
                  <p className="card-desc">{r.description}</p>
                  <div className="card-tags">
                    {r.tags.slice(0, 3).map((tag, j) => (
                      <span key={j} className="card-tag">{tag}</span>
                    ))}
                  </div>
                  <div className="card-footer">
                    <span className="card-link-label">View official source</span>
                    <span className="card-arrow">↗</span>
                  </div>
                </a>
              );
            })}
          </div>
        )}

        <div className="disclaimer">
          <span className="disc-icon">◈</span>
          <span className="disc-text">
            All resources link directly to official government and regulatory sources — IRDAI, Ministry of Finance,
            Ministry of Law & Justice, and the Council for Insurance Ombudsmen.
            CareBridge does not host, modify, or summarise these documents. Always refer to the official source for the most current version.
          </span>
        </div>
      </div>
    </>
  );
}