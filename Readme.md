# GitHub Miner Visualizer

Herramienta que extrae y analiza nombres de funciones de repositorios públicos de GitHub, mostrando las palabras más frecuentes en tiempo real a través de un visualizador web.

## Cómo funciona

- El **miner** busca repositorios populares en GitHub, los clona localmente, extrae los nombres de funciones de archivos Python y Java, y acumula las palabras en un archivo `shared/words.json`.
- El **visualizer** sirve una página web que se actualiza en tiempo real mediante WebSocket cada vez que el miner escribe nuevos resultados.

## Requisitos

- Docker
- Docker Compose

## Configuración

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```env
GITHUB_TOKEN="tu_token_aqui"
PORT=8080
```

- `GITHUB_TOKEN`: token de GitHub para aumentar el límite de requests de 60 a 5.000 por hora. Opcional, sin token el miner funciona con límite reducido.
- `PORT`: puerto en el que se expone el visualizador. Por defecto `8080`.

## Uso

```bash
docker compose up --build
```

Abre el navegador en `http://localhost:8080` (o el puerto que hayas definido).

Para detener:

```bash
docker compose down
```
