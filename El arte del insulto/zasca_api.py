"""
╔══════════════════════════════════════════════════════════════╗
║          Z A S C A  —  API REST (FastAPI) v2.0              ║
║     "El arte de poner a cada quién en su lugar."            ║
╚══════════════════════════════════════════════════════════════╝

Arrancar:
  uvicorn zasca_api:app --reload --port 8000

Docs interactivas:
  http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional
import os

from zasca_engine import (
    filtrar_frase,
    boton_emergencia,
    procesar_insulto,
    listar_opciones,
    obtener_bibliografia,
    AUTORES_VALIDOS,
    NIVELES_VALIDOS,
)

# ── App ───────────────────────────────────────────────────────

app = FastAPI(
    title="ZASCA API",
    description=(
        "**El arte de poner a cada quién en su lugar.**\n\n"
        "Motor lógico con 134 frases de ataque literario, "
        "13 Salidas Elegantes y refinamiento de insultos vulgares.\n\n"
        "**Autores disponibles:** Macedonio Fernández, Oscar Wilde, "
        "Juan José Millás, Groucho Marx, Schopenhauer, "
        "Dr. Mario A. Ramírez Barajas, Usuario (Tú)"
    ),
    version="2.0.0",
    contact={"name": "ZASCA Industrial Heavy · Dr. Mario A. Ramírez Barajas"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos ───────────────────────────────────────────────────

class ZascaRequest(BaseModel):
    autor: str = Field(
        ...,
        example="Groucho Marx",
        description="Autor del zasca. Ver /opciones para la lista completa."
    )
    nivel_veneno: str = Field(
        ...,
        example="Letal",
        description="Intensidad: Sutil | Cáustico | Letal  (o Directo para Usuario)"
    )

class ZascaResponse(BaseModel):
    id: str
    autor: str
    nivel: str
    texto: str
    match_tipo: str

class EmergenciaResponse(BaseModel):
    id: str
    texto: str
    tipo: str

class InsultoRequest(BaseModel):
    frase_vulgar: str = Field(..., example="Eres un idiota")
    autor: str = Field(
        ...,
        example="Oscar Wilde",
        description="Autor cuyo estilo se aplicará al refinamiento."
    )

class InsultoResponse(BaseModel):
    original: str
    autor: str
    version_refinada: str
    estilo_aplicado: str

class BibliografiaItem(BaseModel):
    autor: str
    año: int
    titulo: str
    editorial: str


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/", tags=["General"], include_in_schema=False)
def raiz():
    """Sirve el frontend HTML."""
    html_path = os.path.join(os.path.dirname(__file__), "frontend.html")
    return FileResponse(html_path, media_type="text/html")


@app.get("/manifest.json", include_in_schema=False)
def pwa_manifest():
    """Manifiesto PWA para instalar como app en móvil."""
    return JSONResponse({
        "name": "ZASCA — El arte del insulto literario",
        "short_name": "ZASCA",
        "description": "El arte de poner a cada quién en su lugar.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#16110a",
        "theme_color": "#16110a",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><rect width='512' height='512' fill='%2316110a'/><text x='50%25' y='58%25' font-family='serif' font-size='260' font-weight='bold' fill='%23c9a84c' text-anchor='middle'>Z</text></svg>",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    })


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    """Service Worker para funcionamiento offline."""
    sw = """
const CACHE = 'zasca-v1';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['/'])));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});
self.addEventListener('fetch', e => {
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).catch(() => caches.match('/')));
  }
});
"""
    return PlainTextResponse(sw, media_type="application/javascript")


@app.get("/api", tags=["General"])
def api_info():
    """Información JSON de la API (para integraciones externas)."""
    return {
        "app":     "ZASCA",
        "version": "2.0.0",
        "eslogan": "El arte de poner a cada quién en su lugar.",
        "autoria": "Dr. Mario A. Ramírez Barajas",
        "frases":  134,
        "endpoints": {
            "POST /zasca":        "Obtener zasca filtrado por autor y nivel",
            "GET  /emergencia":   "Salida elegante aleatoria",
            "POST /refinar":      "Refinar insulto vulgar al estilo del autor",
            "GET  /opciones":     "Listar autores y niveles válidos",
            "GET  /bibliografia": "Bibliografía del proyecto ZASCA",
        },
    }


@app.post(
    "/zasca",
    response_model=ZascaResponse,
    tags=["Motor Principal"],
    summary="Obtener zasca",
    description=(
        "Filtra la base de 134 frases por **autor** y **nivel_veneno**. "
        "Usa búsqueda en cascada: exacto → nivel más cercano → fallback global. "
        "Para el autor `Usuario (Tú)` devuelve una frase de estilo directo."
    ),
)
def obtener_zasca(payload: ZascaRequest):
    if payload.autor not in AUTORES_VALIDOS and payload.autor.lower() not in ("usuario (tú)", "usuario"):
        raise HTTPException(
            status_code=422,
            detail=f"Autor inválido. Opciones: {AUTORES_VALIDOS}"
        )
    nivel = payload.nivel_veneno
    if nivel not in NIVELES_VALIDOS and nivel != "Directo":
        raise HTTPException(
            status_code=422,
            detail=f"Nivel inválido. Opciones: {NIVELES_VALIDOS + ['Directo']}"
        )
    return filtrar_frase(payload.autor, payload.nivel_veneno)


@app.get(
    "/emergencia",
    response_model=EmergenciaResponse,
    tags=["Motor Principal"],
    summary="Botón de emergencia — Salida Elegante",
    description=(
        "Ignora todos los filtros y devuelve una **Salida Elegante** aleatoria. "
        "Para retirarse de cualquier conversación con estilo y sin escalada."
    ),
)
def emergencia():
    return boton_emergencia()


@app.post(
    "/refinar",
    response_model=InsultoResponse,
    tags=["Motor Principal"],
    summary="Refinar insulto vulgar",
    description=(
        "Recibe una frase vulgar y la transforma al estilo literario "
        "del autor seleccionado. Preserva la intención, eleva el registro."
    ),
)
def refinar(payload: InsultoRequest):
    if not payload.frase_vulgar.strip():
        raise HTTPException(status_code=422, detail="La frase no puede estar vacía.")
    if payload.autor not in AUTORES_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail=f"Autor inválido. Opciones: {AUTORES_VALIDOS}"
        )
    return procesar_insulto(payload.frase_vulgar, payload.autor)


@app.get(
    "/opciones",
    tags=["Utilidades"],
    summary="Listar valores válidos para el frontend",
    description=(
        "Devuelve autores (con id, nombre e inicial para la pantalla de entrada), "
        "niveles y conteo total de frases."
    ),
)
def opciones():
    return listar_opciones()


@app.get(
    "/bibliografia",
    response_model=list[BibliografiaItem],
    tags=["Utilidades"],
    summary="Bibliografía del proyecto ZASCA",
    description=(
        "Devuelve las referencias bibliográficas completas que sustentan "
        "el corpus literario de ZASCA."
    ),
)
def bibliografia():
    return obtener_bibliografia()
