import streamlit as st
import requests
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CocinaAI",
    page_icon="🌮",
    layout="centered"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fondo cálido */
.stApp {
    background-color: #FDF6EE;
}

/* Ocultar header de Streamlit */
#MainMenu, header, footer { visibility: hidden; }

/* Título principal */
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    color: #1C1208;
    line-height: 1.1;
    margin-bottom: 0.25rem;
}
.hero-sub {
    font-size: 1rem;
    color: #7A6550;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Input area */
.stTextArea textarea {
    background-color: #FFF8F0 !important;
    border: 1.5px solid #D4A96A !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    color: #1C1208 !important;
    padding: 14px !important;
}
.stTextArea textarea:focus {
    border-color: #B5722A !important;
    box-shadow: 0 0 0 3px rgba(181,114,42,0.15) !important;
}

/* Botón principal */
.stButton > button {
    background-color: #B5722A !important;
    color: #FFF8F0 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 2rem !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background-color: #9A5E1F !important;
}

/* Receta card */
.receta-card {
    background: #FFFAF4;
    border: 1px solid #E8D5B7;
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
}
.receta-nombre {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 600;
    color: #1C1208;
    margin-bottom: 0.5rem;
}
.receta-resumen {
    font-size: 0.92rem;
    color: #5C4A32;
    line-height: 1.6;
    margin-bottom: 1rem;
    font-style: italic;
}
.meta-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.meta-pill {
    background: #F2E4CE;
    color: #7A4F1E;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 99px;
}
.meta-pill.verde {
    background: #DFF0D8;
    color: #2D6A1F;
}
.meta-pill.rojo {
    background: #FAE0D5;
    color: #8B2E12;
}
.section-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #B5722A;
    margin: 1rem 0 0.4rem;
}
.ingrediente-item {
    font-size: 0.9rem;
    color: #3D2E1A;
    padding: 3px 0;
}
.consejo-box {
    background: #FFF3DC;
    border-left: 3px solid #D4A96A;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.88rem;
    color: #5C3D0E;
    line-height: 1.5;
    margin-top: 0.75rem;
}
.sustitucion-item {
    font-size: 0.88rem;
    color: #4A3520;
    padding: 2px 0;
}
.apto-pill {
    display: inline-block;
    background: #E8F5E9;
    color: #2E6B35;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 99px;
    margin: 2px 3px 2px 0;
}
.divider {
    border: none;
    border-top: 1px solid #E8D5B7;
    margin: 1rem 0;
}
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #A08060;
    font-size: 0.95rem;
}
.empty-emoji {
    font-size: 3rem;
    margin-bottom: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# ── Pydantic model ────────────────────────────────────────────────────────────
class RecetaInsights(BaseModel):
    nombre: str = Field(description="Nombre del platillo")
    tiempo_minutos: int = Field(description="Tiempo total de preparación en minutos")
    dificultad: str = Field(description="Nivel de dificultad: Fácil, Media o Difícil")
    ingredientes_clave: List[str] = Field(description="Lista de los ingredientes más importantes del platillo")
    resumen: str = Field(description="Descripción breve y apetitosa del platillo en 2 oraciones")
    consejo_chef: str = Field(description="Un consejo práctico para mejorar el resultado")
    sustituciones: List[str] = Field(description="2-3 sustituciones posibles para ingredientes difíciles")
    apto_para: List[str] = Field(description="Perfiles para quienes es ideal: vegetariano, familiar, rápido, etc.")
    puntuacion_facilidad: int = Field(description="Puntuación de facilidad del 1 al 10")

# ── API helpers ───────────────────────────────────────────────────────────────
def search_recipes(ingredients: str, api_key: str, number: int = 4) -> list:
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "cuisine": "mexican",
        "includeIngredients": ingredients,
        "number": number,
        "addRecipeInformation": True,
        "apiKey": api_key
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        return resp.json().get("results", [])
    except Exception:
        return []

def get_recipe_detail(recipe_id: int, api_key: str) -> dict:
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"includeNutrition": False, "apiKey": api_key}
    try:
        resp = requests.get(url, params=params, timeout=10)
        return resp.json()
    except Exception:
        return {}

def render_recipe_text(recipe: dict) -> str:
    title = recipe.get("title", "")
    time = recipe.get("readyInMinutes", "?")
    ingredients = recipe.get("extendedIngredients", [])
    ing_text = "\n".join(f"  - {i.get('original','')}" for i in ingredients)
    steps = []
    for instr in recipe.get("analyzedInstructions", []):
        for step in instr.get("steps", []):
            steps.append(f"  {step['number']}. {step['step']}")
    steps_text = "\n".join(steps) if steps else "No disponible"
    return f"Receta: {title}\nTiempo: {time} minutos\n\nIngredientes:\n{ing_text}\n\nPreparación:\n{steps_text}"

