# 1 carga de librerías
import requests
import pandas as pd
import time
import os
import math
from dotenv import load_dotenv   #busca archivo .env y carga las variables allí definidas
# 2 configuración de la api de forma segura
load_dotenv()

print(f"¿Se cargó el archivo .env?: {load_dotenv()}")
API_KEY = os.getenv("GCP_API_KEY")  # Guarda la clave de Google Cloud para ingresar a la api de maps de forma criptográfica.
if not API_KEY:
    print("❌ ERROR: No se encontró la variable 'GCP_API_KEY' en el archivo .env. Verificá el nombre.")
# 3 Preparación de parametros para la extracción controlada mediante matriz

def generar_grilla (lat_inicio, long_inicio, filas, columnas, distancia_metros = 670):
    puntos = []
    factor_lat = distancia_metros / 111120  # Aproximación de metros a grados latitud
    factor_long = distancia_metros / 95000

    for f in range(filas):
        for c in range(columnas):
            nueva_lat = lat_inicio - (f * factor_lat)
            nueva_long = long_inicio + (c * factor_long)
            puntos.append({"lat": nueva_lat, 
                           "lng": nueva_long})
    return puntos

piloto_zonas = generar_grilla(  # Coordenadas de origen: colon y general paz. matriz 4x3.
    lat_inicio= -31.406872, 
    long_inicio= -64.188811, 
    filas=4, 
    columnas=3, 
    distancia_metros= 670
)

cadenas_multinacionales = ['carrefour', 'vea', 'cencosud', 'disco', 'libertad', 'jumbo', 'chango mas', 'makro'] # cadenas no deseadas
rubros_no_deseados = ['fruteria', 'verduleria', 'dietetica', 'fiambreria', 'granja', 'panadería'] # rubros no deseados
lista_negra = cadenas_multinacionales + rubros_no_deseados

QUERY = "supermercado"  # consulta de interés para filtrar por supermercados
url_nearby = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
lista_comercios = []
ids_procesados = set()  # control de ids duplicados para evitar doble computación

# 4 Primera extracción de acuerdo a los parametros del paso 3
for i, zona in enumerate(piloto_zonas):
    print(f"Escaneando punto {i+1}/{len(piloto_zonas)} (Lat: {zona['lat']:.3f}, Lng: {zona['lng']:.3f})...")
    next_page_token = None
    
    while True:  # estructura del bucle infinito que se rompe cuando no hay mas paginas de resultados (next_page_token es None) y carga los resultados en lista_comercios
        params = {
            'keyword': QUERY,
            'location': f"{zona['lat']},{zona['lng']}",
            'radius': 500, # 500m para cubrir una mancha de 1km de diámetro
            'language': 'es',
            'key': API_KEY
        }
        if next_page_token:  # obtengo token para segunda pagina, si existe
            params['pagetoken'] = next_page_token
            time.sleep(2) # control del tiempo de espera para evitar bloqueo por demora del token en la api

        data = requests.get(url_nearby, params=params).json() # Acá se hace la consulta ala api con los parámetros definidos y transforma la respuesta json en un diccionario de python 
        print(f"Resultados obtenidos en esta página: {len(data.get('results', []))}")
        if data.get('status') == 'OK':
            for item in data.get('results', []):
                p_id = item.get('place_id')
                nombre = item.get('name', '').lower()

                # Solo excluimos si está en la lista negra de gigantes
                if any(gigante in nombre for gigante in lista_negra): 
                    continue
                
                if p_id not in ids_procesados: # si el id del comercio no está en ids_procesados, se incorpora 
                    ids_procesados.add(p_id)
                    lista_comercios.append({
                        'nombre': item.get('name'),
                        'direccion': item.get('vicinity'),
                        'item_id': p_id,
                        'latitud': item.get('geometry', {}).get('location', {}).get('lat'),
                        'longitud': item.get('geometry', {}).get('location', {}).get('lng')
                        
                    })
            
            next_page_token = data.get('next_page_token')
            if not next_page_token: break #si no haytoken para pag siguiente, se rompe el bucle y se pasa a la siguiente zona
        else: break

