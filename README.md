# Sistema de Recomendación Laboral — CNSC

**Proyecto:** Modelo Predictivo para la Recomendación de Oportunidades Laborales en el Ámbito Gubernamental  
**Autores:** Diana Vásquez · Germán Mahecha  
**Maestría:** Ciencia de Datos

---

## Descripción

Sistema de recomendación que combina reglas de negocio y un modelo de Machine Learning (Árbol de Decisión) para recomendar aspirantes a cargos públicos de la Comisión Nacional del Servicio Civil (CNSC). El sistema evalúa el universo completo de candidatos (11.578 aspirantes) frente a cualquier vacante OPEC, aplicando tres reglas de elegibilidad y un índice predictivo basado en el historial de desempeño en pruebas funcionales.

## Contenido del repositorio

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Aplicativo Streamlit — pipeline completo de recomendación |
| `modelo_arbol.pkl` | Modelo Árbol de Decisión entrenado (SMOTE + GridSearchCV) |
| `candidatos_completo.csv` | Base de 11.578 candidatos con 44 variables de perfil |
| `vacantes_opec.csv` | Base de 740 vacantes OPEC con requisitos de elegibilidad |
| `ranking_final.csv` | Ranking de referencia — OPEC 2881 (58 candidatos elegibles) |
| `vacantes.csv` | Base de vacantes en modo demostración (21 OPEC) |
| `requirements.txt` | Dependencias de Python con versiones fijadas |
| `ejecutar.bat` | Script Windows para instalación y ejecución automática |

## Requisitos previos

- **Windows 10/11** (64 bits)
- **Python 3.9 o superior** con la opción *"Add Python to PATH"* marcada al instalar  
  → Descarga: https://www.python.org/downloads/
- Conexión a internet (solo para la instalación inicial de dependencias)

## Instalación y ejecución

### Opción 1 — Archivo .bat (recomendado para Windows)

```
git clone https://github.com/DianaVF2025/proyectoMCD.git
cd proyectoMCD
ejecutar.bat
```

El archivo `ejecutar.bat` realiza automáticamente:
1. Verificación de Python en el sistema
2. Comprobación de archivos requeridos
3. Creación del entorno virtual (solo la primera vez)
4. Instalación de dependencias
5. Apertura del aplicativo en el navegador en http://localhost:8501

### Opción 2 — Ejecución manual (cualquier sistema operativo)

```bash
git clone https://github.com/DianaVF2025/proyectoMCD.git
cd proyectoMCD
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Flujo del sistema de recomendación

El sistema aplica el siguiente pipeline sobre los 11.578 candidatos del universo:

```
11.578 candidatos
      │
      ▼
 Regla 1: Nivel educativo ≥ requerido por la OPEC
      │
      ▼
 Regla 2: Título académico coincidente con los requeridos
      │
      ▼
 Regla 3: Experiencia efectiva ≥ mínimo requerido
      │
      ▼
 Modelo predictivo (Árbol de Decisión)
 → Índice del modelo basado en historial de pruebas funcionales CNSC
      │
      ▼
 Ranking final de candidatos elegibles
```

## Módulos del aplicativo

| Pestaña | Descripción |
|---------|-------------|
| 📋 Ranking | Tabla de candidatos elegibles con índice del modelo y motivo de exclusión para no elegibles |
| 📊 Análisis Visual | Embudo de selección, distribución del índice y gráficas de perfil |
| 🔍 Filtro Manual | Aplicación del flujo completo con criterios personalizados de vacante |
| 🌳 Información del Modelo | Parámetros técnicos e importancia de variables del Árbol de Decisión |
