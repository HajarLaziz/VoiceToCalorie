# frontend/app.py - Version couleurs fraîches (sans noir/violet)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.audio.speech_to_text import SpeechToTextConverter
from backend.ner.spacy_ner import SpacyNERExtractor
from backend.ner.llm_ner import LLMNERExtractor
from backend.database.db_manager import DatabaseManager

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Voice-to-Calorie",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system - Fresh colors (Green/Blue/Orange/White) ───────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap" rel="stylesheet">

<style>
/* ── Reset & base ── */
* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #F0F7F4;
    color: #1A2E2A;
}

/* ── Sidebar fresh ── */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #D1E8E0;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #2D9C7A;
    margin-top: 1.5rem;
}

/* ── Hero fresh ── */
.hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 3.5rem 2rem 2.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #E8F5F0 0%, #D1E8E0 100%);
    border-radius: 24px;
    margin-bottom: 1rem;
}
.hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 70% 55% at 50% -10%, rgba(45,156,122,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero-label {
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #2D9C7A;
    margin-bottom: 0.75rem;
    font-weight: 600;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.5rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.05;
    background: linear-gradient(135deg, #1A5D4A 30%, #2D9C7A 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.75rem;
}
.hero-sub {
    color: #4A7C6A;
    font-size: 0.95rem;
    font-weight: 500;
    direction: rtl;
    font-size: 1rem;
}

/* ── Divider ── */
.divider {
    border: none;
    border-top: 1px solid #D1E8E0;
    margin: 1.5rem 0;
}

/* ── Panel / card fresh ── */
.panel {
    background: #FFFFFF;
    border: 1px solid #D1E8E0;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.panel-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.8rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2D9C7A;
    margin-bottom: 1rem;
}

/* ── Macro strip fresh ── */
.macro-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin: 1.25rem 0;
}
.macro-card {
    background: #F8FCFA;
    border: 1px solid #D1E8E0;
    border-radius: 16px;
    padding: 1rem;
    text-align: center;
    transition: all 0.2s;
}
.macro-card:hover { 
    border-color: #2D9C7A; 
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(45,156,122,0.1);
}
.macro-val {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #1A5D4A;
    line-height: 1;
}
.macro-unit {
    font-size: 0.7rem;
    color: #6B9A88;
    margin-top: 0.2rem;
}
.macro-label {
    font-size: 0.75rem;
    margin-top: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}
.macro-cal .macro-label { color: #2D9C7A; }
.macro-cal .macro-val { color: #1A5D4A; }
.macro-prot .macro-label { color: #3B82F6; }
.macro-prot .macro-val { color: #2563EB; }
.macro-gluc .macro-label { color: #F59E0B; }
.macro-gluc .macro-val { color: #D97706; }
.macro-lip .macro-label { color: #EF4444; }
.macro-lip .macro-val { color: #DC2626; }

/* ── Detected foods badge row fresh ── */
.food-badge {
    display: inline-block;
    background: #E8F5F0;
    border: 1px solid #C5DDD3;
    border-radius: 999px;
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    color: #1A5D4A;
    margin: 0.25rem;
    font-weight: 500;
}
.food-badge:hover {
    background: #2D9C7A;
    color: white;
    border-color: #2D9C7A;
}

/* ── Status pill fresh ── */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}
.pill-success { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }
.pill-error   { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
.pill-info    { background: #DBEAFE; color: #1E40AF; border: 1px solid #BFDBFE; }

/* ── Stat row in sidebar fresh ── */
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.45rem 0;
    border-bottom: 1px solid #D1E8E0;
}
.stat-row:last-child { border-bottom: none; }
.stat-key   { font-size: 0.8rem; color: #6B9A88; font-weight: 500; }
.stat-value { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; color: #1A5D4A; }

/* ── Buttons fresh ── */
.stButton > button {
    background: linear-gradient(135deg, #2D9C7A 0%, #1A5D4A 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1A5D4A 0%, #0F3D30 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(45,156,122,0.35) !important;
}

/* Destructive button fresh */
.danger-btn > button {
    background: #FEF2F2 !important;
    color: #DC2626 !important;
    border: 1px solid #FEE2E2 !important;
}
.danger-btn > button:hover {
    background: #FEE2E2 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── Selectbox / inputs fresh ── */
.stSelectbox > div > div,
.stTextArea textarea,
.stTextInput input {
    background: #FFFFFF !important;
    border: 1px solid #D1E8E0 !important;
    border-radius: 12px !important;
    color: #1A2E2A !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #2D9C7A !important;
    box-shadow: 0 0 0 2px rgba(45,156,122,0.15) !important;
}

/* ── Slider fresh ── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #2D9C7A !important;
}

/* ── Tabs fresh ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #D1E8E0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B9A88 !important;
    border: none !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.7rem 1.4rem !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    color: #2D9C7A !important;
    border-bottom-color: #2D9C7A !important;
}

/* ── Expander fresh ── */
.streamlit-expanderHeader {
    background: #F8FCFA !important;
    border-radius: 12px !important;
    color: #1A5D4A !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}

/* ── Dataframe fresh ── */
.stDataFrame {
    border: 1px solid #D1E8E0 !important;
    border-radius: 14px !important;
    overflow: hidden;
}

/* ── Metric fresh ── */
[data-testid="metric-container"] {
    background: #F8FCFA;
    border: 1px solid #D1E8E0;
    border-radius: 14px;
    padding: 0.75rem 1rem !important;
}

/* ── Code block fresh ── */
.stCodeBlock { 
    background: #F8FCFA !important;
    border-radius: 12px !important;
    border: 1px solid #D1E8E0 !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Example cards fresh ── */
.example-card {
    background: #F8FCFA;
    border: 1px solid #D1E8E0;
    border-radius: 14px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.6rem;
    transition: all 0.2s;
}
.example-card:hover {
    border-color: #2D9C7A;
    background: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

# ── Session init ──────────────────────────────────────────────────────────────
def _init():
    defaults = {
        'db': DatabaseManager(),
        'speech_converter': SpeechToTextConverter(),
        'spacy_extractor': SpacyNERExtractor(),
        'llm_extractor': None,
        'voice_text': None,
        'voice_duration': 0,
        'last_nutrition': None,
        'last_entities': None,
        'last_method': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Sidebar fresh ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙ Paramètres")

    extraction_method = st.selectbox(
        "Moteur NER",
        ["spaCy", "LLM (OpenAI)"],
        label_visibility="collapsed",
    )

    if extraction_method == "LLM (OpenAI)":
        api_key = st.text_input("Clé OpenAI API", type="password", placeholder="sk-…")
        if api_key and st.session_state.llm_extractor is None:
            st.session_state.llm_extractor = LLMNERExtractor(api_key)

    st.markdown("## 📊 Statistiques")
    stats = st.session_state.db.get_statistics()

    st.markdown(f"""
    <div class="panel" style="padding:1rem;">
        <div class="stat-row">
            <span class="stat-key">Total repas</span>
            <span class="stat-value">{stats["total_meals"]}</span>
        </div>
        <div class="stat-row">
            <span class="stat-key">Par voix</span>
            <span class="stat-value">{stats["voice_meals"]}</span>
        </div>
        <div class="stat-row">
            <span class="stat-key">Calories moy.</span>
            <span class="stat-value">{stats["avg_calories"]:.0f} <small style="font-size:.65rem;color:#6B9A88;">kcal</small></span>
        </div>
        <div class="stat-row">
            <span class="stat-key">Prot. moy.</span>
            <span class="stat-value">{stats.get("avg_proteines", 0):.1f} <small style="font-size:.65rem;color:#6B9A88;">g</small></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='danger-btn'>", unsafe_allow_html=True)
    if st.button("🗑 Effacer l'historique", use_container_width=True):
        st.session_state.db.delete_all()
        st.session_state.voice_text = None
        st.session_state.last_nutrition = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Hero fresh ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-label">🎙 Nutrition intelligente</div>
    <div class="hero-title">Voice-to-Calorie</div>
    <div class="hero-sub">تحدث عن وجبتك · تحليل فوري للسعرات الحرارية</div>
</div>
""", unsafe_allow_html=True)

# ── Input zone ────────────────────────────────────────────────────────────────
col_voice, col_text = st.columns(2, gap="medium")

# ─── Colonne VOIX ─────────────────────────────────────────────────────────────
with col_voice:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">🎙 Enregistrement vocal</div>', unsafe_allow_html=True)

    duration = st.slider("Durée (s)", 3, 10, 5, label_visibility="collapsed")
    st.caption(f"Durée d'écoute : **{duration} s** — parlez en arabe")

    if st.button("⬤ Démarrer l'enregistrement", use_container_width=True):
        with st.spinner(f"Écoute en cours — {duration} s…"):
            try:
                text, voice_time = st.session_state.speech_converter.listen_and_convert(
                    duration=duration, language="ar-SA"
                )
                if text:
                    st.session_state.voice_text = text
                    st.session_state.voice_duration = voice_time
                else:
                    st.session_state.voice_text = None
                    st.markdown('<span class="pill pill-error">❌ Aucun texte reconnu</span>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<span class="pill pill-error">❌ {e}</span>', unsafe_allow_html=True)

    if st.session_state.voice_text:
        st.markdown("---")
        st.markdown("**Texte reconnu**")
        st.code(st.session_state.voice_text, language="text")
        st.markdown(
            f'<span class="pill pill-info">⏱ Temps parole : {st.session_state.voice_duration:.1f} s</span>',
            unsafe_allow_html=True,
        )

        if st.button("Analyser ce repas →", use_container_width=True, key="btn_voice_analyze"):
            with st.spinner("Analyse NER…"):
                try:
                    txt = st.session_state.voice_text
                    dur = st.session_state.voice_duration
                    if extraction_method == "spaCy":
                        entities, nutrition, proc_time = st.session_state.spacy_extractor.process(txt)
                        method = "spaCy"
                    else:
                        if not st.session_state.llm_extractor:
                            st.error("Saisir la clé OpenAI")
                            st.stop()
                        entities, nutrition, proc_time = st.session_state.llm_extractor.process(txt)
                        method = "LLM"

                    st.session_state.db.save_meal(txt, nutrition, method, is_voice=True, voice_text=txt)
                    st.session_state.db.log_performance(method, proc_time, dur, len(entities.get("foods", [])))
                    st.session_state.last_nutrition = nutrition
                    st.session_state.last_entities = entities
                    st.session_state.last_method = method
                    st.rerun()
                except Exception as e:
                    st.markdown(f'<span class="pill pill-error">❌ {e}</span>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ─── Colonne TEXTE ────────────────────────────────────────────────────────────
with col_text:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">⌨ Saisie textuelle</div>', unsafe_allow_html=True)

    text_input = st.text_area(
        "Décrivez votre repas en arabe",
        placeholder="أكلت نصف بيتزا وشربت كوب حليب…",
        height=108,
        label_visibility="collapsed",
    )
    st.caption("Ecrivez en arabe · Exemples disponibles dans l'onglet ci-dessous")

    if st.button("Analyser le texte →", use_container_width=True, key="btn_text_analyze"):
        if not text_input.strip():
            st.warning("Veuillez saisir un texte.")
        else:
            with st.spinner("Analyse NER…"):
                try:
                    if extraction_method == "spaCy":
                        entities, nutrition, proc_time = st.session_state.spacy_extractor.process(text_input)
                        method = "spaCy"
                    else:
                        if not st.session_state.llm_extractor:
                            st.error("Saisir la clé OpenAI")
                            st.stop()
                        entities, nutrition, proc_time = st.session_state.llm_extractor.process(text_input)
                        method = "LLM"

                    st.session_state.db.save_meal(text_input, nutrition, method, is_voice=False)
                    st.session_state.db.log_performance(method, proc_time, 0, len(entities.get("foods", [])))
                    st.session_state.last_nutrition = nutrition
                    st.session_state.last_entities = entities
                    st.session_state.last_method = method
                    st.rerun()
                except Exception as e:
                    st.markdown(f'<span class="pill pill-error">❌ {e}</span>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Results panel ─────────────────────────────────────────────────────────────
if st.session_state.last_nutrition:
    nut = st.session_state.last_nutrition
    ent = st.session_state.last_entities or {}
    method_tag = st.session_state.last_method or "–"

    st.markdown(f'<span class="pill pill-success">✓ Analyse réussie — moteur : {method_tag}</span>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown(f"""
    <div class="macro-strip">
        <div class="macro-card macro-cal">
            <div class="macro-val">{nut["calories"]:.0f}</div>
            <div class="macro-unit">kcal</div>
            <div class="macro-label">Calories</div>
        </div>
        <div class="macro-card macro-prot">
            <div class="macro-val">{nut["proteines"]:.1f}</div>
            <div class="macro-unit">g</div>
            <div class="macro-label">Protéines</div>
        </div>
        <div class="macro-card macro-gluc">
            <div class="macro-val">{nut["glucides"]:.1f}</div>
            <div class="macro-unit">g</div>
            <div class="macro-label">Glucides</div>
        </div>
        <div class="macro-card macro-lip">
            <div class="macro-val">{nut["lipides"]:.1f}</div>
            <div class="macro-unit">g</div>
            <div class="macro-label">Lipides</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    foods = ent.get("foods", [])
    if foods:
        badges = "".join(f'<span class="food-badge">🍽 {f}</span>' for f in foods)
        st.markdown(f"<div style='margin:.5rem 0'>{badges}</div>", unsafe_allow_html=True)

    with st.expander("Détails complets de l'analyse"):
        if ent.get("quantities"):
            st.write("**Quantités détectées :**", ", ".join(ent.get("quantities", [])))
        raw = ent.get("raw_text", "")
        if raw:
            st.markdown(f"**Texte original :** `{raw}`")

    # Mini donut chart fresh
    fig = go.Figure(go.Pie(
        labels=["Protéines", "Glucides", "Lipides"],
        values=[nut["proteines"], nut["glucides"], nut["lipides"]],
        hole=0.72,
        marker=dict(colors=["#3B82F6", "#F59E0B", "#EF4444"],
                    line=dict(color="#F0F7F4", width=3)),
        textinfo="none",
    ))
    fig.update_layout(
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#6B9A88", size=11),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.1),
        margin=dict(t=10, b=10, l=10, r=10),
        height=200,
        annotations=[dict(
            text=f"<b>{nut['calories']:.0f}</b><br><span style='font-size:10px'>kcal</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False, font_color="#1A5D4A"
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Tabs fresh ────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📜 Historique", "📈 Évolution", "💡 Exemples arabes"])

with tab1:
    meals = st.session_state.db.get_all_meals(limit=50)
    if meals:
        df = pd.DataFrame(
            meals,
            columns=["ID", "Date", "Texte", "Voix", "Calories", "Prot", "Gluc", "Lip", "Méthode", "Voice", "Créé"],
        )
        st.dataframe(
            df[["Date", "Texte", "Calories", "Prot", "Gluc", "Lip", "Méthode"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucun repas enregistré pour l'instant.")

with tab2:
    daily = st.session_state.db.get_daily_totals(30)
    if daily:
        df_d = pd.DataFrame(daily, columns=["Date", "Calories", "Prot", "Gluc", "Lip"])
        fig_line = px.line(
            df_d, x="Date", y="Calories",
            title="Évolution quotidienne des calories",
            color_discrete_sequence=["#2D9C7A"],
        )
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans", color="#6B9A88"),
            title_font=dict(family="Syne", color="#1A5D4A", size=15),
            xaxis=dict(showgrid=False, color="#6B9A88"),
            yaxis=dict(showgrid=True, gridcolor="#D1E8E0", color="#6B9A88"),
            margin=dict(t=40, b=20, l=0, r=0),
        )
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

        stats_all = st.session_state.db.get_statistics()
        fig_pie = px.pie(
            values=[stats_all["avg_proteines"], stats_all["avg_glucides"], stats_all["avg_lipides"]],
            names=["Protéines", "Glucides", "Lipides"],
            title="Répartition moyenne des macronutriments",
            hole=0.55,
            color_discrete_sequence=["#3B82F6", "#F59E0B", "#EF4444"],
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans", color="#6B9A88"),
            title_font=dict(family="Syne", color="#1A5D4A", size=15),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.05),
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Pas encore assez de données — enregistrez quelques repas !")

with tab3:
    examples = [
        ("Repas léger", "أكلت نصف بيتزا"),
        ("Boisson", "شربت كوبًا كبيرًا من العصير"),
        ("Déjeuner", "أكلت صحنًا متوسطًا من المعكرونة"),
        ("Snack", "تناولت ملعقة عسل"),
        ("Plat marocain", "تناولت طاجين دجاج بالزيتون"),
        ("Couscous", "أكلت كسكس باللحم والخضر"),
        ("Sandwich", "تناولت ساندويتش دجاج مع بطاطس"),
        ("Petits déj.", "أكلت 2 بيضات و3 شرائح خبز"),
        ("Salade", "تناولت طبقًا كبيرًا من السلطة"),
        ("Fruits", "أكلت تفاحة وموزة"),
        ("Légumes", "أكلت بعض البطاطس"),
        ("Lait", "شربت نصف كوب حليب"),
        ("Viande", "أكلت كمية قليلة من اللحم"),
        ("Gâteau", "أكلت قطعة صغيرة من الكعك"),
        ("Riz", "تناولت قليلًا من الأرز"),
    ]
    cols = st.columns(3)
    for i, (cat, ex) in enumerate(examples):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="example-card">
                <div style="font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:#2D9C7A;margin-bottom:.3rem;font-weight:600;">{cat}</div>
                <div style="font-size:.9rem;color:#1A2E2A;direction:rtl;text-align:right;">{ex}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer fresh ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;color:#A8C4B8;font-size:.75rem;letter-spacing:.08em;">
    VOICE-TO-CALORIE &nbsp;·&nbsp; Arabic NLP Nutrition Tracker
</div>
""", unsafe_allow_html=True)