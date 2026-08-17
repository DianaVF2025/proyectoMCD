"""
Sistema de Recomendación Laboral — CNSC
Autores: Diana Vásquez · Germán Mahecha
Maestría en Ciencia de Datos
"""

import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import unicodedata
import re
import os
import warnings
warnings.filterwarnings("ignore")

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sistema de Recomendación CNSC",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_P  = "#1B3A6B"
COLOR_S  = "#2E86AB"
COLOR_A  = "#F5A623"
COLOR_OK = "#27AE60"
COLOR_F  = "#F7F9FC"

st.markdown(f"""
<style>
    .main {{ background-color: {COLOR_F}; }}
    h1, h2, h3 {{ color: {COLOR_P}; }}
    .block-container {{ padding-top: 1.5rem; }}
    .titulo {{
        background: linear-gradient(90deg, {COLOR_P}, {COLOR_S});
        color: white; padding: 0.55rem 1.1rem;
        border-radius: 6px; margin-bottom: 0.8rem;
    }}
    .card {{
        background: white; border-left: 4px solid {COLOR_S};
        padding: 0.9rem 1.1rem; border-radius: 6px; margin-bottom: 0.8rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
    }}
</style>
""", unsafe_allow_html=True)

# ── Jerarquía educativa exacta del notebook ───────────────────────────────────
JERARQUIA = {
    "EDUCACION BASICA PRIMARIA": 1,
    "EDUCACION BASICA SECUNDARIA": 2,
    "BACHILLER": 3,
    "NORMALISTA": 4,
    "TECNICO PROFESIONAL": 5,
    "TECNOLOGICO": 6,
    "PROFESIONAL": 7,
    "ESPECIALIZACION TECNICA PROFESIONAL": 8,
    "ESPECIALIZACION TECNOLOGICA": 9,
    "ESPECIALIZACION PROFESIONAL": 10,
    "MAESTRIA": 11,
    "DOCTORADO": 12,
    "POSTDOCTORADO": 13,
}

MODELO_FEATURES = [
    "total_formaciones", "cantidad_nbc", "cantidad_areas", "nivel_educativo_maximo",
    "cant_bachiller", "cant_doctorado", "cant_educacion_basica_primaria",
    "cant_educacion_basica_secundaria", "cant_educacion_informal",
    "cant_especializacion_profesional", "cant_especializacion_tecnica_profesional",
    "cant_especializacion_tecnologica", "cant_formacion_academica", "cant_formacion_laboral",
    "cant_formacion_penitenciaria", "cant_maestria", "cant_normalista", "cant_postdoctorado",
    "cant_profesional", "cant_tecnico_profesional", "cant_tecnologico",
    "tiene_posgrado", "tiene_formacion_complementaria", "perfil_multidisciplinario",
    "total_experiencias", "periodos_efectivos", "dias_experiencia_efectiva",
    "anios_experiencia_efectiva", "antiguedad_laboral_dias", "antiguedad_laboral_anios",
    "densidad_laboral", "duracion_promedio_experiencia", "duracion_maxima_experiencia",
    "duracion_minima_experiencia", "experiencia_amplia", "experiencia_extensa",
    "trayectoria_estable", "multiples_experiencias", "total_empleos_postulados",
    "participa_varios_concursos",
]