def get_insights(recipe: dict, client: OpenAI) -> RecetaInsights:
    recipe_text = render_recipe_text(recipe)
    json_template = (
        '{\n'
        '  "nombre": "nombre del platillo",\n'
        '  "tiempo_minutos": 30,\n'
        '  "dificultad": "Facil",\n'
        '  "ingredientes_clave": ["ingrediente1", "ingrediente2"],\n'
        '  "resumen": "descripcion breve en 2 oraciones",\n'
        '  "consejo_chef": "un consejo practico",\n'
        '  "sustituciones": ["sustitucion1", "sustitucion2"],\n'
        '  "apto_para": ["perfil1", "perfil2"],\n'
        '  "puntuacion_facilidad": 8\n'
        '}'
    )
    prompt = (
        "Analiza esta receta y responde EXACTAMENTE con este JSON "
        "(todos los campos en espanol, con estos nombres exactos):\n\n"
        + json_template
        + "\n\nReceta a analizar:\n"
        + recipe_text
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un chef experto en cocina mexicana. Responde SOLO con JSON valido, sin texto adicional."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    data = json.loads(completion.choices[0].message.content)
    field_map = {
        "name": "nombre", "title": "nombre",
        "time_minutes": "tiempo_minutos",
        "difficulty": "dificultad",
        "key_ingredients": "ingredientes_clave",
        "summary": "resumen", "description": "resumen",
        "chef_tip": "consejo_chef", "tip": "consejo_chef",
        "substitutions": "sustituciones",
        "suitable_for": "apto_para",
        "ease_score": "puntuacion_facilidad"
    }
    normalized = {field_map.get(k, k): v for k, v in data.items()}
    defaults = {
        "nombre": recipe.get("title", "Receta"),
        "tiempo_minutos": recipe.get("readyInMinutes", 30),
        "dificultad": "Media",
        "ingredientes_clave": [],
        "resumen": "Una deliciosa receta mexicana.",
        "consejo_chef": "Sigue los pasos con cuidado.",
        "sustituciones": [],
        "apto_para": [],
        "puntuacion_facilidad": 5
    }
    defaults.update(normalized)
    return RecetaInsights(**defaults)

def dificultad_color(d: str) -> str:
    if d == "Fácil": return "verde"
    if d == "Difícil": return "rojo"
    return ""

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">CocinaAI 🌮</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Dime qué tienes en el refri y te sugiero recetas mexicanas.</div>', unsafe_allow_html=True)

# API keys
SPOONACULAR_API = st.secrets.get("SPOONACULAR_API", os.getenv("SPOONACULAR_API", ""))
OPENAI_API_KEY  = st.secrets.get("OPENAI_API_KEY",  os.getenv("OPENAI_API_KEY", ""))

if not SPOONACULAR_API or not OPENAI_API_KEY:
    st.error("Faltan las API keys. Agrégalas en secrets.toml o variables de entorno.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# Input
ingredientes = st.text_area(
    "¿Qué ingredientes tienes?",
    placeholder="ej. pollo, chile poblano, crema, cebolla, ajo...",
    height=100,
    label_visibility="collapsed"
)

buscar = st.button("Buscar recetas →")

# Results
if buscar and ingredientes.strip():
    with st.spinner("Buscando recetas mexicanas..."):
        resultados = search_recipes(ingredientes, SPOONACULAR_API)

    if not resultados:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-emoji">🫙</div>
            No encontré recetas con esos ingredientes. Intenta con ingredientes más comunes como pollo, frijoles, chile o jitomate.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(resultados)} recetas encontradas** con tus ingredientes:")
        st.markdown("<br>", unsafe_allow_html=True)

        for r in resultados:
            with st.spinner(f"Analizando {r.get('title', 'receta')}..."):
                detail = get_recipe_detail(r["id"], SPOONACULAR_API)
                if not detail:
                    continue
                insights = get_insights(detail, client)

            dc = dificultad_color(insights.dificultad)
            ing_html = "".join(f'<div class="ingrediente-item">• {i}</div>' for i in insights.ingredientes_clave)
            sust_html = "".join(f'<div class="sustitucion-item">↔ {s}</div>' for s in insights.sustituciones)
            apto_html = "".join(f'<span class="apto-pill">{a}</span>' for a in insights.apto_para)
            facilidad_bar = "●" * insights.puntuacion_facilidad + "○" * (10 - insights.puntuacion_facilidad)

            st.markdown(f"""
            <div class="receta-card">
                <div class="receta-nombre">{insights.nombre}</div>
                <div class="receta-resumen">{insights.resumen}</div>
                <div class="meta-row">
                    <span class="meta-pill">⏱ {insights.tiempo_minutos} min</span>
                    <span class="meta-pill {dc}">{'★' if dc=='verde' else ('⚠' if dc=='rojo' else '◆')} {insights.dificultad}</span>
                    <span class="meta-pill">Facilidad {insights.puntuacion_facilidad}/10</span>
                </div>
                <div class="section-label">Ingredientes clave</div>
                {ing_html}
                <div class="consejo-box">💡 {insights.consejo_chef}</div>
                <hr class="divider">
                <div class="section-label">Sustituciones</div>
                {sust_html}
                <div class="section-label">Apto para</div>
                {apto_html}
            </div>
            """, unsafe_allow_html=True)

elif buscar and not ingredientes.strip():
    st.warning("Escribe al menos un ingrediente para buscar recetas.")

else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-emoji">🧅</div>
        Escribe los ingredientes que tienes disponibles<br>y te sugiero qué cocinar hoy.
    </div>
    """, unsafe_allow_html=True)
