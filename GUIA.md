# Tarea: Pipeline y API publicados — predicción de género musical

API que recibe **correo, país y ciudad** de un cliente y devuelve el **género musical** que probablemente compraría, entrenada con la base Chinook alojada en Supabase y desplegada en contenedores Docker sobre una máquina virtual de AWS.

---

## Los 3 pasos que pidió el profesor

| Paso | Qué es | Dónde se hace |
|---|---|---|
| 1. Vista en Chinook con 4 campos | `sql/01_vista_train_model.sql` | Supabase → SQL Editor |
| 2. Editar el software para entrenar el modelo | `TrainModel.py`, `TrainModelController.py`, `PredictorRequest.py` | Tu repositorio de Git |
| 3. Desplegar en contenedores en la nube | `Dockerfile` + `docker-compose.yml` | Instancia EC2 |

---

## Paso 1 — Crear la vista en Supabase

Entra a tu proyecto Chinook en Supabase, abre **SQL Editor**, pega el contenido de `sql/01_vista_train_model.sql` y ejecuta.

Comprueba que quedó bien:

```sql
SELECT count(*) FROM public.train_model;   -- deben salir 2240 filas
SELECT * FROM public.train_model LIMIT 10;
```

Los 4 campos son:

- `email` → el proveedor del correo (gmail, yahoo, hotmail…). Variable independiente.
- `country` → país. Variable independiente.
- `city` → ciudad. Variable independiente.
- `genre` → género musical. **Variable dependiente**, lo que el modelo predice.

---

## Paso 2 — El código

### Qué cambió respecto a la práctica anterior

En la práctica del `y = x + 3` la entrada era un número y la salida un número: eso es **regresión**. Aquí la entrada son palabras y la salida es una categoría: eso es **clasificación**, y necesita dos piezas nuevas.

**OneHotEncoder.** Un modelo solo entiende números. Este transformador convierte cada categoría en una columna de ceros y unos: `country = Brazil` se vuelve una columna que vale 1 para los clientes brasileños y 0 para el resto. Si en lugar de eso le pusiéramos números (Brasil = 1, Canadá = 2, Alemania = 3), el modelo pensaría que Alemania es "el triple" de Brasil, lo cual no significa nada.

Lleva `handle_unknown="ignore"`, que es lo que evita que la API truene cuando el profesor escriba una ciudad que no está en Chinook.

**RandomForestClassifier.** Un bosque de árboles de decisión. Cada árbol aprende reglas del tipo "si el país es Brasil y el correo es gmail, entonces Latin", y el bosque vota. Se lleva bien con variables categóricas y no necesita ajustes finos.

### Qué esperar del desempeño

Entrené el modelo con los datos reales de Chinook antes de entregarte esto:

| Modelo | Accuracy |
|---|---|
| Predecir siempre el género más común (línea base) | 0.373 |
| Regresión logística | 0.393 |
| **Random Forest** | **0.408** |

Un 41% suena bajo, y conviene que lo tengas claro por si el profesor pregunta. La razón es que la relación real es débil: en Chinook, el 37% de todas las compras son de Rock, y saber que alguien vive en Toronto y usa Hotmail casi no cambia esa probabilidad. El modelo sí aprende algo (gana 3.5 puntos sobre la línea base, y en países con perfil marcado como Brasil se inclina a Latin), pero el techo del problema es ese. Eso no es un error tuyo: es la respuesta honesta que dan los datos, y decirlo así vale más que inflar el número.

---

## Paso 3 — Desplegar en AWS

Tu instancia EC2 ya está lista (Ubuntu 24.04, t3.micro, IP elástica, puerto 8000 abierto y Docker instalado). Falta subir este proyecto y levantarlo.

### 3.1 Subir el código a tu repositorio

Desde tu máquina local, dentro de la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Modelo de prediccion de genero musical - Chinook"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

El `.gitignore` ya excluye el archivo `.env`. **Nunca subas tus credenciales de Supabase a GitHub**: son públicas para cualquiera que vea el repo.

### 3.2 Conectarte a la máquina virtual

Desde la consola de EC2, botón **Conectar** → *Conexión de la instancia EC2*. Ya estás dentro de Ubuntu.

### 3.3 Clonar y configurar

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
cp .env.example .env
nano .env
```

Llena `.env` con tus credenciales reales de Supabase (*Project Settings → Database → Connection string*). Guardas con `Ctrl+O`, `Enter`, y sales con `Ctrl+X`.

### 3.4 Levantar los contenedores

```bash
sudo docker compose up -d --build
```

Esto construye la imagen, corre el contenedor **pipeline** (que entrena contra Supabase y guarda el modelo) y, cuando termina bien, arranca el contenedor **api**.

Revisa que el entrenamiento haya salido:

```bash
sudo docker compose logs pipeline
```

Debe imprimir las filas leídas, el accuracy y "Modelo guardado".

### 3.5 Probar

En tu navegador:

```
http://TU_IP_ELASTICA:8000/docs
```

Prueba `GET /api/health-check` → debe responder `{"status": "OK"}`.

Luego `POST /api/model` con este cuerpo:

```json
{
  "email": "juan@gmail.com",
  "country": "Brazil",
  "city": "Sao Jose dos Campos"
}
```

Respuesta esperada:

```json
{
  "status": "OK",
  "result": "Rock",
  "confidence": 0.41
}
```

### 3.6 Entregar

En Blackboard pega la liga:

```
http://TU_IP_ELASTICA:8000/docs
```

---

## Comandos de Docker que vas a necesitar

| Comando | Para qué |
|---|---|
| `sudo docker compose up -d --build` | Construir y levantar todo |
| `sudo docker compose ps` | Ver qué contenedores están corriendo |
| `sudo docker compose logs -f api` | Ver los mensajes de la API en vivo |
| `sudo docker compose logs pipeline` | Ver cómo salió el entrenamiento |
| `sudo docker compose down` | Apagar los contenedores |
| `sudo docker compose run --rm pipeline` | Reentrenar el modelo sin tocar la API |

---

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El navegador no carga nada en `:8000/docs` | El puerto 8000 no está abierto en el Security Group | En EC2 → Security Groups → regla de entrada TCP 8000 desde 0.0.0.0/0 |
| Carga en la VM pero no desde fuera | Uvicorn arrancó en 127.0.0.1 | Confirma que el comando trae `--host 0.0.0.0` |
| El pipeline truena con error de conexión | Credenciales malas en `.env`, o Supabase pausado | Revisa `.env`; en Supabase, si el proyecto dice *Paused*, reactívalo |
| `relation "public.train_model" does not exist` | No creaste la vista | Ejecuta el Paso 1 |
| La API responde 503 "el modelo no existe" | El pipeline no terminó bien | `sudo docker compose logs pipeline` |
| `permission denied` al usar docker | Tu usuario no está en el grupo docker | Usa `sudo`, o `sudo usermod -aG docker $USER` y reconéctate |
| El proyecto de Supabase se pausó solo | El plan gratuito pausa proyectos inactivos | Reactívalo **antes** de que el profesor califique |

---

## Cómo explicarlo si te pregunta en clase

> Creé una vista en Chinook que cruza cliente, factura, detalle de factura, canción y género, para obtener el proveedor de correo, el país y la ciudad como variables independientes, y el género musical como variable dependiente. El pipeline se conecta a Supabase, lee esa vista, codifica las variables categóricas con One-Hot Encoding y entrena un Random Forest, que guarda serializado en un volumen compartido. La API en FastAPI carga ese modelo y lo expone en `/api/model`. Ambos corren como contenedores Docker separados en una instancia EC2 con IP elástica, publicados en el puerto 8000.
