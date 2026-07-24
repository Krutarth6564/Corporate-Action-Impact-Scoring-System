import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import json

CUSTOM_DARK_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }

    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 40%, #0D9488 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 24px;
        border: 1px solid #334155;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        color: #F8FAFC;
    }
    .main-header p {
        font-size: 14px;
        color: #94A3B8;
        margin-top: 6px;
        margin-bottom: 0;
    }

    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94A3B8;
        font-weight: 600;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 4px;
    }
</style>
"""

def inject_theme():
    """Injects dark-mode styling."""
    st.markdown(CUSTOM_DARK_THEME_CSS, unsafe_allow_html=True)

def render_header():
    """Renders main title banner."""
    st.markdown("""
        <div class="main-header">
            <h1>Corporate Action Impact Scoring System</h1>
            <p>Production Market Intelligence Platform for NSE/BSE Announcement Analysis & Ranking</p>
        </div>
    """, unsafe_allow_html=True)

def render_kpis(summary: Dict[str, Any]):
    """Renders top metric cards."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Filings Analyzed</div>
                <div class="metric-value">{summary['total_processed']}</div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Very High / High Risks</div>
                <div class="metric-value" style="color: #EF4444;">{summary['very_high_count'] + summary['high_count']}</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Avg Impact Score</div>
                <div class="metric-value" style="color: #38BDF8;">{summary['avg_impact_score']} / 100</div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Top Rated Filing</div>
                <div class="metric-value" style="font-size: 15px; margin-top: 8px; color: #FACC15;">{summary['top_announcement']}</div>
            </div>
        """, unsafe_allow_html=True)

def render_company_score_cards(df: pd.DataFrame):
    """Renders prominent impact score cards for all analyzed companies."""
    if df is None or df.empty:
        return
    st.subheader("All Analyzed Company Impact Scores")
    num_cols = max(1, min(len(df), 4))
    cols = st.columns(num_cols)
    
    for idx, (_, row) in enumerate(df.iterrows()):
        col = cols[idx % num_cols]
        rating_color = "#EF4444" if row["impact_rating"] == "Very High" else (
            "#F97316" if row["impact_rating"] == "High" else (
                "#EAB308" if row["impact_rating"] == "Medium" else "#3B82F6"
            )
        )
        with col:
            st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 12px; border-left: 4px solid {rating_color};">
                    <div style="font-size: 11px; font-weight: 700; color: {rating_color};">#{row.get('rank', idx+1)} | {row['impact_rating'].upper()}</div>
                    <div style="font-size: 16px; font-weight: 700; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{row['ticker']}</div>
                    <div style="font-size: 11px; color: #94A3B8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{row['company_name']}</div>
                    <div style="font-size: 22px; font-weight: 800; color: #F8FAFC; margin-top: 4px;">{row['impact_score']} <span style="font-size: 12px; font-weight: 400; color: #94A3B8;">/ 100</span></div>
                    <div style="font-size: 11px; color: #38BDF8; margin-top: 2px;">{row['announcement_type']}</div>
                </div>
            """, unsafe_allow_html=True)

