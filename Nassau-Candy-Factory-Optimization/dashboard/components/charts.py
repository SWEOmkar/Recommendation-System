"""Charts component utilizing Plotly with customized dark configurations."""

import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def _empty_figure(message: str = "Chart unavailable") -> go.Figure:
    """Returns a minimal empty Plotly figure with an annotation message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#8A8A8A"),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def render_revenue_trend(df: pd.DataFrame) -> go.Figure:
    """Renders the Monthly Revenue Trend line chart.

    Matches the mockup color schemes (muted purple line, custom dark grid lines).
    
    Args:
        df (pd.DataFrame): Ingestion dataset.

    Returns:
        go.Figure: Plotly figure object.
    """
    try:
        # Group by month and sum sales
        monthly_sales = df.set_index("Order Date").resample("ME")["Sales"].sum().reset_index()
        monthly_sales["Month Name"] = monthly_sales["Order Date"].dt.strftime("%b")
        
        # Line chart using Plotly graph objects for precise customization
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_sales["Month Name"],
            y=monthly_sales["Sales"],
            mode="lines+markers",
            line=dict(color="#5C54A4", width=3),
            marker=dict(color="#5C54A4", size=6),
            name="Sales"
        ))
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=10, b=30),
            height=320,
            xaxis=dict(
                showline=True,
                showgrid=False,
                showticklabels=True,
                linecolor="rgba(255,255,255,0.05)",
                tickfont=dict(color="#8A8A8A", size=10)
            ),
            yaxis=dict(
                showline=False,
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                tickfont=dict(color="#8A8A8A", size=10),
                tickformat="$,.0f"
            ),
            showlegend=False
        )
        return fig
    except Exception:
        logger.exception("Failed to render revenue trend chart")
        return _empty_figure("Revenue trend unavailable")


def render_sales_donut(df: pd.DataFrame) -> go.Figure:
    """Renders the Sales Share by Product Division donut chart.

    Color matches the mockup:
    - Chocolate: Muted Purple (#5C54A4)
    - Sugar: Teal (#49A09D)
    - Other: Mustard (#E5A93C)

    Args:
        df (pd.DataFrame): Ingestion dataset.

    Returns:
        go.Figure: Plotly figure object.
    """
    try:
        division_shares = df.groupby("Division")["Sales"].sum().reset_index()
        
        # Map division to mockup hex codes
        color_map = {
            "Chocolate": "#5C54A4",
            "Sugar": "#49A09D",
            "Other": "#E5A93C"
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=division_shares["Division"],
            values=division_shares["Sales"],
            hole=0.55,
            marker=dict(colors=[color_map.get(x, "#8A8A8A") for x in division_shares["Division"]]),
            textinfo="percent",
            textfont=dict(size=11, color="#FFFFFF"),
            hoverinfo="label+value"
        )])
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=0.85,
                font=dict(color="#8A8A8A", size=11)
            )
        )
        return fig
    except Exception:
        logger.exception("Failed to render sales donut chart")
        return _empty_figure("Sales distribution unavailable")
