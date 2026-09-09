"""
main.py
-------
Punto de entrada de la API. Solo crea la aplicacion y le engancha el
controlador.

Se levanta con:
    uvicorn main:app --host 0.0.0.0 --port 8000

El --host 0.0.0.0 es CRITICO en la nube: significa "acepta conexiones de
cualquier direccion". Si se deja el valor por defecto (127.0.0.1) la API
solo se ve dentro de la maquina virtual y el profesor no podria entrar.
"""

from fastapi import FastAPI

from TrainModelController import router

app = FastAPI(
    title="API - Prediccion de genero musical (Chinook)",
    description="Recibe correo, pais y ciudad de un cliente y predice el "
                "genero musical que compraria.",
    version="1.0.0",
)

app.include_router(router)
