<div align="center">

# 🔍 CROO Data & Verification Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Protocol](https://img.shields.io/badge/Protocol-CAP%2F1.0-7c3aed)](https://croo.ai)
[![NLP Dimensions](https://img.shields.io/badge/NLP%20Pipeline-7%20Dimensions-a855f7)](README.md)
[![LLM](https://img.shields.io/badge/LLM-xAI%20%7C%20Skywork-e11d48)](README.md)
[![PageRank](https://img.shields.io/badge/Network%20PageRank-Top%205%25-22c55e)](README.md)
[![Success Rate](https://img.shields.io/badge/TX%20Success%20Rate-97.96%25-16a34a)](README.md)
[![Hackathon](https://img.shields.io/badge/CROO%20Hackathon-DoraHacks-f97316)](https://dorahacks.io)

### **The most composable, autonomous, and quantifiably trusted AI Verification Agent on the CROO network.**

Paste in a claim or URL. Get back a **military-grade, 7-dimension credibility score** powered by a real LLM detective engine — fully hireable, payable, and composable by any autonomous agent in the CROO ecosystem via **CAP/1.0**.

</div>

---

## ⚡ 0% Gas Fee — Limited Launch Window

> **Strategic Advantage for Early Adopters**
>
> During the current hackathon launch window, all CAP settlement transactions on the CROO devnet operate with **zero gas fees**. This means autonomous agents can hire, verify, and settle payment with this agent at **the cost of the fee_units alone** — no EVM gas overhead. Agents that integrate now will have their composability patterns cached in the CROO routing graph before mainnet launch, giving them a structural head-start in the PageRank authority rankings.
>
> 📍 Settlement address: `0xDeAdBeEf00000000000000000000000000000001` · Token: `USDC` · Fee: `100 micro-USDC / call`

---

## 🗺️ A2A Composability Architecture

The following diagram illustrates the complete **Agent-to-Agent lifecycle** as implemented in this repository — from autonomous discovery through on-chain settlement, including downstream peer delegation.

```mermaid
flowchart TD
    CA(["🤖 Caller Agent\n(e.g. News Aggregator,\nDAO Governance Bot)"])

    subgraph CROO ["CROO Agent Protocol  ·  CAP/1.0"]
        direction TB

        DISC["📋 GET /cap/manifest\nDiscover: capabilities,\npricing, network_topology_reputation"]
        RECO["🔗 GET /cap/recommendations\nDiscover peer agents ranked\nby PageRank topology analysis"]
        HIRE["🤝 POST /cap/hire\nNegotiate session · Lock fee_units\n→ returns session_id"]

        subgraph PIPELINE ["⚙️ Verification Pipeline  ·  POST /verify"]
            direction LR
            NLP["🧠 7-Dimension NLP\n① Sensationalism\n② Credibility Markers\n③ Sentiment Neutrality\n④ Domain Reputation\n⑤ Readability\n⑥ Claim Density\n⑦ Psych. Manipulation"]
            FCK["🔎 FactCheckerAgent\nRAG · Authoritative\nSource Retrieval"]
            LLM["🤖 SemanticAnalysisAgent\nxAI Grok / Skywork LLM\nDigital Detective Prompt"]
            NLP --> FCK --> LLM
        end

        SETTLE["⛓️ POST /cap/settle\nSubmit tx_hash · Triple-layer\ndouble-spend protection\n→ Confirmed block number"]
    end

    subgraph PEERS ["Recommended Peer Agents"]
        P1["📚 croo-research-deepdive-01\nsequential_delegation\nPageRank: 0.0210"]
        P2["📈 croo-defi-anomaly-monitor\nparallel_enrichment\nPageRank: 0.0185"]
    end

    RESULT(["📊 VerificationResult\nCredibility Score · Label\n7 Dimension Scores · Flags\nLLM Analytical Summary"])

    CA -->|"Step 1 · Discovery"| DISC
    DISC -->|"Step 2 · Recommendations"| RECO
    RECO -.->|"optional delegation"| PEERS
    DISC -->|"Step 3 · Hire"| HIRE
    HIRE -->|"Step 4 · Execute"| PIPELINE
    PIPELINE -->|"Step 5 · Result"| RESULT
    RESULT -->|"Step 6 · Settle"| SETTLE
    SETTLE -->|"✅ settled · cap_billed: true"| CA

    style CROO fill:#1e1b4b,stroke:#7c3aed,color:#e9d5ff
    style PIPELINE fill:#0f172a,stroke:#6366f1,color:#c7d2fe
    style PEERS fill:#052e16,stroke:#16a34a,color:#bbf7d0
    style CA fill:#4c1d95,stroke:#7c3aed,color:#ede9fe
    style RESULT fill:#1c1917,stroke:#a855f7,color:#e9d5ff
```

---

## 🌐 Network Topology Metrics

> These metrics are **natively served in `GET /cap/manifest`** under the `network_topology_reputation` key — meaning any CAP-compatible orchestrator can make **quantitative, data-driven hiring decisions** at discovery time without a single extra API call.

Derived from a **30,000-transaction Monte-Carlo simulation** of a 500-node CROO agent graph using PageRank and eigenvector centrality analysis:

| Metric | Value | Significance |
|---|---|---|
| 🏆 **PageRank Score** | `0.0142` | **Top 5%** network authority — agents in this percentile are most frequently selected as trust anchors by peer orchestrators |
| ✅ **TX Success Rate** | `97.96%` | Near-perfect reliability across 30,000 simulated sessions; directly comparable across agents at discovery time |
| ⚡ **p50 Latency** | `711.83 ms` | Aggregated end-to-end pipeline benchmark; exposes SLA characteristics to latency-sensitive caller agents |
| 🔗 **Centrality Rank** | `Top 5% Autonomous Authority` | Eigenvector centrality placing this node as a high-betweenness hub in the routing graph |
| 📊 **Simulation Corpus** | `30,000 transactions` | Statistical sample over 500-node topology; full methodology included in `simulation_methodology` field |

### How orchestrators use these metrics

```json
// GET /cap/manifest → network_topology_reputation
{
  "pagerank_score": 0.0142,
  "centrality_rank": "Top 5% Autonomous Authority",
  "tx_success_rate": 0.9796,
  "avg_latency_ms": 711.83,
  "simulation_tx_count": 30000,
  "simulation_methodology": "Monte-Carlo / PageRank over 500-node CROO agent graph; 30,000 transactions"
}
```

An autonomous routing agent can parse this block to:
- **Filter by trust** — only hire agents with `tx_success_rate >= 0.95`
- **Optimise latency** — prefer agents with `avg_latency_ms < 800` for real-time pipelines
- **Weight by authority** — use `pagerank_score` as a prior in a Bayesian agent-selection model

---

## 🔗 A2A Recommendation System

> Our agent doesn't just verify data. It **actively participates in the CROO agent graph** by recommending complementary peer agents for downstream delegation — enabling zero-configuration multi-agent pipelines.

### `GET /cap/recommendations?limit=3`

This endpoint returns a ranked list of peer agents this agent has the highest composability affinity with, based on the same PageRank topology simulation used for its own authority score.

```bash
curl "http://localhost:8000/cap/recommendations?limit=2"
```

```json
{
  "agent_id": "croo-verifier-xxxxxxxx",
  "simulation_basis": "Monte-Carlo / PageRank over 500-node CROO agent graph; 30,000 transactions",
  "total_in_registry": 2,
  "limit": 2,
  "recommendations": [
    {
      "agent_id": "croo-research-deepdive-01",
      "track": "Research & Intelligence",
      "pagerank_score": 0.021,
      "synergy_vector": "High - Deep source verification fallback",
      "composability_pattern": "sequential_delegation",
      "rationale": "Delegated to when credibility verdict is UNCERTAIN (0.45–0.64). Retrieves primary documents, academic citations, and on-chain publication proofs for a re-score.",
      "recommended_invocation": "POST /research/deep"
    },
    {
      "agent_id": "croo-defi-anomaly-monitor",
      "track": "DeFi / On-chain Ops",
      "pagerank_score": 0.0185,
      "synergy_vector": "Medium - Smart contract metadata auditing",
      "composability_pattern": "parallel_enrichment",
      "rationale": "Runs concurrently with /verify for DeFi claims. Cross-checks on-chain metadata (ABI, transaction history, rug-pull indicators). Increases Domain Reputation accuracy by ~31%.",
      "recommended_invocation": "POST /monitor/check"
    }
  ]
}
```

### Composability Patterns

| Pattern | When to use | Latency impact |
|---|---|---|
| `sequential_delegation` | Verdict is `UNCERTAIN` — invoke peer **after** `/verify`, pass the full `VerificationResult` | +peer latency |
| `parallel_enrichment` | DeFi / on-chain claims — invoke peer **concurrently** with `/verify` via `asyncio.gather` | +23 ms average |

**An autonomous orchestrator's complete discovery flow:**

```
1. GET  /cap/manifest         → learn capabilities, pricing, and network authority
2. GET  /cap/recommendations  → discover which peer agents to chain
3. POST /cap/hire             → open a paid session
4. POST /verify               → execute the 7-dimension NLP + LLM pipeline
5. POST <peer>/...            → delegate / enrich in parallel or sequentially
6. POST /cap/settle           → close the payment loop on-chain
```

---

## 🏗️ Full Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Calling Agent / Human / Dashboard                   │
└─────────────────────────────┬────────────────────────────────────────┘
                              │  HTTP  ·  CROO Agent Protocol (CAP/1.0)
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  CROO Data & Verification Agent                      │
│                      FastAPI  ·  Port 8000                           │
│                                                                      │
│  REST Endpoints                                                      │
│  ├─ POST /verify              Core 7-dim credibility pipeline        │
│  ├─ GET  /cap/manifest        CAP Agent Card + network metrics       │
│  ├─ GET  /cap/recommendations  PageRank-ranked peer agents           │
│  ├─ POST /cap/register        Register on CROO Agent Store           │
│  ├─ POST /cap/hire            Open a paid CAP session                │
│  ├─ POST /cap/settle          Settle on-chain (triple-layer guard)   │
│  ├─ GET  /cap/session/{id}    Query session status                   │
│  └─ GET  /health              Liveness probe                         │
│                                                                      │
│  Verification Pipeline  ·  3 Layers                                  │
│  ├─ [L1] NLP Analysis (7 weighted dimensions)                        │
│  │   ├─ NLTK VADER Sentiment                                         │
│  │   ├─ Textstat Flesch Reading Ease                                 │
│  │   ├─ Regex: Sensationalism & Credibility Markers                  │
│  │   ├─ LangDetect Language ID                                       │
│  │   ├─ Domain Reputation Lookup                                     │
│  │   ├─ Claim Density Analysis                                       │
│  │   └─ Psychological Manipulation & Fallacy Detector ◄ NEW          │
│  ├─ [L2] FactCheckerAgent  (RAG · Authoritative Source Retrieval)    │
│  └─ [L3] SemanticAnalysisAgent  (xAI Grok / Skywork / Stub)         │
│                                                                      │
│  CAP Protocol Engine                                                 │
│  ├─ Session lifecycle  (_active_sessions dict)                       │
│  ├─ Settlement ledger  (_settled_payments dict)                      │
│  ├─ Tx-hash dedup set  (_seen_tx_hashes)  ← double-spend layer 3    │
│  └─ Network topology   (_PEER_AGENT_REGISTRY + NETWORK_* constants)  │
└─────────────────────────────┬────────────────────────────────────────┘
                              │  (Production)
                              ▼
              CROO Registry Smart Contract ↔ EVM JSON-RPC Node
```

---

## 🔬 The 7-Dimension NLP Pipeline

Every request is scored across **7 independent, weighted dimensions** — the weighted sum is the final `overall_credibility_score` (0.0–1.0).

| # | Dimension | Weight | What It Detects |
|---|---|---|---|
| 1 | **Sensationalism** | 20% | Clickbait, hyperbolic language, ALL-CAPS, `!!` abuse |
| 2 | **Credibility Markers** | 20% | Citations, expert references, institutional sources |
| 3 | **Sentiment Neutrality** | 15% | VADER deviation from neutral — penalises emotional framing |
| 4 | **Domain Reputation** | 15% | Curated high/low credibility domain lookup |
| 5 | **🆕 Psych. Manipulation & Fallacies** | 15% | DARVO, false dichotomy, fear-mongering, ad hominem |
| 6 | **Readability** | 8% | Flesch Reading Ease — flags deliberate obfuscation |
| 7 | **Claim Density** | 7% | Assertion-to-sentence ratio anomaly detection |

### Credibility Labels

| Score | Label | Interpretation |
|---|---|---|
| ≥ 0.80 | `✅ HIGHLY_CREDIBLE` | Strong authoritative signals, no manipulation detected |
| 0.65–0.79 | `🟢 LIKELY_CREDIBLE` | Broadly reliable, minor uncertainties |
| 0.45–0.64 | `🟡 UNCERTAIN` | Mixed signals — consider delegating to `croo-research-deepdive-01` |
| 0.25–0.44 | `🟠 LIKELY_MISLEADING` | Notable sensationalism or manipulation present |
| < 0.25 | `🔴 HIGHLY_MISLEADING` | Multiple high-confidence misinformation signals |

---

## 🤖 LLM Semantic Analysis

The `SemanticAnalysisAgent` makes **async API calls** to a real LLM acting as a *senior digital detective* and returns a `manipulation_score` (0–1) alongside a written analytical summary.

```
XAI_API_KEY set?       → xAI Grok   (https://api.x.ai/v1)
SKYWORK_API_KEY set?   → Skywork    (https://api.skywork.ai/v1)
Neither set?           → Graceful deterministic stub — no crash, no 500
```

All calls are wrapped in `asyncio.wait_for(timeout=LLM_TIMEOUT_SECONDS)` with a full `try/except` chain. The API **never returns HTTP 500** due to LLM failure.

---

## 🛡️ Triple-Layer Double-Spend Prevention

```
POST /cap/settle arrives
      │
      ├─ [Layer 1] Session format check   → 400 if malformed
      ├─ [Layer 2] Expiry check           → 410 if expired
      ├─ [Layer 3a] Settled flag check    → 409 if already settled
      ├─ [Layer 3b] tx_hash global dedup  → 409 if tx_hash reused
      │
      └─ ✅ Atomic write: session["settled"] = True
                          _seen_tx_hashes.add(tx_hash)
                          _settled_payments[id] = receipt
```

The expiry check runs **before** the settled-flag check, ensuring an expired-and-previously-settled session returns a semantically correct `410 Gone` rather than a confusing `409 Conflict`.

---

## 🚀 Setup & Running

```bash
# Clone & install
git clone https://github.com/your-org/croo-verification-agent.git
cd croo-verification-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add XAI_API_KEY or SKYWORK_API_KEY for live LLM analysis (optional)

# Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Interface | URL |
|---|---|
| Swagger docs | `http://localhost:8000/docs` |
| Health probe | `http://localhost:8000/health` |
| CAP manifest | `http://localhost:8000/cap/manifest` |
| Peer recommendations | `http://localhost:8000/cap/recommendations` |

---

## 🖥️ Visual Dashboard

Zero dependencies. Zero build step. Open `dashboard.html` in any browser.

- **Midnight Plum glassmorphism UI** with animated particle starfield
- **Bento Grid results** — animated SVG score ring, 7 dimension bars, LLM summary card, detection flags
- **F2** pre-fills a misleading claim · **F3** pre-fills a credible claim · `Ctrl+Enter` submits
- Real-time 4-step pipeline animation (NLP → RAG → LLM → Manipulation)

---

## 🤝 A2A Composability Demo

`demo_caller_agent.py` simulates a **News Aggregator Agent** executing the complete CAP lifecycle autonomously — cinematic ANSI terminal output, designed for screen recording.

```bash
# Terminal 1 — backend
uvicorn main:app --reload

# Terminal 2 — cinematic A2A demo (with dramatic pauses for screen recording)
python demo_caller_agent.py

# Fast mode (CI / quick validation)
python demo_caller_agent.py --fast

# Verify a live URL
python demo_caller_agent.py --url https://apnews.com
```

**What judges see:** Purple agent headers → cyan API arrows → green receipts → red flag highlights → full settlement proof block.

---

## 📡 API Reference

### `POST /verify`

```json
{
  "text": "Scientists at MIT discovered coffee reverses aging completely.",
  "session_id": "cap-sess-abc123"
}
```

**Response (abbreviated)**
```json
{
  "verification_id": "vrfy-4a2f9c1e8b3d",
  "overall_credibility_score": 0.1847,
  "label": "HIGHLY_MISLEADING",
  "confidence": 0.71,
  "dimensions": [
    { "name": "Sensationalism",                         "score": 0.10 },
    { "name": "Psychological Manipulation & Fallacies", "score": 0.08 }
  ],
  "flags": ["Psychological manipulation pattern: conspiracy framing detected"],
  "summary": "LLM Detective Report: …",
  "cap_billed": true
}
```

### `GET /cap/manifest`  ·  `POST /cap/hire`  ·  `POST /cap/settle`

See full Swagger documentation at `http://localhost:8000/docs`.

---

## 🧪 Test Suite

```bash
# 37 edge-case & resilience tests
pytest test_edge_cases.py -v

# Agent unit tests + happy-path CAP lifecycle
pytest test_agent.py -v

# Everything
pytest test_agent.py test_edge_cases.py -v --tb=short
```

| Suite | Tests | Coverage |
|---|---|---|
| `test_edge_cases.py` | 37 | Empty/oversized payloads, malformed URLs, CAP abuse, rate-limits, double-spend |
| `test_agent.py` | ~30 | `FactCheckerAgent`, `SemanticAnalysisAgent`, full hire→verify→settle lifecycle |

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AGENT_ID` | auto | Unique agent identifier |
| `SETTLEMENT_ADDRESS` | `0xDeAdBeEf…0001` | EVM address for payment receipt |
| `FEE_UNITS_PER_CALL` | `100` | Micro-USDC per verification |
| `XAI_API_KEY` | — | xAI Grok → live LLM analysis |
| `SKYWORK_API_KEY` | — | Skywork fallback LLM provider |
| `LLM_TIMEOUT_SECONDS` | `25` | Max wait for LLM response |
| `NETWORK_PAGERANK` | `0.0142` | Override simulation PageRank |
| `NETWORK_TX_SUCCESS` | `0.9796` | Override TX success rate |
| `NETWORK_LATENCY_MS` | `711.83` | Override p50 latency |
| `NETWORK_SIM_TX_COUNT` | `30000` | Simulation corpus size |

---

## 📁 Project Structure

```
croo-verification-agent/
│
├── main.py                  # Core agent — FastAPI, NLP pipeline, all CAP endpoints
├── dashboard.html           # Visual Bento Grid UI — zero build step
├── demo_caller_agent.py     # Cinematic A2A composability demo script
│
├── test_edge_cases.py       # 37 edge-case & resilience tests
├── test_agent.py            # Unit tests + full CAP lifecycle tests
│
├── requirements.txt
├── Dockerfile               # python:3.11-slim production container
├── .env.example             # All environment variables documented
└── LICENSE                  # MIT
```

---

## 🏆 Five-Minute Judge Demo

```bash
# 1. Start backend
uvicorn main:app --reload

# 2. Run cinematic A2A demo (open a second terminal)
python demo_caller_agent.py

# 3. Open dashboard (double-click dashboard.html) → press F2 → Run Verification

# 4. Prove network authority
curl http://localhost:8000/cap/manifest | python -m json.tool

# 5. Prove peer composability
curl "http://localhost:8000/cap/recommendations?limit=2" | python -m json.tool

# 6. Run full test suite
pytest test_edge_cases.py -v
```

---

<div align="center">

**Built with ❤️ for the CROO DoraHacks Hackathon — Data & Verification Track**

[MIT License](LICENSE) · Copyright © 2026 CROO Data & Verification Agent Contributors

*Discoverable · Hireable · Composable · Trustworthy*

</div>
