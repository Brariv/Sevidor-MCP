"""Carga el Excel de FAQs que tiene UNA HOJA POR MARCA.

Dos detalles del archivo que rompen un `pd.read_excel(path)` simple:

1. La tabla no empieza en la fila 1: arriba hay un logo y un titulo, y los
   encabezados reales ("#", "Pregunta frecuente", "Respuesta sugerida")
   estan varias filas mas abajo. Por eso pandas devuelve columnas
   "Unnamed: 0" y `faq_df["Pregunta frecuente"]` truena con KeyError.
2. Hay una hoja por marca, y `pd.read_excel` sin `sheet_name` solo lee la
   primera.

Aqui la fila de encabezados se busca sola, asi que si mañana alguien agrega
o quita una fila arriba del logo, esto sigue funcionando.
"""
from __future__ import annotations
import sys
import pandas as pd
from Json_RPC_Plumbing import log
from pathlib import Path

COL_PREGUNTA = "Pregunta frecuente"
COL_RESPUESTA = "Respuesta sugerida"


def _fila_de_encabezados(hoja: pd.DataFrame, columna_clave: str = COL_PREGUNTA) -> int | None:
    """Indice de la fila que contiene los encabezados, o None si la hoja no los tiene."""
    for i, fila in hoja.iterrows():
        valores = [str(v).strip().lower() for v in fila if pd.notna(v)]
        if columna_clave.lower() in valores:
            return int(i)
    return None


def leer_faq_por_marca(path: str) -> dict[str, pd.DataFrame]:
    """{nombre_de_la_hoja (marca): DataFrame con columnas pregunta/respuesta}."""
    crudas = pd.read_excel(path, sheet_name=None, header=None)  # None = TODAS las hojas

    por_marca: dict[str, pd.DataFrame] = {}
    for marca, hoja in crudas.items():
        fila = _fila_de_encabezados(hoja)
        if fila is None:
            log(f"[faq] hoja '{marca}' ignorada: no encontre la columna '{COL_PREGUNTA}'")
            continue

        df = hoja.iloc[fila + 1:].copy()
        df.columns = [str(c).strip() for c in hoja.iloc[fila]]
        df = df.loc[:, [c for c in (COL_PREGUNTA, COL_RESPUESTA) if c in df.columns]]
        df = df.dropna(how="all")                      # filas vacias de relleno
        if COL_PREGUNTA in df.columns:
            df = df[df[COL_PREGUNTA].notna()]          # filas sin pregunta no sirven
        por_marca[marca] = df.reset_index(drop=True)

    return por_marca


def leer_faq_plano(path: str) -> pd.DataFrame:
    """Todas las marcas en un solo DataFrame, con una columna 'marca'."""
    por_marca = leer_faq_por_marca(path)
    if not por_marca:
        return pd.DataFrame(columns=["marca", COL_PREGUNTA, COL_RESPUESTA])
    return pd.concat(
        [df.assign(marca=marca) for marca, df in por_marca.items()],
        ignore_index=True,
    )[["marca", COL_PREGUNTA, COL_RESPUESTA]]

# BASE_DIR = Path(__file__).resolve().parent
# ruta = sys.argv[1] if len(sys.argv) > 1 else BASE_DIR / "data" / "FAQ_Redes_Sociales_Marcas.xlsx"
# for marca, df in leer_faq_por_marca(ruta).items():
#     log(f"{marca.title()}: {len(df)} preguntas")
#     for pregunta in df[COL_PREGUNTA].tolist()[:3]:
#         log(f"  - {pregunta}")

# print(leer_faq_plano(ruta).head(3))
# print(f"Total preguntas: {len(leer_faq_plano(ruta))}")