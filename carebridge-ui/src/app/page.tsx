"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";

export default function Home(): React.ReactElement {
  const [mounted, setMounted] = useState<boolean>(true);
  const [scrollY, setScrollY] = useState<number>(0);
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500;1,600&family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600&display=swap');

        :root {
          --ink: #070c0a;
          --ink2: #141f1a;
          --cream: #f2ede4;
          --cream2: #ede7dc;
          --paper: #e9e3d7;
          --sage: #1a5228;
          --sage2: #246b38;
          --sage3: #2f8a48;
          --sage-pale: #d3ead9;
          --sage-glow: rgba(26,82,40,0.15);
          --gold: #8a6225;
          --gold2: #b88a3a;
          --mist: #4e6655;
          --mist2: #6a8572;
          --border: #c4bdb0;
          --border2: #d8d2c8;
          --border3: #e4ddd4;
          --white-5: rgba(255,255,255,0.05);
          --white-8: rgba(255,255,255,0.08);
          --white-12: rgba(255,255,255,0.12);
          --white-20: rgba(255,255,255,0.20);
          --white-30: rgba(255,255,255,0.30);
          --white-45: rgba(255,255,255,0.45);
          --radius-sm: 3px;
          --radius: 4px;
          --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
          --shadow: 0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
          --shadow-lg: 0 20px 60px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.08);
          --transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
        }

        *, *::before, *::after {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }

        html { scroll-behavior: smooth; }

        body {
          background: var(--cream);
          color: var(--ink2);
          font-family: 'Outfit', sans-serif;
          font-weight: 400;
          overflow-x: hidden;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
          text-rendering: optimizeLegibility;
        }

        /* ─── NOISE TEXTURE OVERLAY ─── */
        body::after {
          content: '';
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 9999;
          opacity: 0.025;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        }

        /* ─── SCROLLBAR ─── */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: var(--cream); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--mist2); }

        /* ─── SELECTION ─── */
        ::selection { background: var(--sage-pale); color: var(--sage); }

        /* ══════════════════════════════════════════
           NAV
        ══════════════════════════════════════════ */
        .nav {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 100;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0 52px;
          height: 68px;
          background: rgba(7,12,10,0.92);
          backdrop-filter: blur(24px) saturate(180%);
          -webkit-backdrop-filter: blur(24px) saturate(180%);
          border-bottom: 1px solid rgba(46,122,68,0.25);
          transition: height 0.3s cubic-bezier(0.4,0,0.2,1), background 0.3s ease;
        }

        .nav::before {
          content: '';
          position: absolute;
          bottom: 0;
          left: 52px;
          right: 52px;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(46,122,68,0.4), rgba(154,112,48,0.3), rgba(46,122,68,0.4), transparent);
          pointer-events: none;
        }

        .nav-logo {
          font-family: 'Cormorant Garamond', serif;
          font-size: 21px;
          font-weight: 600;
          letter-spacing: 0.04em;
          color: #cee8d6;
          text-decoration: none;
          transition: opacity 0.2s;
          position: relative;
        }
        .nav-logo:hover { opacity: 0.85; }
        .nav-logo span { color: #52a06a; }

        .nav-logo::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          width: 0;
          height: 1px;
          background: #52a06a;
          transition: width 0.3s ease;
        }
        .nav-logo:hover::after { width: 100%; }

        .nav-links {
          display: flex;
          gap: 34px;
          align-items: center;
          list-style: none;
        }

        .nav-links a {
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 400;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: #6a9e7a;
          text-decoration: none;
          transition: color 0.2s ease;
          position: relative;
        }

        .nav-links a::after {
          content: '';
          position: absolute;
          bottom: -3px;
          left: 0;
          width: 0;
          height: 1px;
          background: currentColor;
          transition: width 0.25s ease;
        }
        .nav-links a:hover::after { width: 100%; }
        .nav-links a:hover { color: #d0e8d8; }

        .nav-cta {
          background: var(--sage) !important;
          color: #dceee0 !important;
          padding: 9px 20px !important;
          border-radius: var(--radius-sm) !important;
          border: 1px solid #2e6b3e !important;
          transition: var(--transition) !important;
          box-shadow: 0 1px 3px rgba(26,82,40,0.3), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        }
        .nav-cta::after { display: none !important; }
        .nav-cta:hover {
          background: var(--sage2) !important;
          transform: translateY(-1px) !important;
          box-shadow: 0 4px 12px rgba(26,82,40,0.35), inset 0 1px 0 rgba(255,255,255,0.08) !important;
        }
        .nav-cta:active { transform: translateY(0) !important; }

        .nav-help {
          color: #c0a040 !important;
          border-bottom: 1px solid rgba(192,160,64,0.3) !important;
          padding-bottom: 1px !important;
        }
        .nav-help::after { display: none !important; }
        .nav-help:hover {
          color: #e0cc70 !important;
          border-color: rgba(192,160,64,0.7) !important;
        }

        /* ══════════════════════════════════════════
           HERO
        ══════════════════════════════════════════ */
        .hero {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 1fr 1fr;
          position: relative;
          overflow: hidden;
        }

        .hero-left {
          padding: 155px 70px 85px 64px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          background: var(--cream);
          position: relative;
          z-index: 1;
        }

        /* Subtle grid lines on hero left */
        .hero-left::before {
          content: '';
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(rgba(0,0,0,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,0,0,0.025) 1px, transparent 1px);
          background-size: 48px 48px;
          pointer-events: none;
        }

        .hero-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--sage);
          margin-bottom: 30px;
          display: flex;
          align-items: center;
          gap: 14px;
          position: relative;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.1s both;
        }

        .hero-eyebrow::before {
          content: '';
          display: block;
          width: 36px;
          height: 1.5px;
          background: linear-gradient(90deg, var(--sage), var(--sage2));
          flex-shrink: 0;
        }

        .hero-h1 {
          font-family: 'Cormorant Garamond', serif;
          font-size: clamp(50px, 5.2vw, 80px);
          font-weight: 500;
          line-height: 1.05;
          letter-spacing: -0.015em;
          color: var(--ink);
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.2s both;
        }

        .hero-h1 em {
          font-style: italic;
          color: var(--sage);
          font-weight: 400;
        }

        .hero-sub {
          margin-top: 26px;
          font-size: 15.5px;
          font-weight: 400;
          line-height: 1.82;
          color: var(--mist);
          max-width: 450px;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.3s both;
        }

        .hero-actions {
          margin-top: 48px;
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.4s both;
        }

        .btn-primary {
          background: var(--sage);
          color: #dceee0;
          padding: 15px 34px;
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          text-decoration: none;
          border-radius: var(--radius-sm);
          border: 1px solid #2e6b3e;
          transition: var(--transition);
          display: inline-block;
          box-shadow: 0 2px 8px rgba(26,82,40,0.25), inset 0 1px 0 rgba(255,255,255,0.07);
          position: relative;
          overflow: hidden;
        }

        .btn-primary::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
          transition: left 0.4s ease;
        }
        .btn-primary:hover::before { left: 100%; }
        .btn-primary:hover {
          background: var(--sage2);
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(26,82,40,0.35), inset 0 1px 0 rgba(255,255,255,0.1);
        }
        .btn-primary:active { transform: translateY(0); }

        .btn-secondary {
          border: 1.5px solid var(--ink);
          color: var(--ink);
          padding: 15px 34px;
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          text-decoration: none;
          border-radius: var(--radius-sm);
          transition: var(--transition);
          display: inline-block;
          position: relative;
          overflow: hidden;
        }
        .btn-secondary::before {
          content: '';
          position: absolute;
          inset: 0;
          background: var(--ink);
          transform: scaleX(0);
          transform-origin: right;
          transition: transform 0.25s cubic-bezier(0.4,0,0.2,1);
          z-index: -1;
        }
        .btn-secondary:hover {
          color: var(--cream);
          border-color: var(--ink);
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }
        .btn-secondary:hover::before { transform: scaleX(1); transform-origin: left; }
        .btn-secondary:active { transform: translateY(0); }

        .hero-trust {
          margin-top: 52px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          animation: fadeSlideUp 0.7s cubic-bezier(0.4,0,0.2,1) 0.5s both;
        }

        .trust-item {
          display: flex;
          align-items: center;
          gap: 11px;
          font-size: 12.5px;
          font-weight: 400;
          color: var(--mist);
          transition: color 0.2s;
        }
        .trust-item:hover { color: var(--ink2); }

        .trust-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--sage);
          flex-shrink: 0;
          box-shadow: 0 0 0 2px rgba(26,82,40,0.15);
        }

        /* ─── HERO RIGHT ─── */
        .hero-right {
          background: var(--ink);
          position: relative;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .hero-right::before {
          content: '';
          position: absolute;
          inset: 0;
          background:
            radial-gradient(ellipse at 20% 80%, rgba(26,82,40,0.28) 0%, transparent 55%),
            radial-gradient(ellipse at 85% 15%, rgba(138,98,37,0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 60% 50%, rgba(26,82,40,0.06) 0%, transparent 60%);
          pointer-events: none;
        }

        /* Dot grid pattern */
        .hero-right::after {
          content: '';
          position: absolute;
          inset: 0;
          background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
          background-size: 28px 28px;
          pointer-events: none;
        }

        .hero-right-inner {
          padding: 80px 56px;
          position: relative;
          z-index: 2;
          width: 100%;
          animation: fadeSlideUp 0.8s cubic-bezier(0.4,0,0.2,1) 0.3s both;
        }

        .hero-panel-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: 16px;
          font-weight: 400;
          font-style: italic;
          color: rgba(255,255,255,0.38);
          margin-bottom: 28px;
          letter-spacing: 0.02em;
        }

        .stat-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2px;
        }

        .stat-cell {
          background: rgba(255,255,255,0.045);
          padding: 34px 30px;
          border: 1px solid rgba(255,255,255,0.07);
          transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
          position: relative;
          overflow: hidden;
          cursor: default;
        }

        .stat-cell::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 2px;
          height: 0;
          background: linear-gradient(180deg, var(--sage2), transparent);
          transition: height 0.3s ease;
        }
        .stat-cell:hover { background: rgba(255,255,255,0.085); border-color: rgba(255,255,255,0.12); }
        .stat-cell:hover::before { height: 100%; }

        .stat-number {
          font-family: 'Cormorant Garamond', serif;
          font-size: 56px;
          font-weight: 500;
          color: #ddeee2;
          line-height: 1;
          letter-spacing: -0.02em;
        }

        .stat-label {
          font-family: 'DM Mono', monospace;
          font-size: 9.5px;
          font-weight: 400;
          letter-spacing: 0.13em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.3);
          margin-top: 12px;
          line-height: 1.5;
        }

        /* ══════════════════════════════════════════
           MARQUEE
        ══════════════════════════════════════════ */
        .marquee-wrap {
          background: var(--ink2);
          padding: 14px 0;
          overflow: hidden;
          white-space: nowrap;
          border-top: 1px solid rgba(255,255,255,0.05);
          border-bottom: 1px solid rgba(255,255,255,0.04);
          position: relative;
        }

        .marquee-wrap::before,
        .marquee-wrap::after {
          content: '';
          position: absolute;
          top: 0;
          bottom: 0;
          width: 120px;
          z-index: 2;
          pointer-events: none;
        }
        .marquee-wrap::before { left: 0; background: linear-gradient(90deg, var(--ink2), transparent); }
        .marquee-wrap::after { right: 0; background: linear-gradient(-90deg, var(--ink2), transparent); }

        .marquee-track {
          display: inline-block;
          animation: marquee 35s linear infinite;
          will-change: transform;
        }
        .marquee-track:hover { animation-play-state: paused; }

        .marquee-item {
          display: inline-block;
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 400;
          letter-spacing: 0.13em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.22);
          padding: 0 50px;
          transition: color 0.2s;
        }
        .marquee-item:hover { color: rgba(255,255,255,0.5); }
        .marquee-item span { color: var(--gold2); margin-right: 50px; }

        @keyframes marquee {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }

        /* ══════════════════════════════════════════
           FEATURES
        ══════════════════════════════════════════ */
        .features {
          padding: 120px 64px;
          max-width: 1320px;
          margin: 0 auto;
        }

        .section-label {
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.22em;
          text-transform: uppercase;
          color: var(--mist2);
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .section-label::before {
          content: '';
          width: 20px;
          height: 1px;
          background: var(--mist2);
          display: block;
        }

        .section-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: clamp(36px, 3.8vw, 56px);
          font-weight: 500;
          line-height: 1.07;
          color: var(--ink);
          letter-spacing: -0.01em;
        }

        .features-grid {
          margin-top: 68px;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 2px;
          background: var(--border);
          border: 1px solid var(--border);
          border-radius: 6px;
          overflow: hidden;
          box-shadow: var(--shadow);
        }

        .feature-card {
          background: var(--cream);
          padding: 48px 40px;
          transition: background 0.25s ease;
          position: relative;
          cursor: default;
          overflow: hidden;
        }

        .feature-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, var(--sage), var(--sage2));
          transform: scaleX(0);
          transition: transform 0.3s ease;
        }
        .feature-card:hover { background: #daeee0; }
        .feature-card:hover::before { transform: scaleX(1); }

        .feature-num {
          font-family: 'DM Mono', monospace;
          font-size: 10px;
          font-weight: 400;
          color: var(--mist2);
          letter-spacing: 0.12em;
          margin-bottom: 28px;
        }

        .feature-icon {
          width: 44px;
          height: 44px;
          border: 1.5px solid var(--sage);
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 24px;
          color: var(--sage);
          font-size: 19px;
          transition: background 0.2s ease, border-color 0.2s ease;
          background: rgba(26,82,40,0.04);
        }
        .feature-card:hover .feature-icon {
          background: rgba(26,82,40,0.1);
          border-color: var(--sage2);
        }

        .feature-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: 23px;
          font-weight: 500;
          margin-bottom: 13px;
          line-height: 1.2;
          color: var(--ink);
          letter-spacing: -0.005em;
        }

        .feature-desc {
          font-size: 13.5px;
          font-weight: 400;
          line-height: 1.8;
          color: var(--mist);
        }

        .feature-arrow {
          position: absolute;
          bottom: 32px;
          right: 32px;
          font-size: 18px;
          color: var(--sage);
          opacity: 0;
          transition: opacity 0.2s ease, transform 0.2s ease;
          font-family: 'DM Mono', monospace;
        }
        .feature-card:hover .feature-arrow {
          opacity: 1;
          transform: translate(3px, -3px);
        }

        /* ══════════════════════════════════════════
           WORKFLOW
        ══════════════════════════════════════════ */
        .workflow {
          background: var(--ink);
          padding: 120px 64px;
          position: relative;
          overflow: hidden;
        }

        .workflow::before {
          content: '';
          position: absolute;
          inset: 0;
          background:
            radial-gradient(ellipse at 10% 50%, rgba(26,82,40,0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 90% 20%, rgba(138,98,37,0.06) 0%, transparent 45%);
          pointer-events: none;
        }

        .workflow-inner {
          max-width: 1320px;
          margin: 0 auto;
          position: relative;
          z-index: 1;
        }

        .workflow .section-label { color: rgba(255,255,255,0.25); }
        .workflow .section-label::before { background: rgba(255,255,255,0.2); }
        .workflow .section-title { color: #ddeee2; }

        .workflow-steps {
          margin-top: 72px;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 52px;
          position: relative;
        }

        .workflow-steps::before {
          content: '';
          position: absolute;
          top: 28px;
          left: 80px;
          right: 80px;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), rgba(255,255,255,0.1), transparent);
        }

        .step-num-wrap {
          display: flex;
          align-items: center;
          gap: 18px;
          margin-bottom: 28px;
        }

        .step-circle {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          border: 1px solid rgba(255,255,255,0.12);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'DM Mono', monospace;
          font-size: 12px;
          font-weight: 500;
          color: var(--gold2);
          flex-shrink: 0;
          background: rgba(255,255,255,0.03);
          transition: var(--transition);
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }
        .step-circle:hover {
          border-color: rgba(255,255,255,0.25);
          background: rgba(255,255,255,0.06);
        }

        .step-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: 21px;
          font-weight: 500;
          color: #ddeee2;
          line-height: 1.25;
          letter-spacing: -0.005em;
        }

        .step-desc {
          font-size: 13.5px;
          font-weight: 400;
          line-height: 1.82;
          color: rgba(255,255,255,0.38);
          padding-left: 74px;
        }

        /* ══════════════════════════════════════════
           HELP / ESCALATION
        ══════════════════════════════════════════ */
        .help-strip {
          background: var(--paper);
          border-top: 1px solid var(--border);
          padding: 100px 64px;
          position: relative;
        }

        .help-strip-inner {
          max-width: 1280px;
          margin: 0 auto;
        }

        .help-hdr {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 32px;
          margin-bottom: 48px;
        }

        .help-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--mist2);
          margin-bottom: 14px;
        }

        .help-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: clamp(32px, 3.2vw, 48px);
          font-weight: 500;
          line-height: 1.08;
          color: var(--ink);
          letter-spacing: -0.01em;
        }
        .help-title em { font-style: italic; color: var(--sage); }

        .help-hdr-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 16px;
          flex-shrink: 0;
        }

        .help-sub {
          font-size: 13.5px;
          font-weight: 400;
          color: var(--mist);
          line-height: 1.82;
          max-width: 340px;
          text-align: right;
        }

        .help-cta {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-family: 'DM Mono', monospace;
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: #dceee0;
          text-decoration: none;
          background: var(--sage);
          padding: 11px 20px;
          border-radius: var(--radius-sm);
          border: 1px solid #2e6b3e;
          transition: var(--transition);
          box-shadow: 0 2px 8px rgba(26,82,40,0.2), inset 0 1px 0 rgba(255,255,255,0.06);
        }
        .help-cta:hover {
          background: var(--sage2);
          transform: translateY(-1px);
          box-shadow: 0 4px 14px rgba(26,82,40,0.3);
        }

        /* Helplines bar */
        .help-helplines {
          background: var(--ink);
          border-radius: var(--radius);
          padding: 20px 28px;
          display: flex;
          align-items: center;
          margin-bottom: 3px;
          border: 1px solid rgba(255,255,255,0.05);
          box-shadow: var(--shadow-sm);
        }

        .help-hl-label {
          font-family: 'DM Mono', monospace;
          font-size: 9.5px;
          font-weight: 500;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.25);
          flex-shrink: 0;
          margin-right: 36px;
        }

        .help-hl-items { display: flex; flex: 1; }

        .help-hl-item {
          display: flex;
          flex-direction: column;
          gap: 3px;
          padding-right: 32px;
          margin-right: 32px;
          border-right: 1px solid rgba(255,255,255,0.08);
          transition: opacity 0.2s;
        }
        .help-hl-item:last-child { border-right: none; padding-right: 0; margin-right: 0; }
        .help-hl-item:hover { opacity: 0.85; }

        .help-hl-name {
          font-family: 'DM Mono', monospace;
          font-size: 8.5px;
          font-weight: 400;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.28);
        }

        .help-hl-num {
          font-family: 'Cormorant Garamond', serif;
          font-size: 20px;
          font-weight: 500;
          color: #cce8d5;
          letter-spacing: 0.02em;
        }

        /* Step cards */
        .help-steps {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 2px;
          background: var(--border2);
          border: 1px solid var(--border2);
          border-radius: var(--radius);
          overflow: hidden;
          margin-bottom: 3px;
          box-shadow: var(--shadow-sm);
        }

        .help-step {
          background: #faf8f4;
          padding: 22px 22px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          transition: background 0.18s ease;
          position: relative;
        }
        .help-step::before {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, var(--sage), var(--sage2));
          transform: scaleX(0);
          transition: transform 0.25s ease;
        }
        .help-step:hover { background: #f2ede4; }
        .help-step:hover::before { transform: scaleX(1); }

        .help-step-num {
          font-family: 'DM Mono', monospace;
          font-size: 9.5px;
          font-weight: 500;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--mist2);
        }

        .help-step-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: 17px;
          font-weight: 500;
          color: var(--ink);
          line-height: 1.25;
        }

        .help-step-desc {
          font-size: 12px;
          font-weight: 400;
          color: var(--mist);
          line-height: 1.68;
        }

        /* Resource cards */
        .help-orgs {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 2px;
          background: var(--border2);
          border: 1px solid var(--border2);
          border-radius: var(--radius);
          overflow: hidden;
          box-shadow: var(--shadow-sm);
        }

        .help-org {
          background: #faf8f4;
          padding: 20px 20px;
          display: flex;
          flex-direction: column;
          gap: 7px;
          text-decoration: none;
          color: inherit;
          transition: background 0.18s ease, transform 0.18s ease;
          position: relative;
          overflow: hidden;
        }
        .help-org::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: var(--sage);
          transform: scaleX(0);
          transition: transform 0.25s ease;
        }
        .help-org:hover { background: var(--cream); }
        .help-org:hover::after { transform: scaleX(1); }

        .help-org-top {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 6px;
        }

        .help-org-name {
          font-family: 'Cormorant Garamond', serif;
          font-size: 16px;
          font-weight: 500;
          color: var(--ink);
          line-height: 1.25;
        }

        .help-org-type {
          font-family: 'DM Mono', monospace;
          font-size: 7.5px;
          font-weight: 500;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          padding: 3px 7px;
          border-radius: 2px;
          flex-shrink: 0;
          margin-top: 3px;
        }

        .help-org-desc {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.68;
          color: var(--mist);
          flex: 1;
        }

        .help-org-action {
          font-family: 'DM Mono', monospace;
          font-size: 9px;
          font-weight: 500;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--sage);
          display: flex;
          align-items: center;
          gap: 4px;
          margin-top: 4px;
          transition: gap 0.2s ease;
        }
        .help-org:hover .help-org-action { gap: 7px; }

        .help-orgs-footer {
          margin-top: 14px;
          display: flex;
          justify-content: flex-end;
        }

        .help-orgs-link {
          font-family: 'DM Mono', monospace;
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 0.13em;
          text-transform: uppercase;
          color: var(--sage);
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border-bottom: 1px solid rgba(26,82,40,0.25);
          padding-bottom: 2px;
          transition: border-color 0.2s ease, gap 0.2s ease;
        }
        .help-orgs-link:hover { border-color: var(--sage); gap: 10px; }

        /* ══════════════════════════════════════════
           CTA BAND
        ══════════════════════════════════════════ */
        .cta-band {
          background: var(--cream);
          border-top: 1px solid var(--border);
          padding: 112px 64px;
          text-align: center;
          position: relative;
          overflow: hidden;
        }

        .cta-band::before {
          content: 'CareBridge';
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-family: 'Cormorant Garamond', serif;
          font-size: clamp(80px, 16vw, 210px);
          font-weight: 500;
          color: rgba(26,82,40,0.04);
          white-space: nowrap;
          pointer-events: none;
          user-select: none;
          letter-spacing: -0.02em;
        }

        .cta-band::after {
          content: '';
          position: absolute;
          inset: 0;
          background:
            radial-gradient(ellipse at 50% 50%, rgba(26,82,40,0.04) 0%, transparent 60%);
          pointer-events: none;
        }

        .cta-title {
          font-family: 'Cormorant Garamond', serif;
          font-size: clamp(36px, 4.2vw, 60px);
          font-weight: 500;
          line-height: 1.07;
          margin-bottom: 20px;
          position: relative;
          color: var(--ink);
          letter-spacing: -0.015em;
          z-index: 1;
        }
        .cta-title em { font-style: italic; color: var(--sage); }

        .cta-sub {
          font-size: 15.5px;
          font-weight: 400;
          color: var(--mist);
          margin-bottom: 52px;
          position: relative;
          max-width: 470px;
          margin-left: auto;
          margin-right: auto;
          line-height: 1.78;
          z-index: 1;
        }

        /* ══════════════════════════════════════════
           FOOTER
        ══════════════════════════════════════════ */
        .footer {
          background: var(--ink);
          padding: 52px 64px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-top: 1px solid rgba(255,255,255,0.05);
          position: relative;
        }

        .footer::before {
          content: '';
          position: absolute;
          top: 0;
          left: 64px;
          right: 64px;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(46,122,68,0.35), rgba(154,112,48,0.2), rgba(46,122,68,0.35), transparent);
          pointer-events: none;
        }

        .footer-logo {
          font-family: 'Cormorant Garamond', serif;
          font-size: 21px;
          font-weight: 500;
          color: rgba(255,255,255,0.35);
          letter-spacing: 0.04em;
          transition: color 0.2s;
        }
        .footer-logo:hover { color: rgba(255,255,255,0.6); }

        .footer-disclaimer {
          font-size: 11.5px;
          font-weight: 400;
          color: rgba(255,255,255,0.18);
          max-width: 480px;
          line-height: 1.72;
          text-align: center;
        }

        .footer-links { display: flex; gap: 28px; }

        .footer-links a {
          font-family: 'DM Mono', monospace;
          font-size: 9.5px;
          font-weight: 400;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.28);
          text-decoration: none;
          transition: color 0.2s ease;
          position: relative;
        }

        .footer-links a::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          width: 0;
          height: 1px;
          background: rgba(255,255,255,0.5);
          transition: width 0.25s ease;
        }
        .footer-links a:hover { color: rgba(255,255,255,0.65); }
        .footer-links a:hover::after { width: 100%; }

        /* ══════════════════════════════════════════
           ANIMATIONS
        ══════════════════════════════════════════ */
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(18px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        /* ══════════════════════════════════════════
           RESPONSIVE
        ══════════════════════════════════════════ */
        @media (max-width: 900px) {
          .hero { grid-template-columns: 1fr; }
          .hero-right { min-height: 340px; }
          .hero-left { padding: 115px 32px 60px; }
          .features, .workflow { padding: 80px 28px; }
          .features-grid, .workflow-steps { grid-template-columns: 1fr; }
          .workflow-steps::before { display: none; }
          .step-desc { padding-left: 0; }
          .nav { padding: 0 22px; }
          .footer { flex-direction: column; gap: 26px; text-align: center; padding: 44px 28px; }
          .footer::before { left: 28px; right: 28px; }
          .footer-links { justify-content: center; flex-wrap: wrap; }
          .cta-band, .help-strip { padding: 80px 28px; }
          .help-hdr { flex-direction: column; align-items: flex-start; }
          .help-hdr-right { align-items: flex-start; }
          .help-sub { text-align: left; }
          .help-helplines { flex-direction: column; align-items: flex-start; gap: 12px; }
          .help-hl-label { margin-right: 0; }
          .help-hl-items { flex-wrap: wrap; gap: 12px; }
          .help-steps, .help-orgs { grid-template-columns: 1fr 1fr; }
        }

        @media (max-width: 540px) {
          .help-steps, .help-orgs { grid-template-columns: 1fr; }
          .stat-grid { grid-template-columns: 1fr 1fr; }
        }
      `}</style>

      {/* ── NAV ── */}
      <nav className="nav">
        <Link href="/" className="nav-logo">
          Care<span>Bridge</span>
        </Link>
        <ul className="nav-links">
          <li>
            <a href="/prepurchase">Analyze Policy</a>
          </li>
          <li>
            <a href="/audit">Claim Audit</a>
          </li>
          <li>
            <a href="/compare">Compare</a>
          </li>
          <li>
            <a href="/support" className="nav-help">
              Get Help
            </a>
          </li>
          <li>
            <a href="/prepurchase" className="nav-cta">
              Get Started
            </a>
          </li>
        </ul>
      </nav>

      {/* ── HERO ── */}
      <section className="hero" ref={heroRef}>
        <div className="hero-left">
          <div className="hero-eyebrow">IRDAI-Aligned Intelligence</div>
          <h1 className="hero-h1">
            Insurance clarity
            <br />
            <em>before the claim</em>
          </h1>
          <p className="hero-sub">
            CareBridge decodes policy wording, identifies structural risks, and
            audits claim rejections — with regulatory precision, not guesswork.
          </p>
          <div className="hero-actions">
            <Link href="/prepurchase" className="btn-primary">
              Analyze a Policy
            </Link>
            <Link href="/audit" className="btn-secondary">
              Audit a Rejection
            </Link>
          </div>
          <div className="hero-trust">
            {[
              "Clause-level detection across 10 risk categories",
              "IRDAI compliance evaluation with 7 regulatory markers",
              "Hybrid rule engine + constrained LLM interpretation",
              "Privacy-first — no document storage",
            ].map((t, i) => (
              <div key={i} className="trust-item">
                <span className="trust-dot" />
                {t}
              </div>
            ))}
          </div>
        </div>

        <div className="hero-right">
          <div className="hero-right-inner">
            <p className="hero-panel-title">Live analysis metrics</p>
            <div className="stat-grid">
              {[
                { n: "10", l: "Clause categories" },
                { n: "7", l: "IRDAI markers" },
                { n: "48h", l: "Max PED wait detected" },
                { n: "4B", l: "Parameter model" },
              ].map((s, i) => (
                <div key={i} className="stat-cell">
                  <div className="stat-number">{s.n}</div>
                  <div className="stat-label">{s.l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── MARQUEE ── */}
      <div className="marquee-wrap">
        <div className="marquee-track">
          {Array(2)
            .fill([
              "Pre-existing Disease",
              "Waiting Period",
              "Room Rent Sublimit",
              "Co-payment Clause",
              "Exclusion Clarity",
              "Restoration Benefit",
              "IRDAI Compliance",
              "Ombudsman Rights",
              "Claim Settlement",
              "Disease-Specific Caps",
            ])
            .flat()
            .map((item, i) => (
              <span key={i} className="marquee-item">
                <span>·</span>
                {item}
              </span>
            ))}
        </div>
      </div>

      {/* ── FEATURES ── */}
      <section className="features">
        <div className="section-label">Intelligence Modules</div>
        <h2 className="section-title">
          Every risk surface,
          <br />
          systematically mapped
        </h2>
        <div className="features-grid">
          {[
            {
              num: "01",
              icon: "⬡",
              title: "Clause-Level Risk Detection",
              desc: "Identifies and classifies 10 critical policy clauses — waiting periods, exclusions, sublimits, co-payments, disease caps — against IRDAI risk thresholds.",
            },
            {
              num: "02",
              icon: "⊛",
              title: "IRDAI Compliance Audit",
              desc: "Evaluates 7 weighted regulatory markers including grievance mechanisms, free-look disclosure, portability clauses, and claims settlement timelines.",
            },
            {
              num: "03",
              icon: "◈",
              title: "Rejection Clause Audit",
              desc: "Matches rejection letters against policy wording, detects contradictions in pre-existing disease and waiting period claims, and scores appeal strength.",
            },
          ].map((f, i) => (
            <div key={i} className="feature-card">
              <div className="feature-num">{f.num}</div>
              <div className="feature-icon">{f.icon}</div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
              <span className="feature-arrow">↗</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── WORKFLOW ── */}
      <section className="workflow">
        <div className="workflow-inner">
          <div className="section-label">How it works</div>
          <h2 className="section-title">
            Three steps from
            <br />
            document to decision
          </h2>
          <div className="workflow-steps">
            {[
              {
                n: "01",
                title: "Submit your document",
                desc: "Paste policy wording, rejection letters, or medical records. No account required. Nothing is stored.",
              },
              {
                n: "02",
                title: "Hybrid analysis runs",
                desc: "Rule engines classify clauses deterministically. The LLM interprets context, ambiguity, and regulatory alignment.",
              },
              {
                n: "03",
                title: "Receive structured intelligence",
                desc: "Clause risk scores, IRDAI compliance flags, red flags, appeal strength, and step-by-step reapplication guidance.",
              },
            ].map((s, i) => (
              <div key={i}>
                <div className="step-num-wrap">
                  <div className="step-circle">{s.n}</div>
                  <h4 className="step-title">{s.title}</h4>
                </div>
                <p className="step-desc">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HELP / ESCALATION ── */}
      <section className="help-strip">
        <div className="help-strip-inner">
          <div className="help-hdr">
            <div>
              <div className="help-eyebrow">Escalation & Assistance</div>
              <h2 className="help-title">
                Rejected?
                <br />
                <em>You have recourse.</em>
              </h2>
            </div>
            <div className="help-hdr-right">
              <p className="help-sub">
                Official regulators, legal aid, and financial assistance —
                separated by function with a structured letter generator.
              </p>
              <a href="/support" className="help-cta">
                Open escalation tool ↗
              </a>
            </div>
          </div>

          <div className="help-helplines">
            <span className="help-hl-label">Free helplines</span>
            <div className="help-hl-items">
              {[
                { name: "IRDAI Helpline", num: "155255" },
                { name: "IRDAI Toll-free", num: "1800 4254 732" },
                { name: "Consumer Helpline", num: "1800-11-4000" },
                { name: "NALSA Legal Aid", num: "15100" },
              ].map((h, i) => (
                <div key={i} className="help-hl-item">
                  <span className="help-hl-name">{h.name}</span>
                  <span className="help-hl-num">{h.num}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="help-steps">
            {[
              {
                n: "01",
                title: "Insurer GRO",
                desc: "File written complaint. Insurer must respond in 15 days.",
              },
              {
                n: "02",
                title: "IRDAI IGMS",
                desc: "Escalate to IRDAI portal if insurer doesn't respond.",
              },
              {
                n: "03",
                title: "Insurance Ombudsman",
                desc: "Free binding resolution. Claims up to Rs 50 lakhs.",
              },
              {
                n: "04",
                title: "Consumer Court",
                desc: "Deficiency of service under CPA 2019. No lawyer needed.",
              },
            ].map((s, i) => (
              <div key={i} className="help-step">
                <div className="help-step-num">{s.n}</div>
                <div className="help-step-title">{s.title}</div>
                <div className="help-step-desc">{s.desc}</div>
              </div>
            ))}
          </div>

          <div className="help-orgs">
            {[
              {
                name: "IRDAI IGMS",
                type: "Regulator",
                desc: "Official complaint portal. 15-day response mandate.",
                action: "igms.irda.gov.in",
                url: "https://igms.irda.gov.in/",
                color: "#1e5c2e",
                bg: "#d6eddc",
              },
              {
                name: "Insurance Ombudsman",
                type: "Quasi-Judicial",
                desc: "Free, binding. Claims up to Rs 50 lakhs. 17 offices.",
                action: "cioins.co.in",
                url: "https://cioins.co.in/",
                color: "#2d3f8a",
                bg: "#d8dff5",
              },
              {
                name: "NALSA Legal Aid",
                type: "Legal Aid",
                desc: "Free lawyers for eligible citizens. Consumer forum.",
                action: "nalsa.gov.in",
                url: "https://nalsa.gov.in/",
                color: "#3a5c10",
                bg: "#daecd0",
              },
              {
                name: "Consumer Forum",
                type: "Legal",
                desc: "CPA 2019 covers insurance. Online filing. No advocate.",
                action: "edaakhil.nic.in",
                url: "https://edaakhil.nic.in/",
                color: "#6a3a10",
                bg: "#f0deca",
              },
            ].map((org, i) => (
              <a
                key={i}
                href={org.url}
                target="_blank"
                rel="noopener noreferrer"
                className="help-org"
              >
                <div className="help-org-top">
                  <span className="help-org-name">{org.name}</span>
                  <span
                    className="help-org-type"
                    style={{ background: org.bg, color: org.color }}
                  >
                    {org.type}
                  </span>
                </div>
                <p className="help-org-desc">{org.desc}</p>
                <span className="help-org-action">{org.action} ↗</span>
              </a>
            ))}
          </div>

          <div className="help-orgs-footer">
            <a href="/support" className="help-orgs-link">
              Generate escalation letter →
            </a>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="cta-band">
        <h2 className="cta-title">
          Make informed decisions.
          <br />
          <em>Before you commit.</em>
        </h2>
        <p className="cta-sub">
          Replace brochure-driven choices with structured insurance
          intelligence.
        </p>
        <Link href="/prepurchase" className="btn-primary">
          Begin Analysis
        </Link>
      </section>

      {/* ── FOOTER ── */}
      <footer className="footer">
        <div className="footer-logo">CareBridge</div>
        <p className="footer-disclaimer">
          CareBridge provides interpretative support based on submitted text. It
          does not constitute legal advice, claim approval, or regulatory
          assessment. Verify all findings with your insurer or a qualified
          advisor.
        </p>
        <div className="footer-links">
          <a href="/prepurchase">Policy Analysis</a>
          <a href="/audit">Claim Audit</a>
          <a href="/compare">Compare</a>
          <a href="/support">Get Help</a>
        </div>
      </footer>
    </>
  );
}