print(f"Piloto finalizado. Total de comercios únicos encontrados: {len(lista_comercios)}")



## 5 segunda extracción: Paginación para obtener más resultados por consulta

url_details = "https://maps.googleapis.com/maps/api/place/details/json"

for comercio in lista_comercios: # para cada extracción de lista_comercios se consulta la api details
    params_details = {
        'place_id': comercio['item_id'],
        'rating': 'rating', # promedio de puntuaciones de usuarios
        'cantidad_reseñas': 'user_ratings_total', # cantidad de reseñas de usuarios
        'key': API_KEY,
        'language': 'es'

    }

    res_details = requests.get(url_details, params=params_details)
    detalles = res_details.json()

    if detalles.get('status') == 'OK':
        #  Extraemos el teléfono y lo guardamos en nuestro diccionario existente
        info_extra = detalles.get('result', {})
        comercio['cantidad_reseñas'] = int (info_extra.get('user_ratings_total', '0'))
        comercio['rating'] = float (info_extra.get('rating', '0'))
    else:
        comercio['rating'] = 'Error en API'
        comercio['cantidad_reseñas'] = 'Error en API'

    # Un pequeño delay para no saturar la API y evitar bloqueos por exceso de solicitudes
    time.sleep(0.1)



df = pd.DataFrame(lista_comercios)
print(df)

# 6 Generación de nueva variable de rating ponderado

df_validos = df[df["rating"].notna() & df["cantidad_reseñas"].notna()].copy() # filtro para trabajar con casos positivos

if not df_validos.empty:
    q_reseñas_min = df_validos["cantidad_reseñas"]. min() # cantidad mínima de reseñas para normalizar
    q_reseñas_max = df_validos["cantidad_reseñas"]. max() # cantidad máxima de reseñas para normalizar

    #Normalizar el ratin, de 1-5 a 0-1

    df_validos["rating_normalizado"] = ((df_validos["rating"] - 1) / 4).clip(lower = 0) # normalizo el rating a escala 0-1

    df_validos["cantidad_reseñas_normalizada"] = df_validos["cantidad_reseñas"].apply(
        lambda x: math.log(x + 1))
    
    log_min = math.log(q_reseñas_min + 1)
    log_max = math.log(q_reseñas_max + 1)
    df_validos["volumen_norm"] = (df_validos["cantidad_reseñas_normalizada"] - log_min) / (
        log_max - log_min
    )
    
    #  Generar el Índice de Consolidación Comercial (ICC)
    # Ponderación: 60% peso del volumen (mercado), 40% peso del reiting.
    df_validos["ICC"] = (df_validos["volumen_norm"] * 0.6) + (
        df_validos["rating_normalizado"] * 0.4
    )

# Clasificación en base a la condición de consolidación
    def clasificar_consolidacion(icc):
        if icc >= 0.75:
            return "Alta Consolidación"
        elif icc >= 0.45:
            return "Media Consolidación"
        else:
            return "Baja Consolidación"

    df_validos["consolidacion"] = df_validos["ICC"].apply(
        clasificar_consolidacion)

    df = df.merge(
        df_validos
            [[ "item_id", "consolidacion"] ],
        on="item_id",
        how="left",
    )




df.to_csv("rating.csv", index=False)

## ojo con el tamaño de la matriz y el radio, porque Google Maps tiene un límite de 60 casos por consulta
## y el criterio para escoger el comercio a extraer es la proximidad con el punto de la matriz (dentro del radio)
## y el ranking del comercio de acuerdo a interacciones de usuarios (si hay mas de 60 casos ene el radio se ordenan por relevancia)
## por lo que si la matriz y radio son muy grandes, se corre el riesgo de no se incluyan comercios con pocas reseñas.
## y si el radio es muy pequeño aumenta el costo.