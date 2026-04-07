# CocinaAI 🌮

Asistente de recetas mexicanas. Dime qué ingredientes tienes y te sugiero qué cocinar.

## Tecnologías
- Streamlit (interfaz)
- OpenAI GPT-4o-mini (análisis con Structured Outputs)
- Spoonacular API (base de datos de recetas)
- Pydantic (modelos de datos)

## Cómo correr localmente

1. Instala dependencias:
   pip install -r requirements.txt

2. Crea el archivo `.streamlit/secrets.toml` con tus keys:
   SPOONACULAR_API = "tu_key"
   OPENAI_API_KEY  = "tu_key"

3. Corre la app:
   streamlit run app.py

## Despliegue en Streamlit Cloud

1. Sube el proyecto a GitHub (sin el secrets.toml)
2. Ve a share.streamlit.io → New app → elige tu repo
3. En "Advanced settings" agrega tus keys como secrets
4. Deploy!