# ── Texto ─────────────────────────────────────────────────────────────────────
def normalizar(texto):
    if pd.isna(texto):
        return ""
    t = str(texto).upper()
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode("utf-8")
    t = re.sub(r"[^A-Z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def max_nivel(texto):
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    return max((JERARQUIA.get(p.strip(), 0) for p in str(texto).split("|")), default=0)

def obtener_titulo_coincidente(titulos_asp, titulos_vac):
    if pd.isna(titulos_asp) or pd.isna(titulos_vac):
        return None
    lista_a = [normalizar(x) for x in str(titulos_asp).split("|")]
    lista_v = [normalizar(x) for x in str(titulos_vac).split("|")]
    for ta in lista_a:
        for tv in lista_v:
            if ta and tv and ta == tv:
                return ta
    return None

# ── Carga de datos ────────────────────────────────────────────────────────────
MODO_COMPLETO = (
    os.path.exists("candidatos_completo.csv") and
    os.path.exists("vacantes_opec.csv")
)

@st.cache_data(show_spinner=False)
def cargar_datos():
    if MODO_COMPLETO:
        c = pd.read_csv("candidatos_completo.csv", low_memory=False)
        v = pd.read_csv("vacantes_opec.csv")
    else:
        c = pd.read_csv("ranking_final.csv")
        v = pd.read_csv("vacantes.csv")
    c.columns = c.columns.str.strip()
    v.columns = v.columns.str.strip()
    # Eliminar columna duplicada que Pandas genera al exportar desde Colab
    if "anios_experiencia_efectiva.1" in c.columns:
        c = c.drop(columns=["anios_experiencia_efectiva.1"])
    # Convertir nivel_educativo_maximo a numérico siempre:
    # el dtype en Python 3.14 puede ser 'str' en vez de 'object',
    # así que no usamos dtype == object sino que mapeamos directamente.
    if "nivel_educativo_maximo" in c.columns:
        c["nivel_educativo_maximo"] = (
            c["nivel_educativo_maximo"]
            .astype(str).str.strip().str.upper()
            .map(JERARQUIA)
            .fillna(0)
            .astype(float)
        )
    return c, v

@st.cache_resource(show_spinner=False)
def cargar_modelo():
    return joblib.load("modelo_arbol.pkl")

# Forzar recarga limpia para que la conversión numérica siempre aplique
cargar_datos.clear()
candidatos_df, vacantes_df = cargar_datos()
modelo = cargar_modelo()

# ── Pipeline de recomendación ─────────────────────────────────────────────────
def recomendar(candidatos, vacante_row):
    nivel_req = JERARQUIA.get(str(vacante_row["nivel_requerido"]).strip(), 0)
    titulos_v = str(vacante_row["titulos_requeridos"])
    exp_min   = float(vacante_row["experiencia_minima_meses"]) if pd.notna(vacante_row["experiencia_minima_meses"]) else 0.0

    df = candidatos.copy()

    # ── Regla 1: nivel educativo ──────────────────────────────────────────────
    if "nivel_educativo_texto" in df.columns:
        df["_niv"] = df["nivel_educativo_texto"].apply(max_nivel)
    else:
        df["_niv"] = 0
    df["R1_nivel"] = df["_niv"] >= nivel_req
    n_r1 = df["R1_nivel"].sum()

    # ── Regla 2: título coincidente ───────────────────────────────────────────
    titulos_v_limpio = titulos_v.strip()
    if not titulos_v_limpio or titulos_v_limpio.lower() in ("nan", "none", ""):
        # Sin títulos requeridos: todos los que pasan R1 pasan R2
        df["titulo_coincidente"] = None
        df["R2_titulo"] = df["R1_nivel"]
    else:
        if "titulos_principales" in df.columns:
            df["titulo_coincidente"] = df["titulos_principales"].apply(
                lambda x: obtener_titulo_coincidente(x, titulos_v_limpio)
            )
        elif "titulo_coincidente" not in df.columns:
            df["titulo_coincidente"] = None
        df["R2_titulo"] = df["R1_nivel"] & df["titulo_coincidente"].notna()
    n_r2 = df["R2_titulo"].sum()

    # ── Regla 3: experiencia mínima ───────────────────────────────────────────
    if "anios_experiencia_efectiva" in df.columns:
        df["experiencia_aspirante_meses"] = df["anios_experiencia_efectiva"] * 12
    elif "experiencia_aspirante_meses" not in df.columns:
        df["experiencia_aspirante_meses"] = 0
    df["R3_experiencia"] = df["R2_titulo"] & (df["experiencia_aspirante_meses"] >= exp_min)
    n_r3 = df["R3_experiencia"].sum()

    # ── Columna de estado por regla (visible en la tabla) ─────────────────────
    def estado_reglas(row):
        r1 = "S" if row["R1_nivel"] else "N"
        r2 = "S" if row["R2_titulo"] else ("—" if not row["R1_nivel"] else "N")
        r3 = "S" if row["R3_experiencia"] else ("—" if not row["R2_titulo"] else "N")
        return f"{r1} · {r2} · {r3}"

    df["cumple_reglas"] = df.apply(estado_reglas, axis=1)

    # ── Modelo predictivo (solo para elegibles) ────────────────────────────────
    df["indice_modelo"] = float("nan")
    elegibles_idx = df[df["R3_experiencia"]].index

    if len(elegibles_idx) > 0 and MODO_COMPLETO:
        r3 = df.loc[elegibles_idx].copy()
        features_ok = [f for f in MODELO_FEATURES if f in r3.columns]
        X = r3[features_ok].copy()

        if "nivel_educativo_maximo" in X.columns:
            X["nivel_educativo_maximo"] = (
                X["nivel_educativo_maximo"]
                .astype(str).str.strip().str.upper()
                .map(JERARQUIA)
                .fillna(0)
                .astype(float)
            )

        X = X.drop(columns=["fecha_primera_experiencia", "fecha_ultima_experiencia"],
                   errors="ignore")
        for col in X.columns:
            if X[col].dtype == object:
                X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)
        X = X.fillna(0)

        try:
            df.loc[elegibles_idx, "indice_modelo"] = modelo.predict_proba(X)[:, 1]
        except Exception as e:
            st.warning(f"Error al ejecutar el modelo: {e}")
            df.loc[elegibles_idx, "indice_modelo"] = 0.0

    # ── Ordenar: elegibles primero (modelo DESC, exp DESC), luego resto ────────
    elegibles  = df[df["R3_experiencia"]].sort_values(
        ["indice_modelo", "experiencia_aspirante_meses"], ascending=[False, False]
    )
    no_elegibles = df[~df["R3_experiencia"]].sort_values(
        "experiencia_aspirante_meses", ascending=False
    )
    ranking = pd.concat([elegibles, no_elegibles], ignore_index=True)
    ranking["puesto"] = range(1, len(ranking) + 1)

    return ranking, int(n_r1), int(n_r2), int(n_r3)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## 🏛️ CNSC")
    st.markdown("**Sistema de Recomendación Laboral**")

    if MODO_COMPLETO:
        st.success(f"✅ **Modo completo**  \n{len(candidatos_df):,} candidatos · {len(vacantes_df)} vacantes")
    else:
        st.warning("⚠️ Modo demo — 58 candidatos")

    st.markdown("---")

    # ── Selector de OPEC (global para todas las pestañas) ─────────────────────
    st.markdown("### Selecciona la OPEC")
    vacantes_df["_etiq"] = (
        "OPEC " + vacantes_df["opec"].astype(str) + " — " +
        vacantes_df["descripcion"].str[:60].str.strip() + "…"
    )
    opcion_sel = st.selectbox(
        "Vacante activa",
        options=vacantes_df["_etiq"].tolist(),
        label_visibility="collapsed",
        key="opec_selector",
    )
    fila_sel = vacantes_df[vacantes_df["_etiq"] == opcion_sel].iloc[0]
    opec_id  = int(fila_sel["opec"])

    titulos_lista = [t.strip() for t in str(fila_sel["titulos_requeridos"]).split("|")]
    exp_min_opec  = float(fila_sel["experiencia_minima_meses"]) if pd.notna(fila_sel["experiencia_minima_meses"]) else 0.0

    # Mostrar resumen de la vacante seleccionada
    st.markdown(
        f'<div style="background:#eef4fb;border-left:3px solid {COLOR_S};'
        f'padding:0.6rem 0.8rem;border-radius:5px;font-size:0.82rem;">'
        f'🎓 <b>{fila_sel["nivel_requerido"]}</b><br>'
        f'⏱️ {exp_min_opec:.0f} meses exp. mín.<br>'
        f'📋 {" | ".join(titulos_lista[:3])}{"…" if len(titulos_lista)>3 else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "**Autores:** Diana Vásquez · Germán Mahecha  \n"
        "**Maestría:** Ciencia de Datos"
    )

