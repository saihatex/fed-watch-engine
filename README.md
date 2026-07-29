# Fed Watch Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An institutional-grade **Fed Funds futures bootstrapping engine** and market-implied FOMC probability model based on CME 30-Day Fed Funds futures (`ZQ`).

---

## 📐 Mathematical Formulation

### 1. Implied Monthly Average Rate

A 30-Day Fed Funds futures contract settles on the arithmetic average daily Effective Federal Funds Rate ($\text{EFFR}$) over the contract month $m$:

$$\text{Price}_m = 100 - \bar{R}_m \implies \bar{R}_m = 100 - \text{Price}_m$$

where $\bar{R}_m$ is the market-implied average rate for month $m$.

### 2. Single-Month Decomposition

For a month $m$ containing an FOMC rate decision on day $d_{\text{decision}}$ with $N$ total days in the month:

$$d_{\text{before}} = d_{\text{decision}}, \quad d_{\text{after}} = N - d_{\text{before}}$$

The monthly average rate $\bar{R}_m$ is a weighted sum of the rate prior to the meeting ($R_{\text{before}}$) and the implied rate post-decision ($R_{\text{after}}$):

$$\bar{R}_m = \frac{d_{\text{before}} \cdot R_{\text{before}} + d_{\text{after}} \cdot R_{\text{after}}}{N}$$

Solving for the post-decision implied rate $R_{\text{after}}$:

$$R_{\text{after}} = \frac{N \cdot \bar{R}_m - d_{\text{before}} \cdot R_{\text{before}}}{d_{\text{after}}}$$

### 3. Multi-Month Curve Bootstrapping

For a sequence of contract months $m \in \{1, 2, \dots, K\}$, the engine carries $R_{\text{after}, m}$ forward as $R_{\text{before}, m+1}$ for subsequent meetings:

$$R_{\text{before}, m+1} = \begin{cases} R_{\text{after}, m} & \text{if month } m \text{ contains an FOMC decision} \\ R_{\text{before}, m} & \text{otherwise} \end{cases}$$

### 4. Probability Mapping

Given rate change $\Delta R = R_{\text{before}} - R_{\text{after}}$ and standard step size $\Delta s = 0.25\%$ (25 bp):

$$\text{Steps} = \frac{\Delta R}{\Delta s}$$

For $0 \le \text{Steps} \le 1$:
$$\mathbb{P}(\text{Cut } 25\text{bp}) = \text{Steps}, \quad \mathbb{P}(\text{Hold}) = 1 - \text{Steps}$$

For $1 < \text{Steps} \le 2$:
$$\mathbb{P}(\text{Cut } 50\text{bp}) = \text{Steps} - 1, \quad \mathbb{P}(\text{Cut } 25\text{bp}) = 2 - \text{Steps}$$

---

## 🏗 System Architecture

```
fed-watch-engine/
├── fedwatch/
│   ├── __init__.py           # Public API exports
│   ├── fomc_calendar.py      # Scheduled FOMC dates & current target rate
│   ├── futures_loader.py     # Live ZQ chain fetcher (yfinance)
│   ├── probability.py        # Single-month pricing equations
│   ├── probability_mapper.py # Multi-outcome probability mapping (-50..+50bp)
│   ├── bootstrap.py          # Multi-month curve bootstrapping engine
│   ├── db.py                 # SQLite persistence schema & storage
│   ├── snapshot.py           # Daily snapshot recording & delta engine
│   ├── cli.py                # Terminal formatter
│   └── dashboard.py          # Interactive Plotly rate path visualizer
├── tests/
│   ├── test_probability.py
│   └── test_bootstrap.py
├── main.py
└── requirements.txt
```

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Execution

Run full bootstrap pipeline with CLI terminal report and SQLite snapshotting:

```bash
python main.py
```

Display interactive Plotly **Fed Path** rate curve:

```bash
python main.py --plot
```

---

## 🧪 Testing

Run pytest suite:

```bash
python -m pytest tests/ -v
```

---

## 📄 License

MIT
