from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .probability import RateExpectation


def plot_probability_bar(expectation: RateExpectation, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 4))

    if expectation.direction == "hold":
        labels = ["No change"]
        values = [expectation.prob_hold * 100]
        colors = ["#4C72B0"]
    else:
        step_bp = int(round(expectation.step_size * 100))
        labels = [f"{step_bp}bp {expectation.direction}", "No change"]
        values = [expectation.prob_move * 100, expectation.prob_hold * 100]
        colors = ["#C44E52", "#4C72B0"]

    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Implied probability (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"FOMC {expectation.meeting_decision_date}")
    for i, v in enumerate(values):
        ax.text(i, v + 2, f"{v:.0f}%", ha="center")
    return ax


def plot_expectation_history(history: pd.Series, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))

    (history * 100).plot(ax=ax, marker="o")
    ax.set_ylabel("Implied probability of move (%)")
    ax.set_xlabel("Date")
    ax.set_title("Market expectations over time")
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3)
    return ax
