# frontend/app.py - Version completement corrigee
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.audio.speech_to_text import SpeechToTextConverter
from backend.ner.spacy_ner import SpacyNERExtractor
from backend.ner.llm_ner import LLMNERExtractor
from backend.database.db_manager import DatabaseManager


def clean_arabic_text(text: str) -> str:
    """Nettoie le texte arabe des caracteres problematiques."""
    if not text:
        return ""
    # Garder seulement arabe, chiffres, espaces
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Voice-to-Calorie",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">

<style>
:root {
  --bg:        #F7FBF4;
  --bg2:       #EEF7E8;
  --white:     #FFFFFF;
  --lime:      #A8E063;
  --lime-deep: #7CC63A;
  --mint:      #3DDC97;
  --mint-deep: #23B87A;
  --coral:     #FF6B6B;
  --amber:     #FFB347;
  --sky:       #5BC8FB;
  --ink:       #0F1F0E;
  --ink2:      #2A3D28;
  --muted:     #7A9478;
  --border:    #D8EDCC;
  --shadow:    rgba(60,140,60,.08);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Bricolage Grotesque', sans-serif;
    background: var(--bg) !important;
    color: var(--ink);
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--lime-deep); border-radius: 99px; }

section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1.5px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }

.sb-brand {
    padding: 1.6rem 1.4rem 1rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: .6rem;
}
.sb-brand-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, var(--lime) 0%, var(--mint) 100%);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
    box-shadow: 0 4px 14px rgba(168,224,99,.4);
}
.sb-brand-name {
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--ink2);
}
.sb-brand-tagline {
    font-size: .6rem;
    color: var(--muted);
    letter-spacing: .06em;
}

.sb-section { padding: 1rem 1.2rem .5rem; }
.sb-label {
    font-size: .62rem;
    font-weight: 700;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--mint-deep);
    margin-bottom: .7rem;
    display: flex; align-items: center; gap: .35rem;
}
.sb-label::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
}

.sb-stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: .5rem;
    margin-bottom: .6rem;
}
.sb-stat-tile {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: .75rem .8rem;
    text-align: center;
}
.sb-stat-tile .val {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--ink2);
    line-height: 1;
}
.sb-stat-tile .lbl {
    font-size: .6rem;
    font-weight: 600;
    letter-spacing: .09em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: .25rem;
}
.sb-stat-tile.accent-lime { border-color: var(--lime); background: #F3FCE8; }
.sb-stat-tile.accent-mint { border-color: var(--mint); background: #EAFAF3; }

.hero-wrap {
    position: relative;
    border-radius: 28px;
    overflow: hidden;
    margin-bottom: 1.5rem;
    background: var(--ink2);
    padding: 3rem 3rem 2.5rem;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 2rem;
    min-height: 200px;
}
.hero-wrap::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 55% 80% at 15% 120%, rgba(168,224,99,.55) 0%, transparent 60%),
        radial-gradient(ellipse 40% 60% at 85% -10%, rgba(61,220,151,.45) 0%, transparent 55%),
        radial-gradient(ellipse 30% 50% at 50% 110%, rgba(255,107,107,.2) 0%, transparent 55%);
    pointer-events: none;
}
.hero-wrap::after {
    content: "";
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,.07) 1px, transparent 1px);
    background-size: 22px 22px;
    pointer-events: none;
}
.hero-left { position: relative; z-index: 1; }
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    background: rgba(255,255,255,.12);
    backdrop-filter: blur(6px);
    border: 1px solid rgba(255,255,255,.18);
    border-radius: 999px;
    padding: .22rem .75rem;
    font-size: .65rem;
    font-weight: 600;
    letter-spacing: .13em;
    text-transform: uppercase;
    color: var(--lime);
    margin-bottom: .9rem;
}
.hero-title {
    font-family: 'Instrument Serif', serif;
    font-style: italic;
    font-size: clamp(2.4rem, 4.5vw, 3.8rem);
    font-weight: 400;
    line-height: 1;
    color: var(--white);
    letter-spacing: -.02em;
    margin-bottom: .5rem;
}
.hero-title span {
    background: linear-gradient(100deg, var(--lime) 0%, var(--mint) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: .95rem;
    color: rgba(255,255,255,.55);
    direction: rtl;
    font-weight: 400;
}
.hero-right {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: .5rem;
}
.hero-badge {
    background: rgba(255,255,255,.1);
    border: 1px solid rgba(255,255,255,.15);
    backdrop-filter: blur(8px);
    border-radius: 16px;
    padding: .8rem 1.2rem;
    text-align: center;
    min-width: 100px;
}
.hero-badge .num {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--lime);
    line-height: 1;
}
.hero-badge .sub {
    font-size: .62rem;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: rgba(255,255,255,.45);
    margin-top: .2rem;
}

