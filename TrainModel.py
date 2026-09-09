"""
TrainModel.py
-------------
EL PIPELINE. Se conecta a la base Chinook en Supabase, lee la vista
public.train_model, entrena un clasificador de genero musical y deja el
modelo entrenado guardado en disco para que la API lo use.

Se ejecuta:
    python TrainModel.py

En Docker es el contenedor "pipeline": corre, entrena, guarda y termina.
"""

import os
import pathlib

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Lee el archivo .env con las credenciales de Supabase
load_dotenv()

COLUMNAS_X = ["email", "country", "city"]   # variables independientes
COLUMNA_Y = "genre"                          # variable dependiente

CARPETA_MODELO = pathlib.Path(os.getenv("MODEL_DIR", "modelo"))
RUTA_MODELO = CARPETA_MODELO / "modelo_genero.pkl"


# ---------------------------------------------------------------------
# 1) CONEXION A LA BASE
# ---------------------------------------------------------------------
def crear_conexion():
    """
    Arma la cadena de conexion a PostgreSQL (Supabase) con lo que
    haya en el archivo .env.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        url = (
            f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'postgres')}"
        )
    return create_engine(url)


def cargar_datos() -> pd.DataFrame:
    """Trae la vista completa a un DataFrame de pandas."""
    motor = crear_conexion()
    consulta = f"SELECT {', '.join(COLUMNAS_X)}, {COLUMNA_Y} FROM public.train_model"
    datos = pd.read_sql(consulta, motor)
    print(f"Filas leidas de la vista: {len(datos)}")
    return datos


# ---------------------------------------------------------------------
# 2) LIMPIEZA
# ---------------------------------------------------------------------
def limpiar(datos: pd.DataFrame) -> pd.DataFrame:
    """
    Quita filas incompletas y estandariza el texto a minusculas sin
    espacios sobrantes. Esto importa mucho: si en la base dice "Brazil"
    y el profesor escribe " brazil ", tienen que coincidir.
    """
    datos = datos.dropna(subset=COLUMNAS_X + [COLUMNA_Y]).copy()
    for columna in COLUMNAS_X:
        datos[columna] = datos[columna].astype(str).str.strip().str.lower()
    return datos


# ---------------------------------------------------------------------
# 3) ENTRENAMIENTO
# ---------------------------------------------------------------------
def entrenar(datos: pd.DataFrame) -> Pipeline:
    """
    Construye y entrena el modelo.

    Ojo con esto, es la diferencia clave contra la practica anterior:
    antes la entrada era un numero y usabamos REGRESION. Aqui la entrada
    son PALABRAS y la salida es una CATEGORIA (el genero), asi que el
    problema es de CLASIFICACION.

    Un modelo no entiende palabras, solo numeros. Por eso usamos
    OneHotEncoder: convierte cada categoria en una columna de ceros y
    unos. "country = Brazil" se vuelve una columna que vale 1 cuando el
    cliente es de Brasil y 0 en los demas casos.

    handle_unknown="ignore" evita que la API truene si el profesor
    escribe un pais o una ciudad que no estaban en los datos.
    """
    X = datos[COLUMNAS_X]
    y = datos[COLUMNA_Y]

    X_entrena, X_prueba, y_entrena, y_prueba = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocesador = ColumnTransformer(
        transformers=[("categorias", OneHotEncoder(handle_unknown="ignore"), COLUMNAS_X)]
    )

    modelo = Pipeline(
        steps=[
            ("preprocesador", preprocesador),
            ("clasificador", RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                n_jobs=-1,
            )),
        ]
    )

    modelo.fit(X_entrena, y_entrena)

    exactitud = accuracy_score(y_prueba, modelo.predict(X_prueba))
    print(f"Accuracy en datos de prueba: {exactitud:.3f}")
    print(f"Generos que el modelo puede predecir: {len(modelo.classes_)}")

    return modelo


# ---------------------------------------------------------------------
# 4) GUARDADO
# ---------------------------------------------------------------------
def guardar(modelo: Pipeline) -> None:
    CARPETA_MODELO.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, RUTA_MODELO)
    print(f"Modelo guardado en {RUTA_MODELO}")


def main() -> None:
    print("=== PIPELINE: entrenamiento del modelo de genero musical ===")
    datos = limpiar(cargar_datos())
    modelo = entrenar(datos)
    guardar(modelo)
    print("=== Pipeline terminado ===")


if __name__ == "__main__":
    main()
