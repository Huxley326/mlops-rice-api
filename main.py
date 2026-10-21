"""API de predicción para el modelo Rice Cammeo/Osmancik de Databricks."""

import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field


DATABRICKS_URL = os.getenv("DATABRICKS_URL", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")

FEATURES = [
    "Area",
    "Perimeter",
    "Major_Axis_Length",
    "Minor_Axis_Length",
    "Eccentricity",
    "Convex_Area",
    "Extent",
    "Axis_Ratio",
    "Solidity",
    "Circularity",
]


class GranoArroz(BaseModel):
    # Las diez entradas coinciden con la firma del modelo ganador de NB02.
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    Area: int = Field(gt=0)
    Perimeter: float = Field(gt=0)
    Major_Axis_Length: float = Field(gt=0)
    Minor_Axis_Length: float = Field(gt=0)
    Eccentricity: float = Field(ge=0, le=1)
    Convex_Area: int = Field(gt=0)
    Extent: float = Field(gt=0, le=1)
    Axis_Ratio: float = Field(gt=0)
    Solidity: float = Field(gt=0, le=1)
    Circularity: float = Field(gt=0)


app = FastAPI(title="API MLOps Arroz", description="Clasifica granos Cammeo u Osmancik")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "databricks_configurado": bool(DATABRICKS_URL and DATABRICKS_TOKEN),
    }


@app.post("/predecir")
def predecir(grano: GranoArroz):
    if not DATABRICKS_URL or not DATABRICKS_TOKEN:
        raise HTTPException(status_code=500, detail="Faltan credenciales de Databricks")

    valores = grano.model_dump()
    payload = {
        "dataframe_split": {
            "columns": FEATURES,
            "data": [[valores[c] for c in FEATURES]],
        }
    }

    try:
        respuesta = requests.post(
            DATABRICKS_URL,
            headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
            json=payload,
            timeout=120,
        )
    except requests.exceptions.Timeout as exc:
        raise HTTPException(status_code=504, detail="Databricks tardó demasiado") from exc
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail="No se pudo conectar con Databricks") from exc

    if respuesta.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Databricks respondió HTTP {respuesta.status_code}",
        )

    try:
        prediccion = int(respuesta.json()["predictions"][0])
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise HTTPException(status_code=502, detail="Respuesta inesperada de Databricks") from exc

    if prediccion not in (0, 1):
        raise HTTPException(status_code=502, detail="Clase inesperada de Databricks")

    return {
        "prediccion": prediccion,
        "clase": "Cammeo" if prediccion == 1 else "Osmancik",
    }
