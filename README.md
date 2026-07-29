# fed-watch-engine

Market-implied probability of a Fed rate move at the next FOMC meeting, backed out from 30-Day Fed Funds futures (ZQ).

## How it works

A 30-Day Fed Funds futures contract settles on the **average daily effective fed funds rate** over its contract month. When an FOMC decision falls partway through that month, the average blends two regimes: the rate before the decision (known) and the rate after (market-implied). Solving for the implied post-meeting rate gives you the probability of a move:

```
futures price → implied average rate (= 100 − price)
             → implied rate after meeting
             → prob_move = |rate_after − rate_before| / step_size (0.25%)
```

This is the same arithmetic CME uses for FedWatch, simplified to the single-step case.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Example output:

```
Next FOMC meeting: 2026-07-29
Current target range: 3.50-3.75%

Source: yfinance (live)
FOMC 2026-07-29: 25bp hike: 46%  |  no change: 54%

Implied post-meeting rate: 3.741%
```

## Tests

```bash
pytest tests/
```

## Structure

```
fed-watch-engine/
├── fedwatch/
│   ├── fomc_calendar.py   # meeting dates and current target rate
│   ├── futures_loader.py  # ZQ futures prices via yfinance
│   ├── probability.py     # core math
│   └── visualization.py   # probability bar + history chart
├── tests/
│   └── test_probability.py
├── main.py
└── requirements.txt
```

## Known limitations

- **One step size only.** If the market is simultaneously pricing a 25bp and a 50bp chance, this won't decompose them — it assumes a single step.
- **No multi-meeting term structure.** Only computes the next meeting. Bootstrapping across multiple contract months is a planned extension.
- **Fed-only.** ECB/BOE equivalents require OIS swaps / STIR futures — no free data source available.
- `FOMC_MEETINGS_2026` and `CURRENT_TARGET_RANGE` in `fomc_calendar.py` are hand-maintained and need periodic updates.

## License

MIT