.panel {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 24px;
    padding: 1.6rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 16px var(--shadow);
    transition: box-shadow .2s;
}
.panel:hover { box-shadow: 0 6px 24px var(--shadow); }
.panel-header {
    display: flex;
    align-items: center;
    gap: .55rem;
    margin-bottom: 1.1rem;
}
.panel-icon {
    width: 32px; height: 32px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: .9rem;
    flex-shrink: 0;
}
.panel-icon.green { background: linear-gradient(135deg, var(--lime) 0%, var(--mint) 100%); }
.panel-icon.blue  { background: linear-gradient(135deg, var(--sky) 0%, #3B6EEF 100%); }
.panel-title {
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--ink2);
}

.macro-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: .65rem;
    margin: 1.25rem 0;
}
.macro-card {
    border-radius: 20px;
    padding: 1.1rem .8rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform .2s;
}
.macro-card::before {
    content: "";
    position: absolute;
    inset: 0;
    opacity: .12;
    background: radial-gradient(ellipse at 50% 0%, white, transparent 70%);
}
.macro-card:hover { transform: translateY(-3px); }
.macro-cal  { background: linear-gradient(145deg, #3DDC97 0%, #23B87A 100%); }
.macro-prot { background: linear-gradient(145deg, #5BC8FB 0%, #2F86D9 100%); }
.macro-gluc { background: linear-gradient(145deg, #FFB347 0%, #F07830 100%); }
.macro-lip  { background: linear-gradient(145deg, #FF6B6B 0%, #D93F3F 100%); }

.macro-card .macro-val {
    font-size: 1.7rem;
    font-weight: 800;
    color: white;
    line-height: 1;
}
.macro-card .macro-unit {
    font-size: .62rem;
    color: rgba(255,255,255,.7);
    margin-top: .15rem;
}
.macro-card .macro-label {
    font-size: .65rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: rgba(255,255,255,.85);
    margin-top: .4rem;
}

.food-badge {
    display: inline-flex;
    align-items: center;
    gap: .3rem;
    background: var(--bg2);
    border: 1.5px solid var(--border);
    border-radius: 999px;
    padding: .28rem .75rem;
    font-size: .77rem;
    font-weight: 600;
    color: var(--ink2);
    margin: .2rem;
    transition: all .18s;
    cursor: default;
}
.food-badge:hover {
    background: var(--lime);
    border-color: var(--lime-deep);
    color: var(--ink);
    transform: scale(1.04);
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    padding: .35rem 1rem;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 600;
}
.pill-success { background: #D0FAEA; color: #0B6B40; border: 1.5px solid #8DE8BE; }
.pill-error   { background: #FFE5E5; color: #961818; border: 1.5px solid #FFAAAA; }
.pill-info    { background: #E0F3FE; color: #0E4F80; border: 1.5px solid #90D4FA; }

.stButton > button {
    background: linear-gradient(135deg, var(--lime-deep) 0%, var(--mint-deep) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-weight: 700 !important;
    font-size: .85rem !important;
    letter-spacing: .03em !important;
    padding: .6rem 1.3rem !important;
    transition: all .2s !important;
    box-shadow: 0 4px 16px rgba(124,198,58,.3) !important;
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg, var(--mint-deep) 0%, #0F8055 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(61,220,151,.4) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

.danger-btn > button {
    background: #FFF0F0 !important;
    color: #C02020 !important;
    border: 1.5px solid #FFCCCC !important;
    box-shadow: none !important;
}
.danger-btn > button:hover {
    background: #FFE0E0 !important;
    transform: none !important;
    box-shadow: none !important;
}

.stSelectbox > div > div,
.stTextArea textarea,
.stTextInput input {
    background: var(--bg) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--ink) !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-size: .9rem !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: var(--mint) !important;
    box-shadow: 0 0 0 3px rgba(61,220,151,.18) !important;
}
.stTextArea textarea { min-height: 110px !important; }

.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: linear-gradient(135deg, var(--lime-deep), var(--mint)) !important;
    box-shadow: 0 2px 8px rgba(61,220,151,.35) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1.5px solid var(--border);
    gap: .2rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border: none !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-weight: 600 !important;
    font-size: .83rem !important;
    padding: .75rem 1.3rem !important;
    border-bottom: 2.5px solid transparent !important;
    transition: all .2s !important;
}
.stTabs [aria-selected="true"] {
    color: var(--mint-deep) !important;
    border-bottom-color: var(--mint-deep) !important;
}

.streamlit-expanderHeader {
    background: var(--bg) !important;
    border-radius: 12px !important;
    color: var(--ink2) !important;
    font-size: .84rem !important;
    font-weight: 600 !important;
    border: 1px solid var(--border) !important;
}

.stDataFrame {
    border: 1.5px solid var(--border) !important;
    border-radius: 16px !important;
    overflow: hidden;
}

[data-testid="metric-container"] {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 16px;
    padding: .8rem 1rem !important;
}

.stCodeBlock {
    background: var(--bg) !important;
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
}

.example-card {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 16px;
    padding: .9rem 1rem;
    margin-bottom: .55rem;
    transition: all .18s;
    cursor: default;
}
.example-card:hover {
    border-color: var(--lime-deep);
    background: var(--bg2);
    transform: translateX(3px);
}

.hr { border: none; border-top: 1.5px solid var(--border); margin: 1.2rem 0; }
#MainMenu, footer, header { visibility: hidden; }
.stSpinner > div > div { border-top-color: var(--mint) !important; }
.stCaption { color: var(--muted) !important; font-size: .75rem !important; }
.stAlert { border-radius: 14px !important; }
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
        'text_to_analyze': None,
        'last_nutrition': None,
        'last_entities': None,
        'last_method': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-icon">🥑</div>
        <div>
            <div class="sb-brand-name">Voice-to-Calorie</div>
            <div class="sb-brand-tagline">Arabic NLP · Nutrition AI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-label">⚙ Moteur NER</div></div>', unsafe_allow_html=True)

    extraction_method = st.selectbox(
        "Moteur NER",
        ["spaCy", "LLM (OpenAI)"],
        label_visibility="collapsed",
    )

    if extraction_method == "LLM (OpenAI)":
        api_key = st.text_input("Clé OpenAI API", type="password", placeholder="sk-…")
        if api_key and st.session_state.llm_extractor is None:
            st.session_state.llm_extractor = LLMNERExtractor(api_key)

    stats = st.session_state.db.get_statistics()

    st.markdown('<div class="sb-section"><div class="sb-label">📊 Statistiques</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding: 0 1.2rem 1rem;">
        <div class="sb-stat-grid">
            <div class="sb-stat-tile accent-lime">
                <div class="val">{stats["total_meals"]}</div>
                <div class="lbl">Total repas</div>
            </div>
            <div class="sb-stat-tile accent-mint">
                <div class="val">{stats["voice_meals"]}</div>
                <div class="lbl">Par voix</div>
            </div>
        </div>
        <div class="sb-stat-grid">
            <div class="sb-stat-tile">
                <div class="val" style="font-size:1.15rem;color:#23B87A;">{stats["avg_calories"]:.0f}</div>
                <div class="lbl">Cal. moy. (kcal)</div>
            </div>
            <div class="sb-stat-tile">
                <div class="val" style="font-size:1.15rem;color:#2F86D9;">{stats.get("avg_proteines", 0):.1f}g</div>
                <div class="lbl">Prot. moy.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='danger-btn' style='padding:0 1.2rem 1.2rem'>", unsafe_allow_html=True)
    if st.button("🗑 Effacer l'historique", use_container_width=True):
        st.session_state.db.delete_all()
        st.session_state.voice_text = None
        st.session_state.text_to_analyze = None
        st.session_state.last_nutrition = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
stats_hero = st.session_state.db.get_statistics()
st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-left">
        <div class="hero-eyebrow">🎙 Nutrition intelligente</div>
        <div class="hero-title">Voice-to-<span>Calorie</span></div>
        <div class="hero-sub">تحدث عن وجبتك · تحليل فوري للسعرات الحرارية</div>
    </div>
    <div class="hero-right">
        <div class="hero-badge">
            <div class="num">{stats_hero["total_meals"]}</div>
            <div class="sub">repas enregistrés</div>
        </div>
        <div class="hero-badge">
            <div class="num" style="color:#3DDC97;">{stats_hero["avg_calories"]:.0f}</div>
            <div class="sub">kcal moyenne</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Input zone ────────────────────────────────────────────────────────────────
col_voice, col_text = st.columns(2, gap="medium")

# ─── Colonne VOIX ─────────────────────────────────────────────────────────────
with col_voice:
    st.markdown("""
    <div class="panel">
        <div class="panel-header">
            <div class="panel-icon green">🎙</div>
            <div class="panel-title">Enregistrement vocal</div>
        </div>
    """, unsafe_allow_html=True)

    duration = st.slider("Durée (s)", 3, 10, 5, label_visibility="collapsed")
    st.caption(f"⏱ Durée d'écoute : **{duration} s** — parlez en arabe")

    if st.button("⬤  Démarrer l'enregistrement", use_container_width=True):
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
        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
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

# ─── Colonne TEXTE (CORRIGEE) ─────────────────────────────────────────────────
with col_text:
    st.markdown("""
    <div class="panel">
        <div class="panel-header">
            <div class="panel-icon blue">⌨</div>
            <div class="panel-title">Saisie textuelle</div>
        </div>
    """, unsafe_allow_html=True)

    text_input = st.text_area(
        "Décrivez votre repas en arabe",
        placeholder="أكلت نصف بيتزا وشربت كوب حليب…",
        height=108,
        label_visibility="collapsed",
        key="text_input_area"
    )
    st.caption("✍ Écrivez en arabe · Exemples dans l'onglet ci-dessous")

    # Bouton analyse
    if st.button("Analyser le texte →", use_container_width=True, key="btn_text_analyze"):
        if not text_input or not text_input.strip():
            st.warning("Veuillez saisir un texte.")
        else:
            # Stocker dans session_state pour traitement apres rerun
            st.session_state.text_to_analyze = clean_arabic_text(text_input)
            st.rerun()

    # Traitement du texte (apres rerun)
    if st.session_state.text_to_analyze:
        with st.spinner("Analyse en cours..."):
            try:
                txt = st.session_state.text_to_analyze
                
                if extraction_method == "spaCy":
                    entities, nutrition, proc_time = st.session_state.spacy_extractor.process(txt)
                    method = "spaCy"
                else:
                    if not st.session_state.llm_extractor:
                        st.error("Saisir la clé OpenAI")
                        st.session_state.text_to_analyze = None
                        st.stop()
                    entities, nutrition, proc_time = st.session_state.llm_extractor.process(txt)
                    method = "LLM"

                # Sauvegarde
                st.session_state.db.save_meal(txt, nutrition, method, is_voice=False)
                st.session_state.db.log_performance(method, proc_time, 0, len(entities.get("foods", [])))
                
                # Stocker les resultats
                st.session_state.last_nutrition = nutrition
                st.session_state.last_entities = entities
                st.session_state.last_method = method
                
                # Reset
                st.session_state.text_to_analyze = None
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Erreur: {str(e)}")
                st.session_state.text_to_analyze = None

    st.markdown("</div>", unsafe_allow_html=True)

# ── Results panel ─────────────────────────────────────────────────────────────
if st.session_state.last_nutrition:
    nut = st.session_state.last_nutrition
    ent = st.session_state.last_entities or {}
    method_tag = st.session_state.last_method or "–"

    st.markdown(f'<span class="pill pill-success">✓ Analyse réussie — moteur : {method_tag}</span>', unsafe_allow_html=True)
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

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

    fig = go.Figure(go.Pie(
        labels=["Protéines", "Glucides", "Lipides"],
        values=[nut["proteines"], nut["glucides"], nut["lipides"]],
        hole=0.72,
        marker=dict(
            colors=["#5BC8FB", "#FFB347", "#FF6B6B"],
            line=dict(color="#FFFFFF", width=3),
        ),
        textinfo="none",
    ))
    fig.update_layout(
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Bricolage Grotesque", color="#7A9478", size=11),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12,
                    font=dict(color="#2A3D28")),
        margin=dict(t=10, b=10, l=10, r=10),
        height=210,
        annotations=[dict(
            text=f"<b>{nut['calories']:.0f}</b><br><span style='font-size:10px'>kcal</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False,
            font_color="#0F1F0E",
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Tabs ──────────────────────────────────────────────────────────────────────
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
            color_discrete_sequence=["#3DDC97"],
        )
        fig_line.update_traces(
            line=dict(width=2.5),
            fill="tozeroy",
            fillcolor="rgba(61,220,151,.08)",
        )
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Bricolage Grotesque", color="#7A9478"),
            title_font=dict(family="Bricolage Grotesque", color="#0F1F0E", size=15),
            xaxis=dict(showgrid=False, color="#7A9478"),
            yaxis=dict(showgrid=True, gridcolor="#D8EDCC", color="#7A9478"),
            margin=dict(t=45, b=20, l=0, r=0),
        )
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

        stats_all = st.session_state.db.get_statistics()
        fig_pie = px.pie(
            values=[stats_all["avg_proteines"], stats_all["avg_glucides"], stats_all["avg_lipides"]],
            names=["Protéines", "Glucides", "Lipides"],
            title="Répartition moyenne des macronutriments",
            hole=0.55,
            color_discrete_sequence=["#5BC8FB", "#FFB347", "#FF6B6B"],
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Bricolage Grotesque", color="#7A9478"),
            title_font=dict(family="Bricolage Grotesque", color="#0F1F0E", size=15),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.08),
            margin=dict(t=45, b=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Pas encore assez de données — enregistrez quelques repas !")

with tab3:
    examples = [
        ("Repas léger",   "أكلت نصف بيتزا"),
        ("Boisson",       "شربت كوبًا كبيرًا من العصير"),
        ("Déjeuner",      "أكلت صحنًا متوسطًا من المعكرونة"),
        ("Snack",         "تناولت ملعقة عسل"),
        ("Plat marocain", "تناولت طاجين دجاج بالزيتون"),
        ("Couscous",      "أكلت كسكس باللحم والخضر"),
        ("Sandwich",      "تناولت ساندويتش دجاج مع بطاطس"),
        ("Petit déj.",    "أكلت 2 بيضات و3 شرائح خبز"),
        ("Salade",        "تناولت طبقًا كبيرًا من السلطة"),
        ("Fruits",        "أكلت تفاحة وموزة"),
        ("Légumes",       "أكلت بعض البطاطس"),
        ("Lait",          "شربت نصف كوب حليب"),
        ("Viande",        "أكلت كمية قليلة من اللحم"),
        ("Gâteau",        "أكلت قطعة صغيرة من الكعك"),
        ("Riz",           "تناولت قليلًا من الأرز"),
    ]
    cols = st.columns(3)
    for i, (cat, ex) in enumerate(examples):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="example-card">
                <div style="font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
                            color:#23B87A;margin-bottom:.3rem;font-weight:700;">{cat}</div>
                <div style="font-size:.88rem;color:#0F1F0E;direction:rtl;text-align:right;
                            line-height:1.5;">{ex}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1.2rem;color:#B8D4B0;
            font-size:.7rem;letter-spacing:.12em;font-weight:500;">
    🥑 VOICE-TO-CALORIE · Arabic NLP Nutrition Tracker · Powered by AI
</div>
""", unsafe_allow_html=True)