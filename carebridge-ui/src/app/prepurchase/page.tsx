"use client";

import { useState } from "react";
import { analyzePolicy, analyzePolicyFromFile } from "../lib/api";
import { PrePurchaseReport } from "../types/prepurchase";
import ReportChat from "../components/layout/Reportchat";
import type { JSX } from "react";

/* ── risk colour tokens ──────────────────────────────────────────── */
const RISK: Record<string, { bg: string; color: string; border: string; dot: string }> = {
  "High Risk":     { bg: "#f5d0cc", color: "#8c1f14", border: "#e08070", dot: "#c94030" },
  "Moderate Risk": { bg: "#faecd0", color: "#7a4e08", border: "#e0b870", dot: "#c9920e" },
  "Low Risk":      { bg: "#d6eddc", color: "#1e5c2e", border: "#9dd0aa", dot: "#3d8a52" },
  "Not Found":     { bg: "#eeebe4", color: "#7a7870", border: "#c8c2b4", dot: "#a8a498" },
};

const CLAUSE_META: Record<string, { label: string; desc: string }> = {
  waiting_period:             { label: "Waiting Period",        desc: "How long before claims become valid" },
  pre_existing_disease:       { label: "Pre-existing Disease",  desc: "Coverage for conditions diagnosed before policy" },
  room_rent_sublimit:         { label: "Room Rent Sublimit",     desc: "Cap on daily hospital room cost" },
  disease_specific_caps:      { label: "Disease-Specific Caps", desc: "Per-disease limits below sum insured" },
  co_payment:                 { label: "Co-payment",            desc: "Policyholder's share of each claim" },
  exclusions_clarity:         { label: "Exclusions Clarity",    desc: "How clearly exclusions are written" },
  claim_procedure_complexity: { label: "Claim Procedure",       desc: "Steps and timelines for filing claims" },
  sublimits_and_caps:         { label: "Sublimits & Caps",      desc: "Other per-event or per-item limits" },
  restoration_benefit:        { label: "Restoration Benefit",   desc: "Whether exhausted SI is replenished" },
  transparency_of_terms:      { label: "Term Transparency",     desc: "Clarity of overall policy language" },
};

const scoreColor = (s: number) =>
  s >= 80 ? "#1e5c2e" : s >= 55 ? "#7a4e08" : "#8c1f14";

const flagIsTrue = (v: boolean | string[]): boolean =>
  typeof v === "boolean" ? v : Array.isArray(v) && v.length > 0;