def render_charts(df: pd.DataFrame, selected_row: pd.Series = None):
    """Renders Plotly Gauge chart, Pie chart, Bar chart, and Score Distribution histogram."""
    if df.empty:
        return

    st.subheader("Visual Market Analytics")
    c1, c2 = st.columns(2)

    # Use selected row or fallback to top row
    target_row = selected_row if selected_row is not None else df.iloc[0]

    with c1:
        # Plotly Gauge Chart for Selected Announcement
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=target_row["impact_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Impact Gauge: {target_row['ticker']} ({target_row['impact_rating']})", 'font': {'size': 14, 'color': "#F8FAFC"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#F8FAFC"},
                'bar': {'color': "#0D9488"},
                'bgcolor': "#1E293B",
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 45], 'color': '#3B82F6'},
                    {'range': [45, 70], 'color': '#EAB308'},
                    {'range': [70, 85], 'color': '#F97316'},
                    {'range': [85, 100], 'color': '#EF4444'}
                ]
            }
        ))
        fig_gauge.update_layout(paper_bgcolor="#0F172A", height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, width='stretch')

    with c2:
        # Plotly Pie Chart for Category Distribution
        cat_counts = df["announcement_type"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig_pie = px.pie(
            cat_counts,
            names="Category",
            values="Count",
            title="Announcement Category Breakdown",
            hole=0.4,
            template="plotly_dark"
        )
        fig_pie.update_layout(paper_bgcolor="#0F172A", height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie, width='stretch')

    c3, c4 = st.columns(2)

    with c3:
        # Plotly Score Distribution Histogram
        fig_dist = px.histogram(
            df,
            x="impact_score",
            nbins=15,
            title="Impact Score Distribution (0-100)",
            color="impact_rating",
            color_discrete_map={
                "Very High": "#EF4444",
                "High": "#F97316",
                "Medium": "#EAB308",
                "Low": "#3B82F6"
            },
            template="plotly_dark"
        )
        fig_dist.update_layout(paper_bgcolor="#0F172A", height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_dist, width='stretch')

    with c4:
        # Average Impact Score by Category Bar Chart
        avg_cat = df.groupby("announcement_type")["impact_score"].mean().reset_index().sort_values("impact_score", ascending=True)
        fig_bar = px.bar(
            avg_cat,
            x="impact_score",
            y="announcement_type",
            orientation="h",
            title="Average Impact Score by Category",
            color="impact_score",
            color_continuous_scale="Tealgrn",
            template="plotly_dark"
        )
        fig_bar.update_layout(paper_bgcolor="#0F172A", height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, width='stretch')

def render_detail_inspector(row: pd.Series):
    """Renders full expandable company deep dive with score explanation."""
    st.markdown(f"### Announcement Inspection: **{row['company_name']}** (`{row['ticker']}`)")
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown(f"**Rank:** `#{row.get('rank', '-')}` | **Impact Score:** `{row['impact_score']}/100` | **Rating:** `{row['impact_rating']}`")
        st.markdown(f"**Category:** `{row['announcement_type']}` | **Sector:** `{row['sector']}` | **Exchange:** `{row['exchange']}`")
        st.markdown(f"**Disclosed Value:** `{row['formatted_contract_value']}` | **Client:** `{row['client']} ({row['government_or_private']})`")
        
        st.info(f"**Executive Business Summary:**\n{row['summary']}")
        st.success(f"**Explainable Score Rationale:**\n{row['score_explanation']}")

        if row.get("positive_signals"):
            st.markdown(f"🟢 **Positive Signals:** {', '.join(row['positive_signals'])}")
        if row.get("risk_factors"):
            st.markdown(f"🔴 **Risk Factors:** {', '.join(row['risk_factors'])}")

    with c2:
        breakdown = row.get("score_breakdown", {})
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except Exception:
                breakdown = {}

        if breakdown:
            st.markdown("#### Score Breakdown")
            lines = []
            for factor, pts in breakdown.items():
                sign = "+" if pts >= 0 else ""
                lines.append(f"{factor.ljust(22, '.')} {sign}{pts:.1f}")
            lines.append("-" * 32)
            lines.append(f"{'Total Score'.ljust(22, '.')} = {row['impact_score']:.1f}")

            formatted_breakdown = "\n".join(lines)
            st.code(formatted_breakdown, language="text")

            b_df = pd.DataFrame(list(breakdown.items()), columns=["Factor", "Points"])
            fig_b = px.bar(
                b_df,
                x="Points",
                y="Factor",
                orientation="h",
                title="Factor Decomposition",
                template="plotly_dark",
                color="Points",
                color_continuous_scale="Viridis"
            )
            fig_b.update_layout(paper_bgcolor="#0F172A", height=240, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_b, width='stretch')
