## Arquitectura general

El programa se dividio en tres componentes:

- **miner**: Programa en python que extrae datos de GitHub y los descarga para tenerlos de forma local en el disco.
- **visualizer**: Servidor web que lee esos datos y los sirve al navegador.
- **shared**: Carpeta compartida entre los otros dos componentes que sirve como canal de comunicación entre ambos.

### Por qué shared

Una base de datos añade complicaciones, ademas de necesitar un tercer contenedor. Un archivo JSON que se va reescribiendo cumple esa función de manera bastante mas sencilla.

La forma de escritura (`write` a `.tmp` + `os.replace`) hace que el visualizer nunca lee un archivo a medias.

---

## Decisiones de diseño del código

### Separación en tres archivos

- `file_manager.py` se encarga de todo lo relacionado con el manejo archivos locales.
- `code_extractor.py` se encarga de lo relacionado con la obtención y el análisis de código (GitHub API, git clone, tree-sitter, extracción de palabras). Es el módulo más grande porque todas estas operaciones van de la mano, se buscan los repositorios, se clonan, se leen y se extraen las palabras.
- `main.py` solo tiene el loop principal y un par de funciones counts.

### Checkpoint

Guardar `repo_index` junto a `page` permite reanudar exactamente desde el repo donde se interrumpió. Esto permite que si el codigo falla, o no puede ejecutarse indefinidamente, seguira a partir del punto donde se quedo la vez anterior.

### git clone

La alternativa era usar la API de GitHub para descargar archivos individuales, pero esto tiene problemas como:

- Requiere una request por archivo. Un repo con 200 archivos Python consume 200 requests de la cuota de 5.000/hora con token, o 60/hora sin él.
- Con `git clone --depth 1` se obtiene el repo completo sin consumir cuota de la API.

El `--depth 1` el historial de commits, reduciendo el tamaño descargado al mínimo necesario, asi aumentando la velocidad de descarga.

### Token de GitHub opcional

Sin token la API de GitHub permite 60 requests/hora por IP. Con token sube a 5.000. El sistema funciona en ambos casos: sin token simplemente procesa menos repos por hora antes de que `check_rate_limit` fuerce una espera.
