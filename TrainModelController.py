"""
TrainModelController.py
-----------------------
LA API. Carga el modelo que dejo el pipeline y lo expone por internet.

Endpoints:
    GET  /api/health-check  -> comprueba que el servicio esta vivo
    POST /api/model         -> recibe email, pais y ciudad; devuelve genero
"""

import os
import pathlib

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException

from PredictorRequest import PredictorRequest, PredictorResponse

RUTA_MODELO = pathlib.Path(os.getenv("MODEL_DIR", "modelo")) / "modelo_genero.pkl"

router = APIRouter()

# El modelo se carga una sola vez y se guarda en memoria. Cargarlo en
# cada peticion seria lento y absurdo.
_modelo = None


def obtener_modelo():
    """Carga el modelo la primera vez que se necesita."""
    global _modelo
    if _modelo is None:
        if not RUTA_MODELO.exists():
            raise HTTPException(
                status_code=503,
                detail=f"El modelo no existe en {RUTA_MODELO}. "
                       f"Hay que correr primero el pipeline (TrainModel.py).",
            )
        _modelo = joblib.load(RUTA_MODELO)
    return _modelo


@router.get("/api/health-check")
def health_check():
    """Endpoint de cortesia. Si responde OK, el contenedor esta arriba."""
    return {"status": "OK"}


@router.post("/api/model", response_model=PredictorResponse)
def predecir_genero(peticion: PredictorRequest):
    """
    Recibe los datos de un cliente y devuelve el genero musical que
    probablemente compraria.

    Ejemplo de entrada:
        {"email": "juan@gmail.com", "country": "Brazil", "city": "Sao Paulo"}

    Ejemplo de salida:
        {"status": "OK", "result": "Rock", "confidence": 0.41}
    """
    modelo = obtener_modelo()

    # Se arma UNA fila con exactamente los mismos nombres de columna y el
    # mismo formato (minusculas, sin espacios) con que se entreno.
    entrada = pd.DataFrame([{
        "email": peticion.dominio_email(),
        "country": peticion.country.strip().lower(),
        "city": peticion.city.strip().lower(),
    }])

    prediccion = modelo.predict(entrada)[0]
    probabilidad = float(modelo.predict_proba(entrada).max())

    return PredictorResponse(
        status="OK",
        result=str(prediccion),
        confidence=round(probabilidad, 4),
    )
