"""
╔══════════════════════════════════════════════════════════════╗
║          Z A S C A  —  Motor Lógico Backend v2.0            ║
║     "El arte de poner a cada quién en su lugar."            ║
╚══════════════════════════════════════════════════════════════╝

Base de datos  : 134 frases (Excel "El arte de insultar")
Autores        : Macedonio Fernández · Oscar Wilde
                 Juan José Millás · Groucho Marx
                 Schopenhauer · Dr. Mario A. Ramírez Barajas
                 Usuario (Tú)
Niveles        : Sutil · Cáustico · Letal · Directo
Emergencia     : 13 Salidas Elegantes
"""

import json
import random
import os
from typing import Optional

# ── Carga de DB ───────────────────────────────────────────────
_DB_PATH = os.path.join(os.path.dirname(__file__), "zasca_db.json")

def _cargar_db() -> dict:
    with open(_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["zasca_db"]

_DB = _cargar_db()

# ── Constantes ────────────────────────────────────────────────
AUTORES_VALIDOS = [a["nombre"] for a in _DB["autores_pantalla"]]
NIVELES_VALIDOS = ["Sutil", "Cáustico", "Letal"]
NIVEL_USUARIO   = "Directo"

_JERARQUIA = {"Sutil": 1, "Cáustico": 2, "Letal": 3}

# Plantillas de refinamiento por estilo de autor
_PLANTILLAS = {
    "Macedonio Fernández": (
        "Lo que usted intenta decir con ese lenguaje tan… corporal podría "
        "formularse así: {esencia}. Aunque, en rigor, la nada no necesita "
        "insultos para manifestarse."
    ),
    "Oscar Wilde": (
        "Permítame traducir su… entusiasmo verbal: {esencia}. "
        "La brutalidad, sin estilo, es simplemente brutalidad."
    ),
    "Juan José Millás": (
        "Su expresión, analizada clínicamente, diagnostica lo siguiente: "
        "{esencia}. El síntoma era evidente; solo faltaba el bisturí adecuado."
    ),
    "Groucho Marx": (
        "Mire, lo que quiso decir es: {esencia}. "
        "No hace falta insultar cuando la realidad ya hace el trabajo sucio."
    ),
    "Schopenhauer": (
        "La Voluntad, a través de usted, quiso expresar: {esencia}. "
        "La filosofía lo dice con más precisión y sin la vulgaridad de la prisa."
    ),
    "Dr. Mario A. Ramírez Barajas": (
        "La evidencia sugiere que usted intentó comunicar: {esencia}. "
        "Clínicamente hablando, el diagnóstico es el mismo con o sin adornos "
        "— pero con rigor académico suena considerablemente mejor."
    ),
}

_SUSTITUCIONES = {
    "idiota":        "carece usted de lucidez",
    "imbécil":       "su razonamiento es notablemente deficiente",
    "estúpido":      "su capacidad intelectual es limitada",
    "inútil":        "su aportación es inexistente",
    "tonto":         "su agudeza mental deja que desear",
    "asco":          "provoca repulsión estética",
    "odio":          "genero una profunda antipatía hacia",
    "mentiroso":     "su relación con la verdad es, cuanto menos, flexible",
    "hipócrita":     "practica usted el arte del doble estándar",
    "arrogante":     "su autoestima supera ampliamente sus méritos",
    "pesado":        "su presencia resulta extraordinariamente gravosa",
    "insoportable":  "su compañía supone un ejercicio de resistencia",
    "cállate":       "le invito a guardar silencio",
    "vete":          "le sugiero que busque otro entorno",
}


# ── filtrar_frase ─────────────────────────────────────────────

def filtrar_frase(autor: str, nivel_veneno: str) -> dict:
    """
    Devuelve la frase más adecuada para el autor y nivel dados.

    Búsqueda en cascada:
      1. Coincidencia exacta  (autor + nivel)
      2. Autor + nivel más cercano en jerarquía
      3. Solo autor           (aleatoria)
      4. Fallback global      (aleatoria de cualquier autor)

    Para autor "Usuario (Tú)" usa frases_usuario con nivel "Directo".
    """
    autor = autor.strip()
    nivel = nivel_veneno.strip()

    # Caso especial: usuario propio
    if autor.lower() in ("usuario (tú)", "usuario", "tú", "tu"):
        frases = _DB["frases_usuario"]
        resultado = random.choice(frases).copy()
        resultado["autor"] = "Usuario (Tú)"
        resultado["match_tipo"] = "exacto"
        return resultado

    frases = _DB["frases_ataque"]

    # Nivel 1: exacto
    exactas = [f for f in frases
               if f["autor"].lower() == autor.lower()
               and f["nivel"].lower() == nivel.lower()]
    if exactas:
        r = random.choice(exactas).copy()
        r["match_tipo"] = "exacto"
        return r

    # Nivel 2: autor + nivel más cercano
    por_autor = [f for f in frases if f["autor"].lower() == autor.lower()]
    if por_autor:
        buscado = _JERARQUIA.get(nivel, 2)
        por_autor.sort(key=lambda f: abs(_JERARQUIA.get(f["nivel"], 2) - buscado))
        r = por_autor[0].copy()
        r["match_tipo"] = "parcial_nivel"
        return r

    # Nivel 3: fallback global
    r = random.choice(frases).copy()
    r["match_tipo"] = "fallback_global"
    return r


# ── boton_emergencia ──────────────────────────────────────────

def boton_emergencia() -> dict:
    """
    Ignora todos los filtros y devuelve una Salida Elegante aleatoria.
    Ideal para situaciones de alta tensión donde hay que retirarse con estilo.
    """
    return random.choice(_DB["emergencia"]).copy()


# ── procesar_insulto ──────────────────────────────────────────

def procesar_insulto(frase_vulgar: str, autor: str) -> dict:
    """
    Recibe una frase vulgar y devuelve su versión refinada
    en el estilo del autor seleccionado.
    """
    autor = autor.strip()
    estilos = _DB.get("estilos_autor", {})
    estilo_info = estilos.get(autor)

    esencia = _extraer_esencia(frase_vulgar)
    plantilla = _PLANTILLAS.get(
        autor,
        "Lo que usted quiso decir: {esencia}. Con más elegancia, naturalmente."
    )
    version_refinada = plantilla.format(esencia=esencia)

    return {
        "original":        frase_vulgar,
        "autor":           autor,
        "version_refinada": version_refinada,
        "estilo_aplicado": estilo_info.get("descripcion", "Estilo propio del autor") if estilo_info else "Estilo genérico",
    }


def _extraer_esencia(frase: str) -> str:
    frase_lower = frase.lower()
    for vulgar, elegante in _SUSTITUCIONES.items():
        if vulgar in frase_lower:
            return elegante
    return "su comportamiento resulta inapropiado para el contexto"


# ── listar_opciones ───────────────────────────────────────────

def listar_opciones() -> dict:
    """Devuelve valores válidos para poblar los selectores del frontend."""
    return {
        "autores":          AUTORES_VALIDOS,
        "autores_pantalla": _DB["autores_pantalla"],
        "niveles":          NIVELES_VALIDOS,
        "total_frases": (
            len(_DB["frases_ataque"])
            + len(_DB["frases_usuario"])
            + len(_DB["emergencia"])
        ),
    }


# ── bibliografia ──────────────────────────────────────────────

def obtener_bibliografia() -> list:
    """Devuelve la bibliografía completa del proyecto ZASCA."""
    return _DB.get("bibliografia", [])


# ── Demo ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 62)
    print("  ZASCA v2.0 — Motor Lógico  |  134 frases  |  Demo")
    print("═" * 62)

    print("\n[1] filtrar_frase — Match exacto (Groucho / Letal)")
    r = filtrar_frase("Groucho Marx", "Letal")
    print(f"  [{r['match_tipo'].upper()}] {r['texto']}")

    print("\n[2] filtrar_frase — Schopenhauer / Sutil")
    r = filtrar_frase("Schopenhauer", "Sutil")
    print(f"  [{r['match_tipo'].upper()}] {r['texto']}")

    print("\n[3] filtrar_frase — Dr. Mario A. Ramírez Barajas")
    r = filtrar_frase("Dr. Mario A. Ramírez Barajas", "Cáustico")
    print(f"  [{r['match_tipo'].upper()}] {r['texto']}")

    print("\n[4] filtrar_frase — Usuario (Tú)")
    r = filtrar_frase("Usuario (Tú)", "Directo")
    print(f"  [{r['match_tipo'].upper()}] {r['texto']}")

    print("\n[5] boton_emergencia")
    r = boton_emergencia()
    print(f"  {r['texto']}")

    print("\n[6] procesar_insulto — Oscar Wilde")
    r = procesar_insulto("Eres un idiota", "Oscar Wilde")
    print(f"  Original : {r['original']}")
    print(f"  Refinado : {r['version_refinada']}")

    print("\n[7] procesar_insulto — Dr. Mario A. Ramírez Barajas")
    r = procesar_insulto("Eres un inútil", "Dr. Mario A. Ramírez Barajas")
    print(f"  Original : {r['original']}")
    print(f"  Refinado : {r['version_refinada']}")

    print("\n[8] Bibliografía")
    for ref in obtener_bibliografia():
        print(f"  • {ref['autor']} ({ref['año']}). {ref['titulo']}. {ref['editorial']}.")

    opts = listar_opciones()
    print(f"\n[9] Total frases en DB: {opts['total_frases']}")
    print("═" * 62 + "\n")
