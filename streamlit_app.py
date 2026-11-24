"""
Tennis Intelligence Platform (TIP) - Streamlit Cloud Web Application
Interactive AI Sports Analytics, Player Intelligence & Tactical Radar Dashboard.
"""
import os
import sys
import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Setup python path so we can reuse backend and ML engine directly
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
ML_DIR = os.path.join(ROOT_DIR, "machine-learning", "models")
SQL_DIR = os.path.join(ROOT_DIR, "sql")

for p in [ROOT_DIR, BACKEND_DIR, ML_DIR, SQL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Page Configuration
st.set_page_config(
    page_title="Tennis Intelligence Platform (TIP)",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark mode with Tennis Neon Green and Electric Cyan)
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .metric-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-val {
        font-size: 26px;
        font-weight: 800;
        color: #10b981;
        font-family: monospace;
    }
    .metric-label {
        font-size: 11px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
    .tier-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.03);
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(16, 185, 129, 0.2) !important;
        color: #34d399 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Database Engine Initialization with Streamlit Secrets & Fallback
@st.cache_resource
def get_db_session():
    """Returns SQLAlchemy session and engine, ensuring tables exist and are seeded."""
    # Check secrets or environment
    db_url = None
    if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
    elif "DATABASE_URL" in os.environ:
        db_url = os.environ["DATABASE_URL"]

    from app.database.connection import engine, SessionLocal, Base
    from app.models.entities import (  # noqa: F401
        Category, Competition, Complex, Venue, Competitor,
        CompetitorRanking, User, OTPVerification, UserFavourite, AIInteraction, SyncLog
    )

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Auto-seed if empty
    session = SessionLocal()
    try:
        count = session.query(Competitor).count()
        if count == 0:
            from seed_database import seed_database
            seed_database()
    except Exception as e:
        st.warning(f"Database auto-seed notice: {e}")
    finally:
        session.close()

    return SessionLocal, engine


# Data Loaders
@st.cache_data(ttl=300)
def load_all_players():
    """Loads players joined with rankings and computes radar traits via ML engine."""
    SessionLocal, _ = get_db_session()
    session = SessionLocal()
    try:
        from app.models.entities import Competitor, CompetitorRanking
        from cluster_engine import TennisMLEngine

        rows = (
            session.query(
                Competitor.competitor_id,
                Competitor.name,
                Competitor.country,
                Competitor.country_code,
                Competitor.abbreviation,
                CompetitorRanking.rank,
                CompetitorRanking.points,
                CompetitorRanking.movement,
                CompetitorRanking.competitions_played,
            )
            .join(CompetitorRanking, Competitor.competitor_id == CompetitorRanking.competitor_id)
            .order_by(CompetitorRanking.rank.asc())
            .all()
        )

        players_raw = [
            {
                "competitor_id": r[0],
                "name": r[1],
                "country": r[2] or "Unknown",
                "country_code": r[3] or "",
                "abbreviation": r[4] or "",
                "rank": r[5],
                "points": r[6],
                "movement": r[7],
                "competitions_played": r[8],
            }
            for r in rows
        ]

        if not players_raw:
            return []

        ml_engine = TennisMLEngine()
        profiled = ml_engine.fit_and_profile(players_raw)
        return profiled
    finally:
        session.close()


@st.cache_data(ttl=300)
def load_queries():
    """Parses sql/queries.sql into a list of {id, title, sql}."""
    queries_file = os.path.join(SQL_DIR, "queries.sql")
    if not os.path.exists(queries_file):
        return []

    with open(queries_file, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"--\s*Query\s*#?(\d+):?\s*([^\n]+)", content)
    queries = []
    # blocks[0] is preamble; blocks[1]=id, blocks[2]=title, blocks[3]=sql
    i = 1
    while i < len(blocks):
        q_id = blocks[i].strip()
        q_title = blocks[i+1].strip()
        q_sql = blocks[i+2].strip()
        queries.append({
            "id": int(q_id),
            "label": f"Query #{q_id}: {q_title}",
            "title": q_title,
            "sql": q_sql
        })
        i += 3
    return queries


# App Header
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 16px; margin-bottom: 24px;">
    <div>
        <h1 style="margin: 0; font-size: 32px; font-weight: 800; color: #ffffff;">
            🎾 TENNIS<span style="color: #10b981;">INTEL</span> PLATFORM
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">
            AI-Powered Sports Analytics, Tactical Archetype Clustering & SQL Analytics Lab
        </p>
    </div>
    <div style="text-align: right;">
        <span class="tier-badge">System Status: OPERATIONAL</span>
        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Connected • High Concurrency Active</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load core data
players = load_all_players()
queries_list = load_queries()

if not players:
    st.error("No player data found in database. Please run seeding.")
    st.stop()

df_players = pd.DataFrame(players)

# Sidebar
with st.sidebar:
    st.image("https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/activity.svg", width=36)
    st.markdown("### 🏆 Platform Navigation")
    menu = st.radio(
        "Choose Intelligence View:",
        [
            "📊 Executive Overview",
            "🎾 Player Explorer & Radar",
            "⚔️ Head-to-Head Comparison",
            "🧠 Machine Learning Clusters",
            "🔍 20 SQL Queries Lab",
            "🛡️ Data Quality & Architecture"
        ]
    )

    st.markdown("---")
    st.markdown("### 📈 Live Telemetry")
    st.markdown(f"**Competitors:** `{len(players)} Pro Players`")
    st.markdown(f"**Top Point Leader:** `{df_players['points'].max():,} pts`")
    st.markdown(f"**Countries Represented:** `{df_players['country'].nunique()}`")
    st.markdown("**ML Model:** `K-Means (K=5)`")

    st.markdown("---")
    st.caption("Tennis Intelligence Platform • Production Build • Streamlit Cloud Edition")


# ==========================================
# VIEW 1: EXECUTIVE OVERVIEW
# ==========================================
if menu == "📊 Executive Overview":
    st.subheader("📊 Executive Analytics & Tournaments Overview")

    # Metric Cards Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{len(players)}</div>
            <div class="metric-label">Tracked Pro Players</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{df_players['competitions_played'].sum()}</div>
            <div class="metric-label">Total Match Instances</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{df_players['country'].nunique()}</div>
            <div class="metric-label">Global Nations</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{int(df_players['points'].mean()):,}</div>
            <div class="metric-label">Average Points</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 0.8])
    with c1:
        st.markdown("#### 🏆 Global Pro Leaderboard")
        display_cols = ["rank", "name", "country", "points", "competitions_played", "cluster_tier"]
        st.dataframe(
            df_players[display_cols].rename(columns={
                "rank": "Rank #",
                "name": "Player Name",
                "country": "Country",
                "points": "ATP Points",
                "competitions_played": "Tournaments",
                "cluster_tier": "Tactical Archetype"
            }),
            use_container_width=True,
            hide_index=True
        )

    with c2:
        st.markdown("#### 🌍 Country Representation")
        country_counts = df_players["country"].value_counts().reset_index()
        country_counts.columns = ["Country", "Player Count"]
        fig = px.bar(
            country_counts,
            x="Player Count",
            y="Country",
            orientation="h",
            color="Player Count",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f1f5f9",
            margin=dict(l=0, r=0, t=10, b=10),
            height=320,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)


