"use client";

import { useState } from "react";

export default function Page() {
  const [query, setQuery] = useState("");

  return (
    <main className="page">
      <header className="nav">
        <div className="wordmark">
          FRAME<span className="dot">.</span>
        </div>
        <a href="#start" className="navcta">
          Log in
        </a>
      </header>

      <section className="hero">
        <p className="eyebrow">TYPE A QUESTION. WATCH THE ANSWER.</p>
        <h1 className="h1">
          Stuck on a concept?
          <br />
          We&rsquo;ll shoot a short film about it.
        </h1>
        <p className="sub">
          Frame turns any confusing topic into a short, narrated explainer —
          built fresh by AI in under a minute.
        </p>

        <form className="slate" id="start" onSubmit={(e) => e.preventDefault()}>
          <input
            className="slate-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Explain... why mitochondria have two membranes"
            aria-label="What do you want explained?"
          />
          <button className="slate-btn" type="submit">
            Make my explainer
          </button>
        </form>
      </section>

      <section className="how" id="how">
        <div className="scenes">
          <div className="scene">
            <span className="scene-n">01</span>
            <h3>You ask.</h3>
            <p>Type a concept or paste a question you got wrong on a test.</p>
          </div>
          <div className="scene">
            <span className="scene-n">02</span>
            <h3>We shoot it.</h3>
            <p>Frame writes a script, generates visuals, and adds a voiceover.</p>
          </div>
          <div className="scene">
            <span className="scene-n">03</span>
            <h3>You keep it.</h3>
            <p>Your explainer lands in your reel, ready to rewatch or remix.</p>
          </div>
        </div>
      </section>

      <section className="cta">
        <h2>Got something you still don&rsquo;t get?</h2>
        <p>Your first five explainers are free.</p>
        <a href="#start" className="cta-btn">
          Make my first explainer
        </a>
      </section>

      <footer className="footer">
        <div className="wordmark small">
          FRAME<span className="dot">.</span>
        </div>
        <p className="fineprint">Made frame by frame, for anyone still figuring something out.</p>
      </footer>

      <style jsx global>{`
        :root {
          --ink: #14161b;
          --ink-soft: #1c1f26;
          --paper: #ede7d8;
          --flame: #e8773a;
          --flame-dim: #c75f28;
          --line: #34373e;
          --ash: #9b9890;
          --ash-dark: #5b5950;
        }
        * {
          box-sizing: border-box;
        }
        html,
        body {
          margin: 0;
          padding: 0;
          background: var(--ink);
        }
        @media (prefers-reduced-motion: reduce) {
          * {
            transition-duration: 0.001ms !important;
          }
        }
      `}</style>

      <style jsx>{`
        .page {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            "Helvetica Neue", Arial, sans-serif;
          background: var(--ink);
          color: var(--paper);
        }
        a {
          color: inherit;
          text-decoration: none;
        }

        .nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 28px 6vw 0;
          max-width: 1000px;
          margin: 0 auto;
        }
        .wordmark {
          font-weight: 800;
          font-size: 20px;
          letter-spacing: 0.04em;
        }
        .wordmark.small {
          font-size: 16px;
        }
        .dot {
          color: var(--flame);
        }
        .navcta {
          font-size: 14px;
          border: 1px solid var(--line);
          border-radius: 999px;
          padding: 8px 18px;
        }
        .navcta:hover {
          border-color: var(--flame);
          color: var(--flame);
        }
        @media (max-width: 420px) {
          .nav {
            padding: 20px 6vw 0;
          }
          .wordmark {
            font-size: 17px;
          }
          .navcta {
            font-size: 13px;
            padding: 7px 14px;
          }
        }

        .hero {
          max-width: 1000px;
          margin: 0 auto;
          padding: 64px 6vw 0;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
        }
        .eyebrow {
          font-size: 12px;
          letter-spacing: 0.16em;
          color: var(--flame);
          margin: 0 0 18px;
        }
        .h1 {
          font-weight: 700;
          font-size: clamp(34px, 6vw, 60px);
          line-height: 1.08;
          letter-spacing: -0.01em;
          margin: 0 0 20px;
          max-width: 720px;
        }
        .sub {
          font-size: 17px;
          line-height: 1.55;
          color: var(--ash);
          max-width: 520px;
          margin: 0 0 32px;
        }
        @media (max-width: 640px) {
          .hero {
            padding: 44px 6vw 0;
          }
          .eyebrow {
            margin-bottom: 14px;
          }
          .h1 {
            margin-bottom: 16px;
          }
          .sub {
            font-size: 15.5px;
            margin-bottom: 28px;
          }
        }

        .slate {
          width: 100%;
          max-width: 560px;
          display: flex;
          gap: 10px;
          margin-bottom: 80px;
        }
        .slate-input {
          flex: 1;
          background: var(--ink-soft);
          border: 1px solid var(--line);
          border-radius: 10px;
          outline: none;
          color: var(--paper);
          font-size: 15px;
          padding: 13px 16px;
        }
        .slate-input::placeholder {
          color: var(--ash-dark);
        }
        .slate-btn {
          background: var(--flame);
          color: var(--ink);
          border: none;
          border-radius: 10px;
          font-weight: 600;
          font-size: 15px;
          padding: 13px 20px;
          cursor: pointer;
          white-space: nowrap;
        }
        .slate-btn:hover {
          background: var(--flame-dim);
        }
        @media (max-width: 560px) {
          .slate {
            flex-direction: column;
          }
          .slate-btn {
            width: 100%;
          }
        }
        @media (max-width: 640px) {
          .slate {
            margin-bottom: 56px;
          }
        }

        .how {
          max-width: 1000px;
          margin: 0 auto;
          padding: 80px 6vw 0;
        }
        .scenes {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 32px;
        }
        .scene {
          border-top: 1px solid var(--line);
          padding-top: 18px;
        }
        .scene-n {
          font-size: 13px;
          color: var(--ash-dark);
        }
        .scene h3 {
          font-size: 22px;
          font-weight: 700;
          margin: 10px 0 8px;
        }
        .scene p {
          color: var(--ash);
          line-height: 1.5;
          font-size: 14px;
          margin: 0;
        }
        @media (max-width: 640px) {
          .how {
            padding: 56px 6vw 0;
          }
          .scenes {
            gap: 24px;
          }
        }

        .cta {
          max-width: 720px;
          margin: 100px auto 0;
          padding: 0 6vw;
          text-align: center;
        }
        .cta h2 {
          font-size: clamp(28px, 4vw, 42px);
          font-weight: 700;
          margin: 0 0 12px;
        }
        .cta p {
          color: var(--ash);
          font-size: 16px;
          margin: 0 0 24px;
        }
        .cta-btn {
          display: inline-block;
          background: var(--flame);
          color: var(--ink);
          font-weight: 600;
          font-size: 15px;
          padding: 13px 28px;
          border-radius: 999px;
        }
        .cta-btn:hover {
          background: var(--flame-dim);
        }
        @media (max-width: 640px) {
          .cta {
            margin-top: 70px;
          }
          .cta-btn {
            width: 100%;
            padding: 14px 20px;
          }
        }

        .footer {
          max-width: 1000px;
          margin: 90px auto 0;
          padding: 24px 6vw 36px;
          border-top: 1px solid var(--line);
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .fineprint {
          font-size: 13px;
          color: var(--ash-dark);
          margin: 0;
        }
        @media (max-width: 640px) {
          .footer {
            margin-top: 64px;
            flex-direction: column;
            align-items: flex-start;
          }
        }
      `}</style>
    </main>
  );
}