# 🌎 Control Territorial / Barrido Comercial / Fase 2
Proyecto para empresa de consumo masivo

# 📌 Contexto del Proyecto
Importante compañía multinacional apuesta a mejorar su capilaridad en la ciudad de Córdoba, conjunto a eficientizar su diseño logístico.

# 📌 Problema Que Resuelve
Problema de subcobertura, en esta segunda fase nos proponemos a caracterizar a los PDV no clientes extrayendo atributos de "details" de la API de Google Maps, a partir de lo cual generamos nuevos indicadores.

# 🎯 Business Questions
*¿Cuáles son los PDV no clientes?
*¿Cuán consolidados están los potenciales clientes?
*¿Cuál es el potencial de los potenciales clientes localizados en la fase anterior?
*¿Cómo priorizamos a los potenciales clientes para ampliar la base de clientes?
# 🧰 Tech Stack
Lenguajes: Python (librerías: pandas, requests)
Análisis Geoespacial: QGIS
APIs: Google Maps API (Nearby Search, Place Details y Text Search), OpenStreetMap (Overpass API)
# 🏗️ Arquitectura
En una segunda extracción a la API obtuve rating y cantidad de reseñas. Con estas nuevas variables generé un nuevo indicador (Consolidación) el mismo pondera para cada caso un 0.6 la cantidad de reseñas obtenidas y un 0.4 la calificación del cliente. Finalmente, puedo deplegar en un mapa los PDV con las nuevas características (consolidación: alta, media y baja).

# 🏗️ Pipeline de Datos
Extracción: El algoritmo recorre la matriz predefinida. Para cada radio/área, ejecuta las consultas a los endpoints de Google Maps, gestionando de forma automática la paginación (next_page_token).
Transformación y Desduplicación: con Python (Pandas), el sistema procesa las respuestas en JSON, normaliza los campos de dirección/coordenadas y aplica una lógica de desduplicación para eliminar solapamientos generados por la cercanía de los radios de búsqueda.
El resultado final es una matriz de datos estandarizada y georreferenciada, lista para ser integrada en el sistemas de información geográfica (QGIS).
mapa
# ✅ Conclusión
De los potenciales clientes claves para ampliar la cuota de mercado en el centro de Córdoba, 7 tienen Alta consolidación, 128 Media consolidación (por mucha reseña y poca calificación o al revés) y 33 son de Baja consolidación.