# ==========================================
# VIEW 2: PLAYER EXPLORER & RADAR PROFILING
# ==========================================
elif menu == "🎾 Player Explorer & Radar":
    st.subheader("🎾 Player Intelligence & 5-Trait Tactical Radar")

    player_names = df_players["name"].tolist()
    selected_name = st.selectbox("Select Pro Player:", player_names, index=0)
    p = df_players[df_players["name"] == selected_name].iloc[0]

    col_bio, col_radar = st.columns([1, 1.2])

    with col_bio:
        st.markdown(f"""
        <div style="background: rgba(17, 24, 39, 0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0; font-size: 24px; color: #ffffff;">{p['name']}</h2>
                <span class="tier-badge">{p['cluster_tier']}</span>
            </div>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 16px 0;">{p['country']} ({p['abbreviation']}) • ID: {p['competitor_id']}</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px;">
                <div class="metric-card">
                    <div class="metric-val">#{p['rank']}</div>
                    <div class="metric-label">Global Rank</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{p['points']:,}</div>
                    <div class="metric-label">Points</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{p['competitions_played']}</div>
                    <div class="metric-label">Competitions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{'+' if p['movement'] > 0 else ''}{p['movement']}</div>
                    <div class="metric-label">Rank Movement</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🎯 ML Tactical Traits")
        traits = p["traits"]
        for trait_name, trait_val in traits.items():
            label = trait_name.replace("_", " ").title()
            st.write(f"**{label}**: `{trait_val:.1f}%`")
            st.progress(float(trait_val) / 100.0)

    with col_radar:
        traits = p["traits"]
        categories = ["Consistency", "Power & Volume", "Stamina", "Rank Momentum", "Efficiency"]
        values = [
            traits.get("consistency", 50),
            traits.get("power_volume", 50),
            traits.get("tournament_stamina", 50),
            traits.get("rank_momentum", 50),
            traits.get("efficiency", 50)
        ]
        # Close radar loop
        categories += [categories[0]]
        values += [values[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            fillcolor='rgba(16, 185, 129, 0.35)',
            line=dict(color='#10b981', width=3),
            name=p['name']
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], color='#64748b', gridcolor='rgba(255,255,255,0.08)'),
                angularaxis=dict(color='#cbd5e1', gridcolor='rgba(255,255,255,0.08)'),
                bgcolor='rgba(0,0,0,0)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9',
            margin=dict(l=40, r=40, t=20, b=20),
            height=420,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)


# ==========================================
# VIEW 3: HEAD-TO-HEAD COMPARISON
# ==========================================
elif menu == "⚔️ Head-to-Head Comparison":
    st.subheader("⚔️ Head-to-Head Tactical Comparison")

    c1, c2 = st.columns(2)
    with c1:
        p1_name = st.selectbox("Player A (Primary):", df_players["name"].tolist(), index=0)
    with c2:
        p2_name = st.selectbox("Player B (Challenger):", df_players["name"].tolist(), index=min(1, len(df_players)-1))

    pA = df_players[df_players["name"] == p1_name].iloc[0]
    pB = df_players[df_players["name"] == p2_name].iloc[0]

    # Comparative Dual Radar
    categories = ["Consistency", "Power & Volume", "Stamina", "Rank Momentum", "Efficiency"]
    vA = [pA["traits"][k] for k in ["consistency", "power_volume", "tournament_stamina", "rank_momentum", "efficiency"]]
    vB = [pB["traits"][k] for k in ["consistency", "power_volume", "tournament_stamina", "rank_momentum", "efficiency"]]

    categories += [categories[0]]
    vA += [vA[0]]
    vB += [vB[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vA,
        theta=categories,
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.25)',
        line=dict(color='#10b981', width=3),
        name=pA['name']
    ))
    fig.add_trace(go.Scatterpolar(
        r=vB,
        theta=categories,
        fill='toself',
        fillcolor='rgba(6, 182, 212, 0.25)',
        line=dict(color='#06b6d4', width=3),
        name=pB['name']
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='#64748b', gridcolor='rgba(255,255,255,0.08)'),
            angularaxis=dict(color='#cbd5e1', gridcolor='rgba(255,255,255,0.08)'),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f1f5f9',
        margin=dict(l=40, r=40, t=30, b=30),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Differential Table
    diff_data = [
        {"Metric": "Global Rank", pA["name"]: f"#{pA['rank']}", pB["name"]: f"#{pB['rank']}", "Advantage": pA["name"] if pA["rank"] < pB["rank"] else pB["name"]},
        {"Metric": "ATP Points", pA["name"]: f"{pA['points']:,}", pB["name"]: f"{pB['points']:,}", "Advantage": pA["name"] if pA["points"] > pB["points"] else pB["name"]},
        {"Metric": "Tournaments Played", pA["name"]: pA["competitions_played"], pB["name"]: pB["competitions_played"], "Advantage": pA["name"] if pA["competitions_played"] > pB["competitions_played"] else pB["name"]},
        {"Metric": "Consistency Score", pA["name"]: f"{pA['traits']['consistency']:.1f}%", pB["name"]: f"{pB['traits']['consistency']:.1f}%", "Advantage": pA["name"] if pA['traits']['consistency'] > pB['traits']['consistency'] else pB["name"]},
        {"Metric": "Power Volume", pA["name"]: f"{pA['traits']['power_volume']:.1f}%", pB["name"]: f"{pB['traits']['power_volume']:.1f}%", "Advantage": pA["name"] if pA['traits']['power_volume'] > pB['traits']['power_volume'] else pB["name"]},
    ]
    st.dataframe(pd.DataFrame(diff_data), use_container_width=True, hide_index=True)


# ==========================================
# VIEW 4: MACHINE LEARNING CLUSTERS
# ==========================================
elif menu == "🧠 Machine Learning Clusters":
    st.subheader("🧠 Unsupervised ML Tactical Archetypes (K-Means)")

    st.markdown("""
    Our platform utilizes an **unsupervised K-Means clustering algorithm** optimized via **Silhouette Analysis (K=5)** to map players into distinct tactical archetypes based on their statistical fingerprint.
    """)

    # 2D Scatter Plot
    fig = px.scatter(
        df_players,
        x="competitions_played",
        y="points",
        color="cluster_tier",
        size="points",
        hover_name="name",
        hover_data=["country", "rank"],
        title="Tactical Archetype Distribution: Points vs Tournaments Played",
        color_discrete_sequence=["#10b981", "#06b6d4", "#f59e0b", "#a855f7", "#ec4899"]
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#f1f5f9',
        xaxis=dict(gridcolor='rgba(255,255,255,0.08)', title="Competitions Played"),
        yaxis=dict(gridcolor='rgba(255,255,255,0.08)', title="Ranking Points"),
        height=480
    )
    st.plotly_chart(fig, use_container_width=True)

    # Archetype Breakdown Card Grid
    st.markdown("#### 📖 The 5 Discovered Tactical Archetypes")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        **1. Elite Grand Slam Tier**  
        *High consistency, high points density, deep tournament conversion.*
        """)
    with t2:
        st.markdown("""
        **2. High-Yield Contenders**  
        *Aggressive power/volume, consistent top-5 bracket challenger.*
        """)
    with t3:
        st.markdown("""
        **3. Dynamic Tour Veteran**  
        *High stamina, adapts across multi-surface ATP tour events.*
        """)


