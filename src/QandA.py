from rapidfuzz import process as rf_process, fuzz
import sys
import json
import unicodedata
import re
import urllib.request
import difflib
import pandas as pd
from DataLoader import leer_faq_plano, COL_PREGUNTA, COL_RESPUESTA
from Tools import MARCAS
from pathlib import Path

# ---------------------------------------------------------------------------
# Business logic 
# ---------------------------------------------------------------------------

# Cargar una sola vez al iniciar el servidor
BASE_DIR = Path(__file__).resolve().parent
FAQ_FILENAME = "FAQ_Redes_Sociales_Marcas.xlsx"
FAQ_PATH = next(
    (
        candidate
        for candidate in (
            BASE_DIR / "data" / FAQ_FILENAME,
            BASE_DIR.parent / "data" / FAQ_FILENAME,
        )
        if candidate.is_file()
    ),
    None,
)

if FAQ_PATH is None:
    raise FileNotFoundError(
        f"No se encontró {FAQ_FILENAME} en {BASE_DIR / 'data'} ni en {BASE_DIR.parent / 'data'}."
    )

faq_df = leer_faq_plano(FAQ_PATH)  # columnas: "pregunta", "respuesta"

def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, sin signos de puntuación, espacios colapsados."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

def buscar_pregunta_exacta(pregunta_usuario: str, faq_df: pd.DataFrame) -> str:
    """Buscar la pregunta más cercana en la FAQ usando difflib."""
    preguntas = faq_df[COL_PREGUNTA].tolist()
    resultados = difflib.get_close_matches(pregunta_usuario, preguntas, n=1, cutoff=0.6)
    if resultados:
        return resultados[0]
    return None

def buscar_preguntas_cercanas(pregunta_usuario, df_marca, n=5, umbral=45):
    preguntas = df_marca[COL_PREGUNTA].tolist()

    resultados = rf_process.extract(
        pregunta_usuario,
        preguntas,
        scorer=fuzz.token_set_ratio,
        processor=normalizar,      # se aplica a la query Y a las opciones
        limit=n,
    )

    candidatos = []
    for match, score, idx in resultados:
        if score < umbral:
            continue
        fila = df_marca.iloc[idx]
        candidatos.append({
            "pregunta": fila[COL_PREGUNTA],
            "respuesta": fila[COL_RESPUESTA],
            "score": round(score),
        })
    return candidatos

def listar_preguntas_producto(arguments: dict) -> str:
    marca = arguments.get("marca")
    if not marca:
        return "El argumento 'marca' es obligatorio."

    df_marca = faq_df[faq_df["marca_norm"] == marca]
    if df_marca.empty:
        return f"No hay preguntas frecuentes registradas para {marca}."

    preguntas = df_marca[COL_PREGUNTA].tolist()
    return json.dumps(preguntas, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Tool registry: JSON Schema definitions exposed via tools/list
# ---------------------------------------------------------------------------

# Definido una sola vez, cerca de TOOLS


# Normalizar UNA vez al cargar el Excel, no en cada llamada
faq_df["marca_norm"] = faq_df["marca"].str.strip().str.lower()

class ToolNotFound(Exception):
    pass


def call_tool(name: str, arguments: dict) -> str:
    if name == "consultar_faq_producto":
        return listar_preguntas_producto(arguments)

    if name.endswith("_exacta"):
        marca = MARCAS.get(name[:-7])  # quitar "_exacta"
        pregunta_usuario = (arguments.get("pregunta") or "")
        if not marca:
            raise ToolNotFound(f"Tool '{name}' not found.")
        if not pregunta_usuario:
            raise ValueError("Los argumentos 'marca' y 'pregunta' son obligatorios.")

        df_marca = faq_df[faq_df["marca_norm"] == marca]
        if df_marca.empty:
            return f"No hay preguntas frecuentes registradas para {marca}."

        pregunta_encontrada = buscar_pregunta_exacta(pregunta_usuario, df_marca)
        if not pregunta_encontrada:
            return (
                f"No se encontró una pregunta frecuente similar para {marca}. "
                "Se recomienda consultar directamente con un farmacéutico."
            )

        respuesta = df_marca.loc[
            df_marca[COL_PREGUNTA] == pregunta_encontrada, COL_RESPUESTA
        ]
        if respuesta.empty:
            return (
                f"No se encontró una respuesta para la pregunta '{pregunta_encontrada}' "
                f"en la FAQ de {marca}."
            )

        return json.dumps({
            "pregunta": pregunta_encontrada,
            "respuesta": respuesta.iloc[0],
        }, ensure_ascii=False)
    
    marca = MARCAS.get(name)
    
    pregunta_usuario = (arguments.get("pregunta") or "")

    if not marca:
        raise ToolNotFound(f"Tool '{name}' not found.")
    if not pregunta_usuario:
        raise ValueError("Los argumentos 'marca' y 'pregunta' son obligatorios.")
    

    df_marca = faq_df[faq_df["marca_norm"] == marca]
    if df_marca.empty:
        return f"No hay preguntas frecuentes registradas para {marca}."

    preguntas_cercanas = buscar_preguntas_cercanas(pregunta_usuario, df_marca)
    if not preguntas_cercanas:
        return (
            f"No se encontró una pregunta frecuente similar para {marca}. "
            "Se recomienda consultar directamente con un farmacéutico."
        )

    return json.dumps(preguntas_cercanas, ensure_ascii=False)