export default function PrePurchasePage(): JSX.Element {
  const PROVIDERS = [
    "Niva Bupa",
    "Star Health",
    "Aditya Birla Health Insurance",
    "HDFC ERGO",
    "ICICI Lombard",
    "Care Health Insurance",
    "Reliance General Insurance",
    "Other providers"
  ];
  const [providerId, setProviderId] = useState<string>(PROVIDERS[0]);
  const [policyText, setPolicyText] = useState<string>("");
  const [file,       setFile]       = useState<File | null>(null);
  const [report,     setReport]     = useState<PrePurchaseReport | null>(null);
  const [loading,    setLoading]    = useState<boolean>(false);
  const [error,      setError]      = useState<string | null>(null);
  const [inputMode,  setInputMode]  = useState<"text" | "file">("text");
  const [agentSummary, setAgentSummary] = useState<string>("");
  const [showAllClauses, setShowAllClauses] = useState<boolean>(false);

  const handleAnalyze = async () => {
    setError(null); setReport(null);
    if (providerId !== "Other providers") {
        try {
            const data = await analyzePolicy("", providerId, agentSummary);
            if (data) {
                setReport(data);
                setTimeout(() => window.scrollTo({ top: 680, behavior: "smooth" }), 120);
            }
        } catch {
            setError("Analysis failed. Could not fetch pre-extracted clauses.");
        } finally { setLoading(false); }
        return;
    }

    if (!policyText.trim() && !file) { setError("Paste policy text or upload a document to begin."); return; }
    setLoading(true);
    try {
      const data = file
        ? await analyzePolicyFromFile(file, agentSummary)
        : policyText.trim().length < 100
          ? (() => { setError("Policy text must be at least 100 characters."); setLoading(false); return null; })()
          : await analyzePolicy(policyText, undefined, agentSummary);
      if (data) {
        setReport(data);
        setTimeout(() => window.scrollTo({ top: 680, behavior: "smooth" }), 120);
      }
    } catch {
      setError("Analysis failed. Try pasting cleaner policy text or a higher-quality document.");
    } finally { setLoading(false); }
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600&display=swap');

        :root {
          --ink: #070c0a; --ink2: #141f1a; --cream: #f2ede4; --cream2: #ede7dc;
          --paper: #e9e3d7; --sage: #1a5228; --sage2: #246b38; --sage3: #2f8a48;
          --sage-pale: #d3ead9; --gold: #8a6225; --gold2: #b88a3a;
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
          font-size: 14px; font-weight: 400; color: var(--mist); max-width: 440px;
          line-height: 1.82; text-align: right;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.2s both;
        }

        /* ── INPUT SECTION ── */
        .input-section {
          max-width: 1220px; margin: 0 auto; padding: 52px 64px 0;
          display: grid; grid-template-columns: 1fr 300px; gap: 28px; align-items: start;
        }
        .input-card {
          background: white; border: 1px solid var(--border);
          border-radius: var(--radius); box-shadow: var(--shadow-sm);
          overflow: hidden;
        }
        .input-tabs { display: flex; border-bottom: 1px solid var(--border); }
        .input-tab {
          flex: 1; padding: 16px 24px;
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 500;
          letter-spacing: 0.1em; text-transform: uppercase; border: none;
          background: none; cursor: pointer; color: var(--mist);
          transition: var(--transition); border-bottom: 2.5px solid transparent; margin-bottom: -1px;
          position: relative;
        }
        .input-tab.active { color: var(--sage); border-bottom-color: var(--sage); background: #f5f0e8; }
        .input-body { padding: 28px; }

        textarea {
          width: 100%; height: 240px; padding: 18px;
          border: 1px solid var(--border); border-radius: var(--radius-sm);
          font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 400;
          line-height: 1.78; color: var(--ink); background: var(--cream);
          resize: vertical; outline: none; transition: border-color 0.2s ease;
        }
        textarea:focus { border-color: var(--sage); box-shadow: 0 0 0 3px rgba(26,82,40,0.06); }
        textarea::placeholder { color: #9a9890; }

        .char-count {
          font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 400;
          color: var(--mist2); margin-top: 10px; letter-spacing: 0.06em;
        }

        .file-drop {
          height: 240px; border: 1.5px dashed var(--border); border-radius: var(--radius-sm);
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          gap: 14px; cursor: pointer; transition: var(--transition); padding: 24px; text-align: center;
        }
        .file-drop:hover { border-color: var(--sage); background: #f5f0e8; }
        .file-drop.has-file { border-color: var(--sage); border-style: solid; background: #f0f8f2; }
        .file-drop-icon { font-size: 26px; color: var(--mist); }
        .file-drop-text {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 400;
          letter-spacing: 0.1em; text-transform: uppercase; color: var(--mist);
        }
        .file-drop-sub { font-size: 12px; font-weight: 400; color: var(--mist2); }
        .file-name { font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; color: var(--sage); }
        input[type="file"] { display: none; }

        .analyze-btn {
          width: 100%; padding: 17px; background: var(--sage); color: #dceee0;
          border: 1px solid #2e6b3e; border-radius: var(--radius-sm);
          font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 500;
          letter-spacing: 0.14em; text-transform: uppercase; cursor: pointer;
          transition: var(--transition);
          display: flex; align-items: center; justify-content: center; gap: 10px;
          margin-top: 16px;
          box-shadow: 0 2px 8px rgba(26,82,40,0.2), inset 0 1px 0 rgba(255,255,255,0.07);
          position: relative; overflow: hidden;
        }
        .analyze-btn::before {
          content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
          transition: left 0.4s ease;
        }
        .analyze-btn:hover::before { left: 100%; }
        .analyze-btn:hover:not(:disabled) {
          background: var(--sage2); transform: translateY(-1px);
          box-shadow: 0 5px 18px rgba(26,82,40,0.3);
        }
        .analyze-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .spinner {
          width: 13px; height: 13px;
          border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
          border-radius: 50%; animation: spin 0.7s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .error-msg {
          margin-top: 16px; padding: 13px 18px;
          background: #f5d0cc; border: 1px solid #e08070; border-radius: var(--radius-sm);
          font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 400; color: #8c1f14;
          border-left: 3px solid #c94030;
        }

        /* ── INPUT SIDEBAR ── */
        .sidebar { display: flex; flex-direction: column; gap: 14px; }
        .sidebar-card {
          background: white; border: 1px solid var(--border);
          border-radius: var(--radius); padding: 22px;
          box-shadow: var(--shadow-sm);
        }
        .sidebar-label {
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
          letter-spacing: 0.16em; text-transform: uppercase; color: var(--mist2); margin-bottom: 16px;
        }
        .sidebar-item {
          display: flex; align-items: flex-start; gap: 10px; padding: 7px 0;
          border-bottom: 1px solid #eee8e0;
          font-size: 12.5px; font-weight: 400; color: var(--ink2); line-height: 1.55;
        }
        .sidebar-item:last-child { border-bottom: none; }
        .sidebar-dot {
          width: 4px; height: 4px; border-radius: 50%; background: var(--sage);
          flex-shrink: 0; margin-top: 6px;
        }
        .privacy-card {
          background: var(--ink); border-radius: var(--radius);
          padding: 22px 24px; box-shadow: var(--shadow-sm);
          position: relative; overflow: hidden;
        }
        .privacy-card::before {
          content: ''; position: absolute; inset: 0;
          background: radial-gradient(ellipse at 20% 80%, rgba(26,82,40,0.2) 0%, transparent 60%);
          pointer-events: none;
        }
        .privacy-title {
          font-family: 'Cormorant Garamond', serif; font-size: 18px; font-weight: 500;
          color: #cce8d5; margin-bottom: 10px; position: relative; z-index: 1;
        }
        .privacy-text {
          font-size: 12.5px; font-weight: 400; color: rgba(255,255,255,0.4);
          line-height: 1.75; position: relative; z-index: 1;
        }
        .tips-card {
          background: #f0f8f2; border: 1px solid #9dd0aa;
          border-radius: var(--radius); padding: 20px 22px;
        }
        .tips-title {
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
          letter-spacing: 0.14em; text-transform: uppercase; color: var(--sage); margin-bottom: 12px;
        }
        .tips-item {
          font-size: 12.5px; font-weight: 400; color: #143a1e;
          line-height: 1.65; padding: 6px 0; border-bottom: 1px solid rgba(26,82,40,0.1);
        }
        .tips-item:last-child { border-bottom: none; }

        /* ── RESULTS DIVIDER ── */
        .results-divider {
          max-width: 1220px; margin: 60px auto 0; padding: 0 64px;
          display: flex; align-items: center; gap: 20px;
        }
        .divider-label {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 500;
          letter-spacing: 0.15em; text-transform: uppercase; color: var(--mist); white-space: nowrap;
        }
        .divider-line { flex: 1; height: 1px; background: var(--border); }
        .conf-chip {
          font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 500;
          letter-spacing: 0.1em; text-transform: uppercase; padding: 5px 13px;
          border-radius: 2px; white-space: nowrap;
        }

        /* ── RESULTS GRID ── */
        .results-layout {
          max-width: 1220px; margin: 36px auto 0; padding: 0 64px;
          display: grid; grid-template-columns: 1fr 340px; gap: 22px; align-items: start;
        }
        .results-main { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
        .results-side { display: flex; flex-direction: column; gap: 18px; position: sticky; top: 100px; min-width: 0; }

        /* ── REPORT CARDS ── */
        .rcard {
          background: white; border: 1px solid var(--border);
          border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm);
          transition: box-shadow 0.2s ease;
        }
        .rcard:hover { box-shadow: var(--shadow); }
        .rcard-hdr {
          padding: 14px 26px; border-bottom: 1px solid var(--border);
          display: flex; justify-content: space-between; align-items: center;
          background: #f5f0e8;
        }
        .rcard-title {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 500;
          letter-spacing: 0.13em; text-transform: uppercase; color: #4a5248;
        }
        .rcard-body { padding: 26px; }

        /* ── SCORE CARD ── */
        .score-hero { display: grid; grid-template-columns: 110px 1fr; gap: 28px; align-items: center; }
        .score-ring { width: 110px; height: 110px; position: relative; flex-shrink: 0; }
        .score-ring svg { transform: rotate(-90deg); }
        .score-ring-label {
          position: absolute; inset: 0;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .score-big {
          font-family: 'Cormorant Garamond', serif; font-size: 30px;
          font-weight: 600; line-height: 1;
        }
        .score-sub {
          font-family: 'DM Mono', monospace; font-size: 9px; font-weight: 400;
          letter-spacing: 0.1em; color: var(--mist); margin-top: 3px;
        }
        .score-meta { display: flex; flex-direction: column; gap: 10px; }
        .score-rating {
          font-family: 'Cormorant Garamond', serif; font-size: 32px;
          font-weight: 500; line-height: 1; letter-spacing: -0.01em;
        }
        .score-row {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 400;
          letter-spacing: 0.06em; color: var(--mist);
        }
        .score-summary {
          margin-top: 18px; font-size: 13.5px; font-weight: 400; line-height: 1.82;
          color: var(--ink2); padding-top: 18px; border-top: 1px solid #eee8e0; font-style: italic;
        }
        .score-indicator-note {
          margin-top: 16px; padding: 9px 14px;
          background: #fdf8ec; border: 1px solid #ddd090; border-radius: var(--radius-sm);
          font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.04em;
          color: #7a5c10; line-height: 1.68; border-left: 2px solid #c9a030;
        }

        /* ── CLAUSE HEATMAP ── */
        .clause-grid { display: grid; grid-template-columns: 1fr 1fr; }
        .clause-cell {
          padding: 15px 22px; display: flex; justify-content: space-between;
          align-items: flex-start; gap: 12px; border-bottom: 1px solid #eee8e0;
          transition: background 0.15s ease;
        }
        .clause-cell:hover { background: #faf7f2; }
        .clause-cell:nth-last-child(-n+2) { border-bottom: none; }
        .clause-cell:nth-child(even) { border-left: 1px solid #eee8e0; }
        .clause-name { font-size: 12.5px; font-weight: 400; color: var(--ink2); line-height: 1.35; }
        .clause-desc { font-size: 11px; font-weight: 400; color: var(--mist); margin-top: 3px; line-height: 1.4; }
        .clause-badge {
          font-family: 'DM Mono', monospace; font-size: 8.5px; font-weight: 500;
          letter-spacing: 0.08em; text-transform: uppercase; padding: 4px 10px;
          border-radius: 2px; white-space: nowrap; flex-shrink: 0; margin-top: 2px;
        }
        .clause-summary { display: flex; gap: 0; border-top: 1px solid #eee8e0; }
        .clause-summary-seg {
          flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;
          padding: 14px 8px; border-right: 1px solid #eee8e0;
        }
        .clause-summary-seg:last-child { border-right: none; }
        .clause-summary-count {
          font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 600; line-height: 1;
        }
        .clause-summary-label {
          font-family: 'DM Mono', monospace; font-size: 8.5px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase;
        }

        /* ── IRDAI COMPLIANCE ── */
        .compliance-bar-wrap { margin-bottom: 18px; }
        .bar-label {
          display: flex; justify-content: space-between;
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
          letter-spacing: 0.08em; color: var(--mist); margin-bottom: 8px;
        }
        .bar-track { height: 6px; background: #eee8e0; border-radius: 4px; overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 4px; transition: width 0.9s cubic-bezier(0.4,0,0.2,1); }
        .compliance-flags {
          display: flex; flex-direction: column; gap: 1px;
          background: #eee8e0; border: 1px solid #eee8e0; border-radius: var(--radius-sm);
          overflow: hidden; margin-top: 6px;
        }
        .compliance-row {
          background: white; padding: 11px 18px;
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          transition: background 0.15s;
        }
        .compliance-row:hover { background: #faf7f2; }
        .compliance-key { font-size: 12.5px; font-weight: 400; color: var(--ink2); }
        .compliance-val { font-family: 'DM Mono', monospace; font-size: 13px; font-weight: 500; }

        /* ── BROKER RISK ── */
        .broker-bars { display: flex; flex-direction: column; gap: 16px; }
        .broker-counts {
          display: flex; gap: 0; border: 1px solid #eee8e0; border-radius: var(--radius-sm);
          overflow: hidden; margin-bottom: 16px;
        }
        .broker-count-seg { flex: 1; padding: 12px 16px; display: flex; flex-direction: column; gap: 3px; }
        .broker-count-seg + .broker-count-seg { border-left: 1px solid #eee8e0; }
        .broker-count-num {
          font-family: 'Cormorant Garamond', serif; font-size: 24px; font-weight: 600; line-height: 1;
        }
        .broker-count-lbl {
          font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.08em;
          text-transform: uppercase; color: var(--mist);
        }
        .broker-reco {
          margin-top: 18px; padding-top: 16px; border-top: 1px solid #eee8e0;
          font-size: 13.5px; font-weight: 400; color: var(--ink2); line-height: 1.78; font-style: italic;
        }
        .broker-insufficient {
          margin-bottom: 14px; padding: 10px 14px;
          background: #faecd0; border: 1px solid #e0b870; border-radius: var(--radius-sm);
          font-family: 'DM Mono', monospace; font-size: 9.5px; letter-spacing: 0.04em;
          color: #7a4e08; line-height: 1.65; border-left: 2px solid #c9920e;
        }

        /* ── FLAGS ── */
        .flags-list { display: flex; flex-direction: column; }
        .flag-item {
          display: flex; gap: 12px; align-items: flex-start; padding: 12px 20px;
          border-bottom: 1px solid #eee8e0;
          font-size: 12.5px; font-weight: 400; color: var(--ink2); line-height: 1.55;
          transition: background 0.15s;
        }
        .flag-item:hover { background: #faf7f2; }
        .flag-item:last-child { border-bottom: none; }
        .flag-icon { flex-shrink: 0; font-size: 10px; margin-top: 3px; }

        /* ── LOW CONFIDENCE ── */
        .low-conf {
          padding: 16px 22px; background: #faecd0; border: 1px solid #e0b870;
          border-radius: var(--radius-sm); border-left: 3px solid #c9920e;
          display: flex; gap: 14px; align-items: flex-start;
          font-size: 13.5px; font-weight: 400; color: #5a3808; line-height: 1.68;
        }

        /* ── DARK SUMMARY ── */
        .dark-summary {
          background: var(--ink); border-radius: var(--radius); padding: 22px;
          box-shadow: var(--shadow-sm); position: relative; overflow: hidden;
        }
        .dark-summary::before {
          content: ''; position: absolute; inset: 0;
          background: radial-gradient(ellipse at 20% 80%, rgba(26,82,40,0.15) 0%, transparent 55%);
          pointer-events: none;
        }
        .dark-summary-label {
          font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
          letter-spacing: 0.14em; text-transform: uppercase; color: rgba(255,255,255,0.28);
          margin-bottom: 16px; position: relative; z-index: 1;
        }
        .dark-summary-row {
          padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.07);
          display: flex; justify-content: space-between; align-items: center; gap: 8px;
          position: relative; z-index: 1;
        }
        .dark-summary-row:last-child { border-bottom: none; }
        .dark-summary-key { font-size: 12.5px; font-weight: 400; color: rgba(255,255,255,0.4); }
        .dark-summary-val {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 500;
          color: #ddeee2; letter-spacing: 0.04em; text-align: right;
        }

        /* ── CHECKLIST ── */
        .checklist-card {
          background: white; border: 1px solid var(--border);
          border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm);
        }
        .checklist-hdr { padding: 14px 22px; border-bottom: 1px solid var(--border); background: #f5f0e8; }
        .checklist-hdr-label {
          font-family: 'DM Mono', monospace; font-size: 10.5px; font-weight: 500;
          letter-spacing: 0.13em; text-transform: uppercase; color: #4a5248;
        }
        .checklist-item {
          display: flex; gap: 14px; align-items: flex-start; padding: 12px 22px;
          border-bottom: 1px solid #eee8e0;
          font-size: 12.5px; font-weight: 400; color: var(--ink2); line-height: 1.55;
          transition: background 0.15s;
        }
        .checklist-item:hover { background: #faf7f2; }
        .checklist-item:last-child { border-bottom: none; }
        .check-icon { flex-shrink: 0; color: var(--sage); font-size: 11px; font-weight: 600; margin-top: 1px; }

        /* ── FOOTNOTE ── */
        .report-fn {
          max-width: 1220px; margin: 36px auto 0; padding: 18px 64px 40px;
          font-family: 'DM Mono', monospace; font-size: 9.5px; font-weight: 400;
          color: var(--mist2); letter-spacing: 0.05em; text-align: center; line-height: 2;
          border-top: 1px solid var(--border3);
        }
        .report-fn strong { color: #3a4038; letter-spacing: 0.08em; }

        /* ── ANIMATIONS ── */
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── RESPONSIVE ── */
        @media (max-width: 900px) {
          .page-hdr, .input-section, .results-divider, .results-layout, .report-fn { padding-left: 24px; padding-right: 24px; }
          .page-hdr { flex-direction: column; align-items: flex-start; gap: 16px; }
          .page-sub { text-align: left; max-width: 100%; }
          .input-section, .results-layout { grid-template-columns: 1fr; }
          .clause-grid { grid-template-columns: 1fr; }
          .clause-cell:nth-child(even) { border-left: none; }
          .clause-cell:nth-last-child(-n+2) { border-bottom: 1px solid #eee8e0; }
          .clause-cell:last-child { border-bottom: none; }
          .results-side { position: static; }
          .score-hero { grid-template-columns: 1fr; }
        }
      `}</style>

      <div className="page">

        {/* ── HEADER ── */}
        <div className="page-hdr">
          <div>
            <div className="page-eyebrow">Pre-Purchase Analysis</div>
            <h1 className="page-title">Read the fine print.<br /><em>Before you sign.</em></h1>
          </div>
          <p className="page-sub">
            Paste policy wording or upload a document. CareBridge classifies
            10 risk clauses, evaluates IRDAI compliance, and scores structural
            risk — clause by clause.
          </p>
        </div>

        {/* ── INPUT ── */}
        <div className="input-section">
          <div className="input-card">
            <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border)", background: "#f5f0e8" }}>
                <label style={{ fontFamily: "DM Mono", fontSize: 10.5, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--mist)", display: "block", marginBottom: 8 }}>Select Insurance Provider</label>
                <select 
                    value={providerId} 
                    onChange={e => setProviderId(e.target.value)}
                    style={{ width: "100%", padding: "12px", borderRadius: "4px", border: "1px solid var(--border)", fontSize: "14px", outline: "none", cursor: "pointer", fontFamily: "Outfit" }}
                >
                    {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
            </div>

            {providerId === "Other providers" ? (
                <>
                <div className="input-tabs">
                {(["text", "file"] as const).map(mode => (
                    <button key={mode} className={`input-tab ${inputMode === mode ? "active" : ""}`}
                    onClick={() => setInputMode(mode)}>
                    {mode === "text" ? "Paste Text" : "Upload Document"}
                    </button>
                ))}
                </div>
                <div className="input-body">
                {inputMode === "text" ? (
                    <>
                    <textarea
                        placeholder="Paste policy wording here — include sections on waiting periods, exclusions, sublimits, co-payment, and claim procedures for best results..."
                        value={policyText}
                        onChange={e => { setPolicyText(e.target.value); setFile(null); }}
                    />
                    <div className="char-count">{policyText.length.toLocaleString()} characters · min 100 required</div>
                    </>
                ) : (
                    <>
                    <label htmlFor="fileUpload" className={`file-drop ${file ? "has-file" : ""}`}>
                        {file ? (
                        <>
                            <span className="file-drop-icon" style={{ color: "var(--sage)" }}>✓</span>
                            <span className="file-name">{file.name}</span>
                            <span className="file-drop-sub">{(file.size / 1024).toFixed(0)} KB · click to change</span>
                        </>
                        ) : (
                        <>
                            <span className="file-drop-icon">⬆</span>
                            <span className="file-drop-text">Drop file or click to upload</span>
                            <span className="file-drop-sub">PDF · PNG · JPG · TXT — max 10 MB</span>
                        </>
                        )}
                    </label>
                    <input id="fileUpload" type="file" accept=".pdf,.jpg,.jpeg,.png,.txt"
                        onChange={e => { const f = e.target.files?.[0]; if (f) { setFile(f); setPolicyText(""); } }} />
                    </>
                )}
                </div>
                </>
            ) : (
                <div className="input-body">
                    <div style={{ textAlign: "center", padding: "10px 0 20px", color: "var(--mist)", fontSize: 13, lineHeight: 1.6 }}>
                        We have already thoroughly analyzed this provider's standard policy.<br/>
                        <b>100% accurate clauses</b> are pre-loaded for instant analysis.
                    </div>
                </div>
            )}

            <div style={{ padding: "0 28px 20px" }}>
                <label style={{ fontFamily: "DM Mono", fontSize: 10, fontWeight: 500, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--mist2)", display: "block", marginBottom: 8 }}>Agent's Summary / Promises (Optional)</label>
                <textarea 
                    placeholder="Enter what your agent told you... e.g. 'No waiting period', 'Covers everything from day 1', etc."
                    value={agentSummary}
                    onChange={e => setAgentSummary(e.target.value)}
                    style={{ height: "80px", marginBottom: "0" }}
                />
            </div>
              <div style={{ padding: "0 28px 28px" }}>
                  <button className="analyze-btn" onClick={handleAnalyze} disabled={loading} style={{ marginTop: 0 }}>
                    {loading ? <><span className="spinner" />Analysing policy...</> : "Run Policy Analysis"}
                  </button>
                  {error && <div className="error-msg">{error}</div>}
              </div>
          </div>

          <div className="sidebar">
            <div className="sidebar-card">
              <div className="sidebar-label">10 Clauses Analysed</div>
              {Object.values(CLAUSE_META).map((c, i) => (
                <div key={i} className="sidebar-item"><span className="sidebar-dot" />{c.label}</div>
              ))}
            </div>
            <div className="tips-card">
              <div className="tips-title">For best results</div>
              {[
                "Include the full policy schedule and benefit table",
                "Paste exclusions and waiting period sections",
                "Add co-payment and room rent clauses if available",
              ].map((t, i) => <div key={i} className="tips-item">{t}</div>)}
            </div>
            <div className="privacy-card">
              <div className="privacy-title">Privacy first</div>
              <p className="privacy-text">Your document is analysed in memory and never stored. Results are generated locally using an on-device model.</p>
            </div>
          </div>
        </div>

        {/* ── RESULTS ── */}
        {report && (
          <>
            <div className="results-divider">
              <span className="divider-label">Analysis Report</span>
              <span className="divider-line" />
              <span className="conf-chip" style={{
                background: report.confidence === "High" ? "#d6eddc" : report.confidence === "Low" ? "#f5d0cc" : "#faecd0",
                color:      report.confidence === "High" ? "#1e5c2e" : report.confidence === "Low" ? "#8c1f14" : "#7a4e08",
              }}>Confidence: {report.confidence}</span>
            </div>

            <div className="results-layout">
              <div className="results-main">
                {report.confidence === "Low" && (
                  <div className="low-conf">
                    <span style={{ fontSize: 15, flexShrink: 0, marginTop: 1 }}>⚠</span>
                    <span>Low confidence — submitted text may be insufficient. Include full clause sections for a complete analysis.</span>
                  </div>
                )}

                <div className="rcard" style={{ border: report.score_breakdown.adjusted_score >= 80 ? "1px solid #9dd0aa" : report.score_breakdown.adjusted_score >= 55 ? "1px solid #e0b870" : "1px solid #e08070", background: "white", marginBottom: "20px" }}>
                  <div className="rcard-body" style={{ padding: "32px", textAlign: "center" }}>
                    <div className="page-eyebrow" style={{ justifyContent: "center", marginBottom: "16px" }}>Final Verdict</div>
                    <h2 className="page-title" style={{ fontSize: "42px", marginBottom: "12px", color: scoreColor(report.score_breakdown.adjusted_score) }}>
                      {report.score_breakdown.adjusted_score >= 80 ? "Proceed with Confidence" : 
                       report.score_breakdown.adjusted_score >= 55 ? "Proceed with Caution" : "Avoid or Re-negotiate"}
                    </h2>
                    <p style={{ fontSize: "16px", color: "var(--mist)", maxWidth: "600px", margin: "0 auto 24px" }}>
                      {report.summary}
                    </p>
                    <div style={{ display: "flex", justifyContent: "center", gap: "12px" }}>
                      <span className="conf-chip" style={{ background: "var(--paper)", color: "var(--sage)", fontSize: "11px" }}>Confidence: {report.confidence}</span>
                      <span className="conf-chip" style={{ background: "var(--paper)", color: "var(--gold)", fontSize: "11px" }}>Compliance: {report.irdai_compliance.compliance_rating}</span>
                    </div>
                  </div>
                </div>

                <ReportChat reportData={report} context="prepurchase" />

                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">Policy Assessment</span>
                    <span className="rcard-title">{Math.round(report.score_breakdown.adjusted_score)} / 100</span>
                  </div>
                  <div className="rcard-body">
                    <div className="score-hero">
                      <div className="score-ring">
                        <svg width="110" height="110" viewBox="0 0 110 110">
                          <circle cx="55" cy="55" r="46" fill="none" stroke="#eee8e0" strokeWidth="9" />
                          <circle cx="55" cy="55" r="46" fill="none"
                            stroke={scoreColor(report.score_breakdown.adjusted_score)}
                            strokeWidth="9" strokeLinecap="round"
                            strokeDasharray={`${2 * Math.PI * 46}`}
                            strokeDashoffset={`${2 * Math.PI * 46 * (1 - report.score_breakdown.adjusted_score / 100)}`}
                            style={{ transition: "stroke-dashoffset 1s ease" }}
                          />
                        </svg>
                        <div className="score-ring-label">
                          <span className="score-big" style={{ color: scoreColor(report.score_breakdown.adjusted_score) }}>
                            {Math.round(report.score_breakdown.adjusted_score)}
                          </span>
                          <span className="score-sub">/ 100</span>
                        </div>
                      </div>
                      <div className="score-meta">
                        <div className="score-rating" style={{ color: scoreColor(report.score_breakdown.adjusted_score) }}>
                          {report.overall_policy_rating}
                        </div>
                        <div className="score-row">Risk index · {typeof report.score_breakdown.risk_index === "number" ? report.score_breakdown.risk_index.toFixed(2) : report.score_breakdown.risk_index}</div>
                        <div className="score-row">Confidence · {report.confidence}</div>
                      </div>
                    </div>
                    <div className="score-indicator-note">
                      ⚠ Indicative assessment based on submitted text only — not an endorsement or guarantee of coverage.
                      Verify clause details directly with your insurer before purchasing.
                    </div>
                    {report.summary && <p className="score-summary">{report.summary}</p>}
                  </div>
                </div>



                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">Clause Risk Assessment</span>
                    <span className="rcard-title">10 clauses</span>
                  </div>
                  {(() => {
                    const counts = { "High Risk": 0, "Moderate Risk": 0, "Low Risk": 0, "Not Found": 0 };
                    Object.values(report.clause_risk).forEach(v => { if (v in counts) counts[v as keyof typeof counts]++; });
                    return (
                      <div className="clause-summary">
                        {(["High Risk", "Moderate Risk", "Low Risk", "Not Found"] as const).map(lbl => (
                          <div key={lbl} className="clause-summary-seg">
                            <span className="clause-summary-count" style={{ color: RISK[lbl].color }}>{counts[lbl]}</span>
                            <span className="clause-summary-label" style={{ color: RISK[lbl].color }}>
                              {lbl === "Not Found" ? "N/F" : lbl.replace(" Risk", "")}
                            </span>
                          </div>
                        ))}
                      </div>
                    );
                  })()}
                  <div className="clause-grid">
                    {Object.entries(report.clause_risk)
                      .slice(0, showAllClauses ? undefined : 4)
                      .map(([key, value]) => {
                      const cfg  = RISK[value] || RISK["Not Found"];
                      const meta = CLAUSE_META[key];
                      return (
                        <div key={key} className="clause-cell">
                          <div>
                            <div className="clause-name">{meta?.label || key}</div>
                            <div className="clause-desc">{meta?.desc}</div>
                          </div>
                          <span className="clause-badge" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
                            {value}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  {Object.keys(report.clause_risk).length > 4 && (
                    <button 
                      onClick={() => setShowAllClauses(!showAllClauses)}
                      style={{ width: "100%", padding: "12px", background: "#f5f0e8", border: "none", borderTop: "1px solid #eee8e0", fontFamily: "DM Mono", fontSize: "10px", color: "var(--mist)", cursor: "pointer", textTransform: "uppercase", letterSpacing: "0.1em" }}
                    >
                      {showAllClauses ? "↑ Show Fewer Clauses" : "↓ Show All 10 Clauses"}
                    </button>
                  )}
                </div>

                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">IRDAI Compliance</span>
                    <span className="rcard-title" style={{ color: "#1e5c2e" }}>{report.irdai_compliance.compliance_rating}</span>
                  </div>
                  <div className="rcard-body">
                    <div className="compliance-bar-wrap">
                      <div className="bar-label">
                        <span>Compliance Score</span>
                        <span>{report.irdai_compliance.compliance_score} / 7</span>
                      </div>
                      <div className="bar-track">
                        <div className="bar-fill" style={{ width: `${(report.irdai_compliance.compliance_score / 7) * 100}%`, background: "var(--sage)" }} />
                      </div>
                    </div>
                    <div className="compliance-flags">
                      {Object.entries(report.irdai_compliance.compliance_flags)
                        .filter(([k]) => !k.startsWith("_"))
                        .map(([k, v]) => {
                          const passed = flagIsTrue(v);
                          return (
                            <div key={k} className="compliance-row">
                              <span className="compliance-key">{k.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</span>
                              <span className="compliance-val" style={{ color: passed ? "#1e5c2e" : "#8c1f14" }}>{passed ? "✓" : "✗"}</span>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                </div>
                
                {report.agent_validation && (
                  <div className="rcard">
                    <div className="rcard-hdr">
                      <span className="rcard-title">Verification Report</span>
                      <span className="rcard-title" style={{ color: report.agent_validation.trust_score < 70 ? "#8c1f14" : "#1e5c2e" }}>
                        Trust Score: {Math.round(report.agent_validation.trust_score)}%
                      </span>
                    </div>
                    <div className="rcard-body" style={{ padding: 0 }}>
                      <div style={{ padding: "18px 26px", borderBottom: "1px solid #eee8e0", fontSize: "13.5px", lineHeight: "1.7", color: "var(--ink2)" }}>
                        {report.agent_validation.is_consistent 
                          ? "The agent's summary is largely consistent with the policy wording and IRDAI regulations."
                          : "Multiple discrepancies found between the agent's claims and the actual policy clauses."}
                      </div>
                      
                      {report.agent_validation.discrepancies.length > 0 && (
                        <div style={{ background: "#fff5f5" }}>
                          <div style={{ padding: "10px 26px", fontSize: "9px", fontFamily: "DM Mono", textTransform: "uppercase", letterSpacing: "0.14em", color: "#8c1f14", borderBottom: "1px solid #f5d0cc", opacity: 0.7 }}>Discrepancy Analysis</div>
                          {report.agent_validation.discrepancies.map((c, i) => (
                            <div key={i} style={{ padding: "20px 26px", borderBottom: "1px solid #f5d0cc" }}>
                              <div style={{ fontSize: "14px", fontWeight: 600, color: "#8c1f14", marginBottom: "6px" }}>Claim: "{c.claim}"</div>
                              <div style={{ fontSize: "13px", color: "#5a1a14", lineHeight: "1.6" }}><b>Fact:</b> {c.fact_check}</div>
                              {c.citation && <div style={{ fontSize: "10px", marginTop: "10px", color: "#8c1f14", opacity: 0.6, fontFamily: "DM Mono", textTransform: "uppercase" }}>Ref: {c.citation}</div>}
                            </div>
                          ))}
                        </div>
                      )}

                      {report.agent_validation.verified_claims.length > 0 && (
                        <div style={{ background: "#f8fbf9" }}>
                          <div style={{ padding: "10px 26px", fontSize: "9px", fontFamily: "DM Mono", textTransform: "uppercase", letterSpacing: "0.14em", color: "var(--sage)", borderBottom: "1px solid #d6eddc", opacity: 0.7 }}>Verified Assertions</div>
                          {report.agent_validation.verified_claims.map((c, i) => (
                            <div key={i} style={{ padding: "20px 26px", borderBottom: "1px solid #d6eddc" }}>
                              <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sage)", marginBottom: "6px" }}>Claim: "{c.claim}"</div>
                              <div style={{ fontSize: "13px", color: "#1a4a26", lineHeight: "1.6" }}><b>Verification:</b> {c.fact_check}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {(report.red_flags.length > 0 || report.positive_flags.length > 0) && (
                  <div className="rcard">
                    <div className="rcard-hdr">
                      <span className="rcard-title">Risk Signals</span>
                      <span className="rcard-title">{report.red_flags.length + report.positive_flags.length} signals</span>
                    </div>
                    <div className="flags-list">
                      {report.red_flags.map((f, i) => (
                        <div key={`r${i}`} className="flag-item">
                          <span className="flag-icon" style={{ color: "#8c1f14" }}>▲</span>{f}
                        </div>
                      ))}
                      {report.positive_flags.map((f, i) => (
                        <div key={`p${i}`} className="flag-item">
                          <span className="flag-icon" style={{ color: "#1e5c2e" }}>◆</span>{f}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {report.regulatory_citations && report.regulatory_citations.length > 0 && (
                  <div className="rcard" style={{ borderStyle: "dashed" }}>
                    <div className="rcard-hdr" style={{ background: "transparent" }}>
                      <span className="rcard-title">Regulatory References</span>
                      <span className="rcard-title">IRDAI GUIDELINES</span>
                    </div>
                    <div className="rcard-body">
                      {report.regulatory_citations.map((cite, idx) => (
                        <div key={idx} style={{ display: "flex", gap: "12px", marginBottom: idx === report.regulatory_citations.length - 1 ? 0 : "12px", fontSize: "12px", color: "var(--mist)", lineHeight: "1.5" }}>
                          <span style={{ color: "var(--sage2)", fontWeight: "600" }}>§</span>
                          {cite}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="results-side">
                <div className="dark-summary">
                  <div className="dark-summary-label">Score Summary</div>
                  {[
                    { label: "Overall Rating",   value: report.overall_policy_rating },
                    { label: "Adjusted Score",   value: `${Math.round(report.score_breakdown.adjusted_score)} / 100` },
                    { label: "Risk Index",       value: typeof report.score_breakdown.risk_index === "number" ? report.score_breakdown.risk_index.toFixed(2) : String(report.score_breakdown.risk_index) },
                    { label: "IRDAI Compliance", value: `${report.irdai_compliance.compliance_score} / 7` },
                    { label: "Confidence",       value: report.confidence },
                  ].map(({ label, value }) => (
                    <div key={label} className="dark-summary-row">
                      <span className="dark-summary-key">{label}</span>
                      <span className="dark-summary-val">{value}</span>
                    </div>
                  ))}
                </div>

                <div className="rcard">
                  <div className="rcard-hdr">
                    <span className="rcard-title">Structural Risk</span>
                    <span className="rcard-title" style={{
                      color: report.broker_risk_analysis.structural_risk_level === "High"     ? "#8c1f14"
                           : report.broker_risk_analysis.structural_risk_level === "Elevated" ? "#7a4e08"
                           : report.broker_risk_analysis.structural_risk_level === "Insufficient Data" ? "#7a7870"
                           : "#1e5c2e",
                    }}>{report.broker_risk_analysis.structural_risk_level}</span>
                  </div>
                  <div className="rcard-body">
                    {!report.broker_risk_analysis.data_sufficient && (
                      <div className="broker-insufficient">
                        ⚠ Insufficient data — structural risk assessment is based on partial clause coverage.
                        Add more policy sections for a complete picture.
                      </div>
                    )}
                    <div className="broker-counts">
                      <div className="broker-count-seg">
                        <span className="broker-count-num" style={{ color: "#8c1f14" }}>{report.broker_risk_analysis.high_risk_count}</span>
                        <span className="broker-count-lbl">High risk clauses</span>
                      </div>
                      <div className="broker-count-seg">
                        <span className="broker-count-num" style={{ color: "#7a7870" }}>{report.broker_risk_analysis.not_found_count}</span>
                        <span className="broker-count-lbl">Clauses not found</span>
                      </div>
                    </div>
                    <div className="broker-bars">
                      <div>
                        <div className="bar-label">
                          <span>Risk Density</span>
                          <span>{(report.broker_risk_analysis.risk_density_index * 100).toFixed(0)}%</span>
                        </div>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${report.broker_risk_analysis.risk_density_index * 100}%`, background: "#c94030" }} />
                        </div>
                      </div>
                      <div>
                        <div className="bar-label">
                          <span>Transparency</span>
                          <span>{report.broker_risk_analysis.transparency_score}%</span>
                        </div>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${report.broker_risk_analysis.transparency_score}%`, background: "var(--sage)" }} />
                        </div>
                      </div>
                    </div>
                    {report.broker_risk_analysis.recommendation && (
                      <p className="broker-reco">{report.broker_risk_analysis.recommendation}</p>
                    )}
                  </div>
                </div>

                {report.checklist_for_buyer.length > 0 && (
                  <div className="checklist-card">
                    <div className="checklist-hdr">
                      <div className="checklist-hdr-label">Before You Buy</div>
                    </div>
                    {report.checklist_for_buyer.map((q, i) => (
                      <div key={i} className="checklist-item">
                        <span className="check-icon">→</span>{q}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <p className="report-fn">
              <strong>CareBridge provides interpretative analysis only.</strong><br />
              Not legal advice · Not an insurance endorsement · Scores are indicative, not guarantees of coverage.<br />
              Verify all findings with your insurer or a qualified advisor before purchasing a policy.
            </p>
          </>
        )}
      </div>
    </>
  );
}