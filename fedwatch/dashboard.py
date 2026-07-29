from __future__ import annotations

from fedwatch.bootstrap import BootstrapNode


def create_fed_path_figure(nodes: list[BootstrapNode], current_rate: float):
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError("Plotly is required. Install via 'pip install plotly'.")

    dates = ["Today"]
    rates = [current_rate]
    hover_texts = [f"Current Rate: {current_rate:.3f}%"]

    cut_bars: list[float] = [0.0]
    hold_bars: list[float] = [1.0]
    hike_bars: list[float] = [0.0]

    for node in nodes:
        if node.meeting is None:
            continue
        dates.append(str(node.meeting.decision_date))
        rates.append(node.rate_after)

        if node.outcomes:
            cut_bars.append((node.outcomes.probs.get(-50, 0.0) + node.outcomes.probs.get(-25, 0.0)) * 100)
            hold_bars.append(node.outcomes.probs.get(0, 0.0) * 100)
            hike_bars.append((node.outcomes.probs.get(25, 0.0) + node.outcomes.probs.get(50, 0.0)) * 100)
            dominant_bp, dominant_prob = node.outcomes.dominant
            label = "hold" if dominant_bp == 0 else f"{dominant_bp:+d}bp"
            hover_texts.append(
                f"FOMC {node.meeting.decision_date}<br>"
                f"Implied: {node.rate_after:.3f}%<br>"
                f"Dominant: {label} ({dominant_prob*100:.0f}%)"
            )
        else:
            cut_bars.append(0.0)
            hold_bars.append(100.0)
            hike_bars.append(0.0)
            hover_texts.append(f"FOMC {node.meeting.decision_date}<br>Implied: {node.rate_after:.3f}%")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=rates,
        mode="lines+markers+text",
        text=[f"{r:.2f}%" for r in rates],
        textposition="top center",
        hoverinfo="text",
        hovertext=hover_texts,
        line=dict(color="#4ade80", width=3),
        marker=dict(size=10, color="#4ade80", line=dict(color="#000000", width=2)),
        name="Implied Rate",
    ))

    fig.add_trace(go.Bar(
        x=dates,
        y=cut_bars,
        name="Cut Prob %",
        marker_color="rgba(248, 113, 113, 0.5)",
        yaxis="y2",
    ))
    fig.add_trace(go.Bar(
        x=dates,
        y=hold_bars,
        name="Hold Prob %",
        marker_color="rgba(148, 163, 184, 0.4)",
        yaxis="y2",
    ))
    fig.add_trace(go.Bar(
        x=dates,
        y=hike_bars,
        name="Hike Prob %",
        marker_color="rgba(96, 165, 250, 0.5)",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Market-Implied Fed Funds Rate Path",
        xaxis=dict(title="FOMC Decision Date"),
        yaxis=dict(title="Implied Rate (%)", side="left"),
        yaxis2=dict(
            title="Probability (%)",
            side="right",
            overlaying="y",
            range=[0, 120],
            showgrid=False,
        ),
        barmode="stack",
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#0a0a0a",
        font=dict(family="JetBrains Mono, monospace", color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=70, b=50),
    )

    return fig