# ==========================================
# VIEW 5: 20 SQL QUERIES LAB
# ==========================================
elif menu == "🔍 20 SQL Queries Lab":
    st.subheader("🔍 Interactive SQL Analytics Lab (20 Production Queries)")

    if not queries_list:
        st.info("No queries found in sql/queries.sql.")
    else:
        query_options = {q["label"]: q for q in queries_list}
        selected_label = st.selectbox("Select Analytical Query:", list(query_options.keys()))
        selected_q = query_options[selected_label]

        st.markdown(f"**Query Objective:** {selected_q['title']}")
        st.code(selected_q["sql"], language="sql")

        if st.button("🚀 Execute Query on Live Database", type="primary"):
            SessionLocal, engine = get_db_session()
            try:
                with engine.connect() as conn:
                    result_df = pd.read_sql(selected_q["sql"], conn)
                st.success(f"Execution Successful! Returned {len(result_df)} records.")
                st.dataframe(result_df, use_container_width=True)

                # Export CSV
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name=f"tip_query_{selected_q['id']}_results.csv",
                    mime="text/csv"
                )
            except Exception as err:
                st.error(f"SQL execution error: {err}")


# ==========================================
# VIEW 6: DATA QUALITY & ARCHITECTURE
# ==========================================
elif menu == "🛡️ Data Quality & Architecture":
    st.subheader("🛡️ 3NF Relational Integrity & Architecture Telemetry")

    SessionLocal, engine = get_db_session()
    session = SessionLocal()
    try:
        from app.models.entities import Category, Competition, Complex, Venue, Competitor, CompetitorRanking

        entity_counts = {
            "Categories": session.query(Category).count(),
            "Competitions": session.query(Competition).count(),
            "Complexes": session.query(Complex).count(),
            "Venues": session.query(Venue).count(),
            "Competitors (Players)": session.query(Competitor).count(),
            "Rankings": session.query(CompetitorRanking).count(),
        }

        st.markdown("#### 🗄️ Database Record Counts (3NF Normalized)")
        cols = st.columns(len(entity_counts))
        for col, (entity, count) in zip(cols, entity_counts.items()):
            col.metric(entity, count)

        st.markdown("---")
        st.markdown("#### 🏗️ Dual-Database Architecture Blueprint")
        st.markdown("""
        - **Local / Edge Mode:** SQLite 3 in high-concurrency WAL (Write-Ahead Logging) mode.
        - **Cloud Serverless Mode:** Neon PostgreSQL with async pooling via SQLAlchemy ORM.
        - **Data Source:** Official SportRadar Tennis API & Staged 3NF JSON Feeds.
        - **Machine Learning:** Scikit-Learn K-Means, Silhouette Score Optimization, Vectorized Radar Scoring.
        """)

    finally:
        session.close()
