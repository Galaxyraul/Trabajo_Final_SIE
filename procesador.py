import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd
import time
import numpy as np
import requests
import os
import random

BASE_URL = "https://opendata.aemet.es/opendata/api"
PATH_ZONAS_INUNDABLES = './zonas_inundables/datos_andalucia.shp'
PATH_MAPAS = './mapas/municipios_andalucia.shp'
PATH_DATOS_CLIMATOLOGICO = './online'
PATH_API = './API_KEY.txt'
PATH_DICCIONARIO = './diccionario.xlsx'
PATH_DATA = './online/data.csv'

class Mapa:
    def __init__(self):
        self.mapa = create_map()
        self.mapa_risky = create_map_risky()
        
    def get_municipio(self,municipio):
        data = self.mapa[self.mapa['nombre'] == municipio]
        return paint_map(data,municipio),(int)(data['riesgo'].iloc[0])
    
    def get_andalucia(self):
        return paint_map(self.mapa,'Toda Andalucia')
    
    def get_municipio_risky(self,municipio):
        data = self.mapa_risky[self.mapa_risky['nombre'] == municipio]
        return paint_map(data,f"{municipio} Risky"),(int)(data['riesgo'].iloc[0])
    
    def get_andalucia_risky(self):
        return paint_map(self.mapa_risky,'Toda Andalucia Risky')
    

def paint_map(data,data_name):
    color_dict = {
        0: 'green',  
        1: 'yellow', 
        2: 'red',     
        3: 'black'    
    }
    data['color'] = data['riesgo'].map(color_dict)
    fig, ax = plt.subplots(figsize=(10, 8))
    data.plot(ax=ax, color=data['color'], edgecolor='black')
    ax.set_title(f"Mapa de riesgo para: {data_name}")
    ax.set_axis_off()
    # Save the plot as an image
    image_path = f'./images/{data_name}_map.png'
    plt.savefig(image_path)
    plt.close()
    return image_path

def load_mapa(path):
    return gpd.read_file(path,encoding='utf-8')
    
def load_diccionario(path):
    return pd.read_excel(path)

def load_data(path):
    return pd.read_csv(path,encoding='utf-8')

def load_key(path):
    with open (path,'r') as f:
        key = f.read()
    return key


def add_datos_clima(zonas_inundables,datos_clima):
    datos_clima['precipitaciones'] = datos_clima['precipitaciones']/1000
    zonas_inundables = zonas_inundables.merge(datos_clima,left_on='COD',right_on='COD')
    condiciones = [
        zonas_inundables['precipitaciones'] > zonas_inundables['Q_M3_S'],                
        zonas_inundables['precipitaciones'] > 0.8 * zonas_inundables['Q_M3_S'],          
        zonas_inundables['precipitaciones'] > 0.5 * zonas_inundables['Q_M3_S']            
        ]
    valores = [3, 2, 1]
    zonas_inundables['riesgo'] = np.select(condiciones, valores, default=0)
    return zonas_inundables

def get_mapa(municipios_andalucia,riesgos_municipios):
    mapa = municipios_andalucia.merge(riesgos_municipios,how='outer',left_on='nombre',right_on='NOMBRE')
    mapa['riesgo'] = mapa['riesgo'].fillna(0)
    mapa=mapa.drop_duplicates(subset =['nombre_x'],keep='first')
    mapa = mapa.rename(columns={'nombre_x': 'nombre'})
    return mapa

def obtener_precipitacion(API_KEY,codigo_ine):
    # Endpoint de predicción diaria para el municipio
    endpoint = f"/prediccion/especifica/municipio/horaria/{codigo_ine}"
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}

    # Paso 1: Solicitar la URL temporal
    try:
      response = requests.get(url, params=params)
    except Exception as e:
      print(f"Error en la solicitud para municipio {codigo_ine}: {e}")
      return [429]

    if response.status_code != 200:
        return [response.status_code]

    # Paso 2: Descargar los datos desde la URL temporal
    datos_url = response.json().get("datos")
    if not datos_url:
        print(f"No se pudo obtener la URL de datos para municipio {codigo_ine}")
        return [404]

    datos_response = requests.get(datos_url)
    if datos_response.status_code != 200:
        print(f"Error al descargar datos para municipio {codigo_ine}: {datos_response.status_code}")
        return [datos_response.status_code]

    # Extraer datos de precipitación
    datos = datos_response.json()
    # La estructura del JSON puede variar; adaptamos para predicciones
    try:
        prediccion_hoy = datos[0]["prediccion"]["dia"][0]  # Día actual
        precipitacion_dia = prediccion_hoy.get("precipitacion", "No disponible")
        precipitaciones = pd.DataFrame(precipitacion_dia)
        precipitaciones['value'] = pd.to_numeric(precipitaciones['value'], errors='coerce')
        return [200,precipitaciones['value'].sum()]
    except Exception as e:
        print(f"Error al procesar datos para municipio {codigo_ine}: {e}")
        return None
    
def request_aemet(API_KEY,code_list):
    dic_precipitaciones = {}
    tries = 2
    for codigo in code_list:
        for i in range(tries):
            precipitacion = obtener_precipitacion(API_KEY,codigo)
            if precipitacion[0] == 429:
                time.sleep(60)
            elif precipitacion[0] != 200:
                dic_precipitaciones[codigo] = -1
                break
            else:
                dic_precipitaciones[codigo] = precipitacion[1]
                break
    
def clean_zonas_inundables(zonas_inundables,diccionario):
    volumenes = zonas_inundables[['nombre','Q_M3_S']]
    volumenes['Q_M3_S'] = volumenes['Q_M3_S'].str.replace(',', '.')
    volumenes['Q_M3_S'] = volumenes['Q_M3_S'].str.split(';').str[0]
    volumenes['Q_M3_S'] = pd.to_numeric(volumenes['Q_M3_S'], errors='coerce')
    volumenes.dropna(subset=['Q_M3_S'],inplace=True)
    volumenes = volumenes.merge(diccionario,left_on='nombre',right_on='NOMBRE')
    return volumenes

def create_map_risky():
    probabilities = {
        0: 0.8,
        1: 0.1, 
        2: 0.002, 
        3: 0.002
    }
    
    mapa = municipios_andalucia = load_mapa(PATH_MAPAS)
    mapa['riesgo'] = random.choices(list(probabilities.keys()), weights=list(probabilities.values()), k=len(mapa))
    mapa.loc[mapa['nombre'] == 'Jaén', 'riesgo'] = 3
    return mapa

def create_map():
    API_KEY = load_key(PATH_API)
    zonas_inundables = load_mapa(PATH_ZONAS_INUNDABLES)
    municipios_andalucia = load_mapa(PATH_MAPAS)
    diccionario = load_diccionario(PATH_DICCIONARIO)
    zonas_inundables = clean_zonas_inundables(zonas_inundables,diccionario)
    if(os.listdir(PATH_DATOS_CLIMATOLOGICO) != 0):
        datos_clima = load_data(PATH_DATA)
    else:
        datos_clima = request_aemet(API_KEY,zonas_inundables['COD'].unique())
    riesgos_municipios = add_datos_clima(zonas_inundables,datos_clima)
    mapa = get_mapa(municipios_andalucia,riesgos_municipios)
    return mapa
instancia_mapa = Mapa()