# ── Calcular ranking para la OPEC seleccionada ───────────────────────────────
# Usar session_state para no recalcular si el usuario solo cambia de pestaña
if ("last_opec" not in st.session_state or st.session_state.last_opec != opec_id):
    with st.spinner(f"Calculando ranking para OPEC {opec_id}…"):
        ranking, n_r1, n_r2, n_r3 = recomendar(candidatos_df, fila_sel)
    st.session_state.last_opec   = opec_id
    st.session_state.ranking     = ranking
    st.session_state.n_r1        = n_r1
    st.session_state.n_r2        = n_r2
    st.session_state.n_r3        = n_r3
else:
    ranking  = st.session_state.ranking
    n_r1     = st.session_state.n_r1
    n_r2     = st.session_state.n_r2
    n_r3     = st.session_state.n_r3

n_total = len(candidatos_df)

# ── Encabezado principal ──────────────────────────────────────────────────────
st.markdown(
    f'<div class="titulo"><h2 style="color:white;margin:0;">'
    f'🏛️ Sistema de Recomendación CNSC — OPEC {opec_id}</h2></div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="card">'
    f'<b>OPEC {opec_id}:</b> {fila_sel["descripcion"]}<br>'
    f'🎓 <b>Nivel requerido:</b> {fila_sel["nivel_requerido"]} &nbsp;|&nbsp; '
    f'📋 <b>Títulos:</b> {" | ".join(titulos_lista)} &nbsp;|&nbsp; '
    f'⏱️ <b>Experiencia mínima:</b> {exp_min_opec:.0f} meses'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total candidatos evaluados", f"{n_total:,}")
c2.metric("Pasan Regla 1 — Nivel educativo", f"{n_r1:,}")
c3.metric("Pasan Regla 2 — Título coincidente", f"{n_r2:,}")
c4.metric("✅ Elegibles finales (Regla 3)", f"{n_r3:,}")

# ── Pestañas ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Ranking",
    "📊 Análisis Visual",
    "🔍 Filtro Manual",
    "🌳 Información del Modelo",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RANKING
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if n_r3 == 0:
        st.warning("Ningún candidato cumple los tres requisitos de esta OPEC.")
    else:
        st.subheader(f"Ranking de Recomendación — OPEC {opec_id}  ({n_r3} candidatos elegibles)")

        # ── Tabla de elegibles ─────────────────────────────────────────────────
        cols_tab = ["puesto", "postulante", "nivel_educativo_texto",
                    "titulo_coincidente", "experiencia_aspirante_meses", "indice_modelo"]
        elegibles_df = ranking[ranking["R3_experiencia"]].copy() if "R3_experiencia" in ranking.columns else ranking.copy()
        cols_ok  = [c for c in cols_tab if c in elegibles_df.columns]
        df_tabla = elegibles_df[cols_ok].copy()
        if "experiencia_aspirante_meses" in df_tabla.columns:
            df_tabla["experiencia_aspirante_meses"] = df_tabla["experiencia_aspirante_meses"].round(1)
        if "indice_modelo" in df_tabla.columns:
            df_tabla["indice_modelo"] = df_tabla["indice_modelo"].map(
                lambda x: "100 %" if (not pd.isna(x) and x >= 0.99) else ("0 %" if not pd.isna(x) else "—")
            )
        df_tabla = df_tabla.rename(columns={
            "puesto": "Puesto",
            "postulante": "ID Postulante",
            "nivel_educativo_texto": "Nivel Educativo",
            "titulo_coincidente": "Título Coincidente",
            "experiencia_aspirante_meses": "Experiencia (meses)",
            "indice_modelo": "Índice del Modelo",
        })
        st.dataframe(df_tabla, use_container_width=True, height=460)

        # ── Candidatos no elegibles (expandible) ───────────────────────────────
        no_elig = ranking[~ranking["R3_experiencia"]].copy() if "R3_experiencia" in ranking.columns else pd.DataFrame()
        if len(no_elig) > 0:
            with st.expander(f"Ver candidatos no elegibles ({len(no_elig):,}) — motivo de exclusión por regla"):
                st.caption(
                    "**Leyenda de reglas:** N = Nivel educativo · T = Título · E = Experiencia  \n"
                    "S = cumple · N = no cumple · — = no evaluado (falló regla anterior)"
                )
                cols_ne = ["puesto", "postulante", "cumple_reglas", "nivel_educativo_texto",
                           "titulo_coincidente", "experiencia_aspirante_meses"]
                cols_ne_ok = [c for c in cols_ne if c in no_elig.columns]
                df_ne = no_elig[cols_ne_ok].copy()
                if "experiencia_aspirante_meses" in df_ne.columns:
                    df_ne["experiencia_aspirante_meses"] = df_ne["experiencia_aspirante_meses"].round(1)
                df_ne = df_ne.rename(columns={
                    "puesto": "#",
                    "postulante": "ID Postulante",
                    "cumple_reglas": "Reglas (N·T·E)",
                    "nivel_educativo_texto": "Nivel Educativo",
                    "titulo_coincidente": "Título Coincidente",
                    "experiencia_aspirante_meses": "Experiencia (meses)",
                })
                st.dataframe(df_ne, use_container_width=True, height=380)

        csv_dl = df_tabla.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Descargar ranking CSV",
            data=csv_dl,
            file_name=f"ranking_opec_{opec_id}.csv",
            mime="text/csv",
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANÁLISIS VISUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if n_r3 == 0:
        st.warning("Sin candidatos elegibles para esta OPEC.")
    else:
        st.subheader(f"Análisis Visual — OPEC {opec_id}")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("**Embudo de Selección**")
            fig, ax = plt.subplots(figsize=(5, 3.2))
            etapas  = ["Total\ncandidatos", "Regla 1\nNivel educ.", "Regla 2\nTítulo", "Regla 3\nExp. mín."]
            valores = [n_total, n_r1, n_r2, n_r3]
            colores = [COLOR_P, COLOR_S, COLOR_A, COLOR_OK]
            bars = ax.bar(etapas, valores, color=colores)
            for b, v in zip(bars, valores):
                ax.text(b.get_x() + b.get_width()/2, v + max(valores)*0.01,
                        f"{v:,}", ha="center", va="bottom", fontweight="bold", fontsize=9)
            ax.set_ylabel("Candidatos")
            ax.spines[["top", "right"]].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)

        with col_g2:
            st.markdown("**Distribución de Probabilidad de Éxito**")
            fig2, ax2 = plt.subplots(figsize=(5, 3.2))
            conteo_p = ranking["indice_modelo"].value_counts().sort_index()
            col_bars = [COLOR_OK if p >= 0.99 else COLOR_A for p in conteo_p.index]
            etiq_p   = [f"{p:.0%}" for p in conteo_p.index]
            ax2.bar(etiq_p, conteo_p.values, color=col_bars)
            ax2.set_ylabel("Candidatos")
            ax2.set_xlabel("Probabilidad de éxito")
            ax2.spines[["top", "right"]].set_visible(False)
            p_alta = mpatches.Patch(color=COLOR_OK, label="Alta (100 %)")
            p_baja = mpatches.Patch(color=COLOR_A,  label="Baja (0 %)")
            ax2.legend(handles=[p_alta, p_baja], fontsize=8)
            fig2.tight_layout()
            st.pyplot(fig2)

        # Nivel educativo de elegibles
        if "nivel_educativo_texto" in ranking.columns:
            col_g3, col_g4 = st.columns(2)
            with col_g3:
                st.markdown("**Nivel Educativo de Candidatos Elegibles**")
                conteo_n = ranking["nivel_educativo_texto"].value_counts()
                fig3, ax3 = plt.subplots(figsize=(5, max(2.5, len(conteo_n)*0.4)))
                ax3.barh(conteo_n.index, conteo_n.values, color=COLOR_S)
                for i, v in enumerate(conteo_n.values):
                    ax3.text(v + max(conteo_n.values)*0.01, i, f"{v:,}", va="center", fontsize=9)
                ax3.set_xlabel("Candidatos")
                ax3.spines[["top", "right"]].set_visible(False)
                fig3.tight_layout()
                st.pyplot(fig3)

            with col_g4:
                if "experiencia_aspirante_meses" in ranking.columns:
                    st.markdown("**Experiencia (meses) por Probabilidad de Éxito**")
                    fig4, ax4 = plt.subplots(figsize=(5, 3.2))
                    col_sc = [COLOR_OK if p >= 0.99 else COLOR_A
                              for p in ranking["indice_modelo"]]
                    ax4.scatter(ranking["experiencia_aspirante_meses"],
                                ranking["indice_modelo"],
                                c=col_sc, alpha=0.7, edgecolors="white", s=60)
                    ax4.set_xlabel("Experiencia (meses)")
                    ax4.set_ylabel("Probabilidad de éxito")
                    ax4.spines[["top", "right"]].set_visible(False)
                    fig4.tight_layout()
                    st.pyplot(fig4)

        # Top 10 por experiencia dentro de prob alta
        st.markdown("**Top 10 candidatos con alta probabilidad (ordenados por experiencia)**")
        prob_max = ranking["indice_modelo"].max()
        top_alta = ranking[ranking["indice_modelo"] >= prob_max].head(10)
        if len(top_alta) > 0 and "experiencia_aspirante_meses" in top_alta.columns:
            fig5, ax5 = plt.subplots(figsize=(10, 3))
            etiq5 = [f"#{r['puesto']}" for _, r in top_alta.iterrows()]
            ax5.bar(etiq5, top_alta["experiencia_aspirante_meses"], color=COLOR_S)
            ax5.set_ylabel("Experiencia (meses)")
            ax5.set_xlabel("Puesto en ranking")
            ax5.spines[["top", "right"]].set_visible(False)
            fig5.tight_layout()
            st.pyplot(fig5)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FILTRO MANUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Filtro Manual de Candidatos")
    st.markdown(
        f"Define los requisitos de cualquier vacante y el sistema aplica el mismo flujo: "
        f"**Regla 1 → Regla 2 → Regla 3 → Modelo** sobre los **{n_total:,} candidatos** del universo."
    )

    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        nivel_f = st.selectbox(
            "Nivel educativo mínimo (Regla 1)",
            options=list(JERARQUIA.keys()),
            index=list(JERARQUIA.keys()).index("PROFESIONAL"),
            key="filtro_nivel",
        )
    with cf2:
        exp_f = st.slider("Experiencia mínima en meses (Regla 3)", 0, 120, 3, key="filtro_exp")
    with cf3:
        titulo_f = st.text_input(
            "Título(s) requerido(s) — separar con | (Regla 2)",
            placeholder="MEDICINA | INGENIERIA QUIMICA",
            key="filtro_titulo",
        )

    fila_manual = pd.Series({
        "opec": "manual",
        "descripcion": "Filtro personalizado",
        "nivel_requerido": nivel_f,
        "titulos_requeridos": titulo_f.strip(),
        "experiencia_minima_meses": exp_f,
    })

    with st.spinner("Aplicando flujo completo…"):
        rank_m, nr1_m, nr2_m, nr3_m = recomendar(candidatos_df, fila_manual)

    # KPIs — igual que Tab 1
    fm1, fm2, fm3, fm4 = st.columns(4)
    fm1.metric("Total candidatos evaluados", f"{n_total:,}")
    fm2.metric("Regla 1 — Nivel educativo", f"{nr1_m:,}")
    fm3.metric("Regla 2 — Título coincidente", f"{nr2_m:,}")
    fm4.metric("Elegibles finales (Regla 3)", f"{nr3_m:,}")

    # Tabla de elegibles — mismo formato que Tab 1
    cols_m = ["puesto", "postulante", "nivel_educativo_texto",
              "titulo_coincidente", "experiencia_aspirante_meses", "indice_modelo"]
    elegibles_m = rank_m[rank_m["R3_experiencia"]].copy() if "R3_experiencia" in rank_m.columns else rank_m.copy()

    if len(elegibles_m) == 0:
        st.warning("Ningún candidato cumple los tres criterios. Ajusta los parámetros.")
    else:
        cols_ok = [c for c in cols_m if c in elegibles_m.columns]
        df_m = elegibles_m[cols_ok].copy()
        if "experiencia_aspirante_meses" in df_m.columns:
            df_m["experiencia_aspirante_meses"] = df_m["experiencia_aspirante_meses"].round(1)
        if "indice_modelo" in df_m.columns:
            df_m["indice_modelo"] = df_m["indice_modelo"].map(
                lambda x: "100 %" if (not pd.isna(x) and x >= 0.99) else ("0 %" if not pd.isna(x) else "—")
            )
        df_m = df_m.rename(columns={
            "puesto": "Puesto",
            "postulante": "ID Postulante",
            "nivel_educativo_texto": "Nivel Educativo",
            "titulo_coincidente": "Título Coincidente",
            "experiencia_aspirante_meses": "Experiencia (meses)",
            "indice_modelo": "Índice del Modelo",
        })
        st.dataframe(df_m, use_container_width=True, height=380)

        csv_m = df_m.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Descargar resultado CSV", data=csv_m,
                           file_name="filtro_manual.csv", mime="text/csv")

    # Candidatos no elegibles — mismo patrón que Tab 1
    no_elig_m = rank_m[~rank_m["R3_experiencia"]].copy() if "R3_experiencia" in rank_m.columns else pd.DataFrame()
    if len(no_elig_m) > 0:
        with st.expander(f"Ver candidatos no elegibles ({len(no_elig_m):,}) — motivo de exclusión por regla"):
            st.caption(
                "**Leyenda:** N = Nivel educativo · T = Título · E = Experiencia  \n"
                "S = cumple · N = no cumple · — = no evaluado (falló regla anterior)"
            )
            cols_ne = ["puesto", "postulante", "cumple_reglas", "nivel_educativo_texto",
                       "titulo_coincidente", "experiencia_aspirante_meses"]
            cols_ne_ok = [c for c in cols_ne if c in no_elig_m.columns]
            df_ne_m = no_elig_m[cols_ne_ok].copy()
            if "experiencia_aspirante_meses" in df_ne_m.columns:
                df_ne_m["experiencia_aspirante_meses"] = df_ne_m["experiencia_aspirante_meses"].round(1)
            df_ne_m = df_ne_m.rename(columns={
                "puesto": "#",
                "postulante": "ID Postulante",
                "cumple_reglas": "Reglas (N·T·E)",
                "nivel_educativo_texto": "Nivel Educativo",
                "titulo_coincidente": "Título Coincidente",
                "experiencia_aspirante_meses": "Experiencia (meses)",
            })
            st.dataframe(df_ne_m, use_container_width=True, height=380)

    # Embudo de selección
    st.markdown("**Embudo de Selección**")
    fig_e, ax_e = plt.subplots(figsize=(8, 2.8))
    vals_e = [n_total, nr1_m, nr2_m, nr3_m]
    bars_e = ax_e.bar(
        ["Total", "Regla 1\nNivel educ.", "Regla 2\nTítulo", "Regla 3\nExp."],
        vals_e, color=[COLOR_P, COLOR_S, COLOR_A, COLOR_OK],
    )
    for b, v in zip(bars_e, vals_e):
        ax_e.text(b.get_x() + b.get_width()/2, v + max(vals_e)*0.01,
                  f"{v:,}", ha="center", va="bottom", fontweight="bold")
    ax_e.set_ylabel("Candidatos")
    ax_e.spines[["top", "right"]].set_visible(False)
    fig_e.tight_layout()
    st.pyplot(fig_e)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INFORMACIÓN DEL MODELO
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Modelo Predictivo — Árbol de Decisión")

    cm1, cm2 = st.columns([1, 1])

    with cm1:
        st.markdown("""
**Algoritmo seleccionado:** Árbol de Decisión (`DecisionTreeClassifier` — scikit-learn)

| Parámetro               | Valor                       |
|-------------------------|-----------------------------|
| Variable objetivo       | Éxito parcial del aspirante |
| Variables predictoras   | 40                          |
| Optimización            | GridSearchCV · 5-fold CV    |
| Balanceo de clases      | SMOTE                       |
| F1-Score promedio CV    | 0.8083 (IC 95 %)            |

**¿Por qué Árbol de Decisión y no Random Forest?**
Random Forest obtuvo métricas ligeramente superiores, pero el Árbol de Decisión fue
seleccionado porque sus reglas son **auditables y explicables** ante la entidad pública,
cumpliendo los principios de transparencia algorítmica exigidos en procesos de selección del Estado.

**¿Por qué la probabilidad es 0 % o 100 %?**
El modelo aprendió fronteras de decisión muy marcadas porque los datos de entrenamiento
tienen una separación clara entre aspirantes que aprobaron y los que no.
El desempate entre candidatos de igual probabilidad se resuelve por experiencia acumulada.
        """)

    with cm2:
        st.markdown("**Importancia de Variables (Top 15)**")
        try:
            importancias = modelo.feature_importances_
            nombres = (modelo.feature_names_in_
                       if hasattr(modelo, "feature_names_in_")
                       else [f"Var {i}" for i in range(len(importancias))])
            df_imp = (
                pd.DataFrame({"Variable": nombres, "Importancia": importancias})
                .sort_values("Importancia", ascending=False)
                .head(15)
            )
            fig_i, ax_i = plt.subplots(figsize=(5, 5))
            ax_i.barh(df_imp["Variable"][::-1], df_imp["Importancia"][::-1], color=COLOR_S)
            ax_i.set_xlabel("Importancia relativa")
            ax_i.spines[["top", "right"]].set_visible(False)
            fig_i.tight_layout()
            st.pyplot(fig_i)
        except Exception as e:
            st.info(f"No se pudo obtener la importancia de variables: {e}")

    st.markdown("---")
    st.subheader("Métricas de Evaluación (conjunto de prueba 20 %)")
    cm1e, cm2e, cm3e, cm4e = st.columns(4)
    cm1e.metric("Accuracy",  "~82 %")
    cm2e.metric("Precision", "~84 %")
    cm3e.metric("Recall",    "~80 %")
    cm4e.metric("ROC-AUC",   "~0.88")

    st.markdown("---")
    st.subheader("Flujo del Sistema")
    st.markdown(f"""
```
{n_total:,} candidatos (universo completo)
         │
         ▼ Selección de OPEC en el sidebar
  ┌───────────────────────────┐
  │  Regla 1: Nivel educativo │  →  {n_r1:,} pasan
  │  Regla 2: Título exacto   │  →  {n_r2:,} pasan
  │  Regla 3: Experiencia mín.│  →  {n_r3:,} pasan
  └─────────────┬─────────────┘
               │
               ▼
  ┌────────────────────────┐
  │  Árbol de Decisión     │  predict_proba()
  │  40 variables          │
  └─────────────┬──────────┘
               │
               ▼
  Ranking ordenado por probabilidad ↓
  Desempate por experiencia ↓
```
*(Números correspondientes a la OPEC {opec_id} actualmente seleccionada)*
    """)
