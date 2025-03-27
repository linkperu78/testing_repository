import sys
import pandas as pd
import warnings
import traceback
import logging
import argparse
import yaml
from urllib.parse import urljoin

from IA.ia_utils import api_request
from IA.forecast_neuralprophet.forecast_utils import *

warnings.filterwarnings("ignore")

# Leer configuración desde YAML
with open(f'{script_folder}/configForecast.yml', 'r') as file:
    config = yaml.safe_load(file)

# Configurar el parser de argumentos
parser = argparse.ArgumentParser(description="Script para manejar la predicción y la inserción de datos.")
parser.add_argument('--insert', type=str, default='False', 
                    help='Indica si se deben insertar los datos en la base de datos (True/False)')
parser.add_argument('--forecast', type=str, default=None, 
                    help='Indica que modelo de forecast se desea crear (V, H o RX)')
parser.add_argument('--limit', type=int, default=1000, 
                    help='Número máximo de registros a obtener.')
parser.add_argument('--offset', type=int, default=0, 
                    help='Offset en la consulta.')
args = parser.parse_args()

forecast_types = [args.forecast] if args.forecast else ['H', 'V', 'RX']
limit = args.limit
offset = args.offset

for forecast_type in forecast_types:
    if forecast_type not in ['H', 'V', 'RX']:
        print(f"Forecast '{forecast_type}' no es válido. Debe ser 'V', 'H' o 'RX'.")
        sys.exit(1)

    forecast_name, model_folder = forecast_setting(forecast_type, script_folder)
    if forecast_name is None or model_folder is None:
        print("Error al configurar el forecast.")
        print(forecast_name, model_folder)
        sys.exit(1)

    insert = args.insert.lower() == 'true'

    logging.basicConfig(filename=f'/{model_folder}/prediccion_{forecast_name}.log', 
                        level=logging.INFO, 
                        format='%(asctime)s:%(levelname)s:%(message)s')

    DB_API_URL = config["db_api_url"]
    INVENTORY_PMP_URL = urljoin(DB_API_URL, config["inventario_pmp_url"])
    CAMBIUM_DATA_IP_URL_BASE = urljoin(DB_API_URL, config["cambium_data_ip_url_base"])

    pmp_files = api_request(url=INVENTORY_PMP_URL, dataframe=True)
    subscribers = pmp_files[pmp_files["tipo"].str.contains("PMP", na=False, case=False)]["ip"].unique()

    lstfinal = []
    for subs in subscribers:
        url = urljoin(CAMBIUM_DATA_IP_URL_BASE, f"{subs}?limit={limit}&offset={offset}")
        print(url)
        results = api_request(url, dataframe=False)
        if results:
            lstfinal.extend(results)

    df_raw = pd.DataFrame(lstfinal)
    if df_raw.empty:
        print("No hay datos para procesar.")
        continue

    prediction_column = get_prediction_column(forecast_name)

    df_raw['snr_h'] = df_raw['snr'].apply(lambda x: extract_value(x, 'snr_h'))
    df_raw['snr_v'] = df_raw['snr'].apply(lambda x: extract_value(x, 'snr_v'))
    df_raw['rx'] = df_raw['link_radio'].apply(lambda x: extract_value(x, 'rx'))

    df = df_raw[['fecha', 'ip', prediction_column]]
    df = df.rename(columns={'fecha': 'ds', prediction_column: 'y'})
    df = df.drop_duplicates(subset=['ds', 'ip'])

    df['ds'] = pd.to_datetime(df['ds'])
    df['ds'] = df['ds'].apply(lambda x: x.replace(second=0, microsecond=0))
    df['ds'] = df['ds'].dt.round('15min')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')

    if df['y'].isna().sum() > 0:
        print(f"Advertencia: {df['y'].isna().sum()} valores no convertibles a numérico. Se imputarán con la media.")
        df['y'] = df['y'].fillna(df['y'].mean())

    df_group = df.groupby('ip')
    print(f"Forecast: {forecast_name}")
    lista_predicciones = []

    for ip in list(df_group.groups.keys()):
        print("IP seleccionada: ", ip)
        try:
            df_ip = df_group.get_group(ip)
            df_ip = df_ip.drop_duplicates(subset=['ds'])

            if forecast_name in ["SNR_V", "SNR_H", "RX"]:
                q = predict(df_ip, ip, model_folder, forecast_name, logging, 5)
                if q is not None:
                    lista_predicciones.append(q)
        except Exception as e:
            print(f"Error = {e}")
            print(traceback.format_exc())
            logging.error(f"Error = {e}")
            logging.error(traceback.format_exc())

    if not lista_predicciones:
        print("No hay datos para insertar.")
        continue

    print(lista_predicciones)
    print(type(lista_predicciones))

    if insert and lista_predicciones:
        print("Insertando en la base de datos.")
        try:
            url_add_list_prediccion = urljoin(DB_API_URL, config["predicciones_list_add"])
            print(url_add_list_prediccion)
            api_request(url_add_list_prediccion, method="POST", data=lista_predicciones)
        except Exception as e:
            print(f"Error = {e}")
            print(traceback.format_exc())
            logging.error(f"Error = {e}")
            logging.error(traceback.format_exc())
    else:
        print("No se insertarán los datos en la base de datos.")
        logging.info("No se insertarán los datos en la base de datos.")
        print("Datos de predicción:")
        for i in lista_predicciones:
            print(i)
