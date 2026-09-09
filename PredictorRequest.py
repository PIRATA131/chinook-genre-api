"""
PredictorRequest.py
-------------------
Define el CONTRATO de la API: que datos entran y que datos salen.

Esto es lo que hace que en la pagina /docs aparezcan los cuadritos donde
el profesor va a escribir el correo, el pais y la ciudad. Antes aqui
vivian los campos "sex" y "nuevo"; ahora son los tres de la tarea.
"""

from pydantic import BaseModel, Field


class PredictorRequest(BaseModel):
    """Lo que el usuario manda a POST /api/model."""

    email: str = Field(
        ...,
        description="Correo del cliente. Puede ser completo (juan@gmail.com) "
                    "o solo el proveedor (gmail).",
        examples=["juan@gmail.com"],
    )
    country: str = Field(
        ...,
        description="Pais de origen del cliente.",
        examples=["Brazil"],
    )
    city: str = Field(
        ...,
        description="Ciudad de origen del cliente.",
        examples=["Sao Jose dos Campos"],
    )

    def dominio_email(self) -> str:
        """
        Normaliza el correo al mismo formato con el que se entreno el modelo.

        La vista de SQL guarda solo el proveedor: de "juan@gmail.com"
        guarda "gmail". Si el modelo se entreno con "gmail" y le mandamos
        "juan@gmail.com", no reconoce nada. Por eso aqui recortamos igual.
        """
        texto = self.email.strip().lower()
        if "@" in texto:
            texto = texto.split("@")[1]
        return texto.split(".")[0]


class PredictorResponse(BaseModel):
    """Lo que la API regresa."""

    status: str = "OK"
    result: str = Field(..., description="Genero musical predicho.")
    confidence: float = Field(..., description="Probabilidad que el modelo le da (0 a 1).")
