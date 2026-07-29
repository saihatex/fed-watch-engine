from __future__ import annotations

from fedwatch.bootstrap import BootstrapNode


def create_fed_path_figure(nodes: list[BootstrapNode], current_rate: float):
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError("Plotly is required for dashboard visualization. Install it via 'pip install plotly'.")

    dates = []
    rates = []
    hover_texts = []

    dates.append("Today")
    rates.append(current_rate)
    hover_texts.append(f"Current Rate: {current_rate:.3f}%")

    for node in nodes:
        if node.meeting is not None:
            dates.append(str(node.meeting.decision_date))
            rates.append(node.rate_after)
            outcome_text = str(node.outcomes) if node.outcomes else ""
            hover_texts.append(f"FOMC {node.meeting.decision_date}<br>Implied: {node.rate_after:.3f}%<br>{outcome_text}")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rates,
            mode="lines+markers+text",
            text=[f"{r:.2f}%" for r in rates],
            textposition="top center",
            hoverinfo="text",
            hovertext=hover_texts,
            line=dict(color="#ffffff", width=3),
            marker=dict(size=8, color="#4ade80"),
        )
    )

    fig.update_layout(
        title="Market-Implied Fed Funds Rate Path",
        xaxis_title="FOMC Decision Date",
        yaxis_title="Implied Rate (%)",
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(family="JetBrains Mono, monospace", color="#ffffff"),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig
