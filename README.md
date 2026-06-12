# Validacion de Clasificacion de Preguntas Municipio

Aplicacion local en Streamlit para probar un modelo ya entrenado que clasifica preguntas para un chatbot municipal en dos clases:

- `valida`: la pregunta pertenece al dominio del municipio.
- `no_valida`: la pregunta es fuera de dominio, intenta usar el bot como ChatGPT, o busca vulnerar seguridad / extraer datos.

## Que incluye este repositorio

- App en Streamlit para inferencia interactiva.
- Persistencia local con SQLite para guardar preguntas, predicciones y votos.
- Historial ordenado por interacciones.
- Dataset base reutilizado desde el proyecto de entrenamiento.
- Integracion con un modelo ya exportado con `save_pretrained`.

## Estructura

```text
VALIDACION_CLASIFICACION_PREGUNTAS_MUNICIPIO/
├─ app/
│  └─ streamlit_app.py
├─ data/
│  ├─ raw/
│  │  └─ municipio_validacion_preguntas_400.csv
│  └─ feedback.db
├─ models/
│  ├─ README.md
│  └─ municipio_question_validator/   # ignorado por Git
├─ src/
│  ├─ config.py
│  ├─ inference/
│  │  └─ predictor.py
│  ├─ services/
│  │  └─ validation_service.py
│  └─ storage/
│     ├─ repository.py
│     └─ schema.sql
├─ tests/
│  └─ test_repository.py
├─ streamlit_app.py
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## Modelo

Este repositorio no entrena el modelo. Usa un modelo ya exportado localmente con Hugging Face.

Ruta por defecto:

```text
models/municipio_question_validator
```

Tambien puedes usar otra ruta configurando la variable de entorno `MODEL_DIR`.

Para despliegue, la app ahora soporta dos modos:

1. Modelo local en `MODEL_DIR`.
2. Descarga automatica desde Hugging Face si defines `MODEL_REPO_ID`.

La descarga remota guarda el modelo en cache local y evita archivos de entrenamiento pesados como `optimizer.pt` o `checkpoints/`.

## Dataset de referencia

El dataset base incluido en `data/raw/municipio_validacion_preguntas_400.csv` contiene ejemplos `valida` y `no_valida` con subtipo.

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar la app

```bash
streamlit run streamlit_app.py
```

## Variables configurables

- `MODEL_DIR`: ruta alternativa al modelo entrenado.
- `MODEL_REPO_ID`: identificador del repositorio del modelo en Hugging Face.
- `MODEL_REVISION`: rama, tag o commit del modelo en Hugging Face. Por defecto `main`.
- `MODEL_CACHE_DIR`: carpeta local donde se descargara el modelo remoto.
- `DATABASE_PATH`: ruta alternativa para la base SQLite.
- `APP_TITLE`: titulo de la aplicacion.

## Modo administrador

La app puede habilitar moderacion simple desde `st.secrets`.

Archivo local:

```toml
ADMIN_PASSWORD = "tu-clave-segura"
```

Comportamiento:

- Si `ADMIN_PASSWORD` no existe, nadie vera el modo administrador.
- Si existe, cualquier visitante vera la app como usuario normal.
- Solo quien conozca la clave y la ingrese en la barra lateral podra activar `Modo administrador`.
- En ese modo aparece el boton `Ocultar del historial`.

Al desplegar en Streamlit Community Cloud, esa clave debe cargarse en la seccion `Secrets` del panel de la app. Los secretos no se muestran a los visitantes, pero si alguien conoce tu clave podria entrar como administrador.

## Despliegue recomendado en Streamlit

Para que la app funcione bien en Streamlit Community Cloud:

- Sube a GitHub solo el codigo de la app.
- No subas la carpeta completa del modelo si pesa mas de lo que GitHub tolera.
- Publica el modelo de inferencia en Hugging Face.
- Configura en Streamlit los secrets o variables necesarias.

Ejemplo de secrets para despliegue:

```toml
ADMIN_PASSWORD = "tu-clave-segura"
MODEL_REPO_ID = "tu-usuario/tu-modelo"
MODEL_REVISION = "main"
```

Si el modelo remoto es publico, no necesitas token. Si fuera privado, haria falta agregar un token de Hugging Face y extender la app para usarlo.

## Checklist para Streamlit Community Cloud

Valores recomendados al crear la app:

- Repository: `Nahuel247/VALIDACION_CLASIFICACION_PREGUNTAS_MUNICIPIO`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: `3.12`

Secrets sugeridos para pegar en `Advanced settings > Secrets`:

```toml
ADMIN_PASSWORD = "tu-clave-segura"
MODEL_REPO_ID = "tu-usuario/tu-modelo"
MODEL_REVISION = "main"
```

Flujo:

1. Entra a [share.streamlit.io](https://share.streamlit.io/).
2. Haz clic en `Create app`.
3. Selecciona el repo `Nahuel247/VALIDACION_CLASIFICACION_PREGUNTAS_MUNICIPIO`.
4. Usa `streamlit_app.py` como archivo principal.
5. En `Advanced settings`, elige Python `3.12` y pega tus secrets.
6. Despliega la app.

## Como funciona el feedback

Cada vez que una persona clasifica una pregunta:

- se guarda la pregunta,
- se guarda la prediccion y su confianza,
- si la misma pregunta vuelve a aparecer, sube el conteo de interacciones,
- otras personas pueden votar `Correcta` o `Incorrecta`.

El historial se ordena por `interacciones = veces_preguntada + votos positivos + votos negativos`.

## Limitaciones

- No hay autenticacion de usuarios en esta version.
- Los votos se restringen a una vez por sesion del navegador, no por identidad real.
- SQLite es suficiente para demo local, no para alta concurrencia.
- El modelo puede equivocarse en casos frontera o preguntas ambiguas.

## Relacion con el repositorio de entrenamiento

Este repositorio fue pensado para desacoplar la demo / inferencia del pipeline de entrenamiento. El script original de entrenamiento y la investigacion del modelo deben mantenerse en otro repositorio y otra publicacion.

## Mejoras futuras

- Login y moderacion.
- Dashboard admin.
- Exportacion de feedback para reentrenamiento.
- Version desplegable en nube.
- Analitica avanzada por subtipo y confianza.
