
from neuralprophet import NeuralProphet
import pickle
from datetime import datetime, timedelta
import pandas as pd
import os
import json
import re
import numpy as np

## Folder path
script_path                 = os.path.abspath(__file__)
script_folder               = os.path.dirname(script_path)

#Funcion de filtro
def filter_data(sublist, snr_type):
    if snr_type == "AirRx":
        # Postprocesamiento: concatenar ip y oid en una sola columna llamada 'ip'
        processed_list = []
        for result in sublist:
            concatenated_ip = f"{result['IP']}_{result['OID']}_{result['CodeName']}"
            processed_result = {
                'ip': concatenated_ip,
                'ds': result['Datetime'],
                'y': result['Value']
            }
            processed_list.append(processed_result)
        return processed_list
    if snr_type == "RX":
        return sublist
    else:
        filtered_list = []
        for item in sublist:
            ip, timestamp, snr_data = item
            match_v = re.search(r'([\d\.]+) V', snr_data)  # Captura números decimales
            match_h = re.search(r'([\d\.]+) H', snr_data)  # Captura números decimales
            if match_v and snr_type == "V":
                snr = float(match_v.group(1))  # Convertir a decimal (float)
            elif match_h and snr_type == "H":
                snr = float(match_h.group(1))  # Convertir a decimal (float)
            else:
                snr = None
            filtered_list.append([ip, timestamp, snr])
    return filtered_list

def agregar_ruido_si_igual(df_group):
    # Verificar si todos los valores de 'y' son iguales
    if df_group['y'].nunique() == 1:
        print("Todos los valores de 'y' son iguales. Agregando ruido...")
        ruido = np.random.normal(0, 1e-6, df_group.shape[0])
        df_group['y'] = df_group['y'] + ruido
        return df_group
    else:
        print("Los valores de 'y' no son todos iguales. No se agregará ruido.")
        return df_group

def create_model(dataframe, ip, script_folder, N_FORECAST, GROWTH, YEARLY_SEASONALITY, WEEKLY_SEASONALITY, DAILY_SEASONALITY, N_LAGS, LEARNING_RATE, NORMALIZE, EPOCHS, forecast_name):
    print(f"Creando modelo para la IP: {ip} MODELO {forecast_name}")
    df_group = dataframe.get_group(ip)
    df_group=df_group.reset_index(drop=True)

    start_date = df_group['ds'].min()
    end_date = df_group['ds'].max()
    print("start", start_date, "end", end_date)
    #dall = pd.date_range(start=df_group["ds"][0], end=df_group["ds"][len(df_group)-1], freq="1T")
    dall = pd.date_range(start=start_date, end=end_date, freq="1T")
    print("dall", dall)
    df_group=df_group.drop_duplicates(subset=['ds', 'ip'], keep='last')
    df_group = df_group.set_index('ds')
    print(df_group.index.is_unique)
    duplicated_index = df_group.index.duplicated(keep=False)
    duplicated_rows = df_group[duplicated_index]
    print("Filas con índices duplicados:")
    print(duplicated_rows)
    df_group=df_group.reindex(dall, method='bfill')
    print("df group post dall")
    print(df_group)
    df_group=df_group.reset_index()

    print("Dataframe post reset_index")
    print(df_group)

    df_group.rename(columns={"index": "ds"}, inplace=True)
    df_group=df_group[["ds","y"]]
    print(f"Número de filas en el DataFrame: {len(df_group)}. Suma de N_FORECAST + N_LAGS: {N_FORECAST + N_LAGS}.")
    # df_group['y'] = df_group['y'].fillna(method='ffill')  # Rellenar valores faltantes con el valor anterior

    # Agregar ruido si todos los valores de 'y' son iguales
    df_group = agregar_ruido_si_igual(df_group)

    if len(df_group) < N_FORECAST + N_LAGS:
        print("Error: No hay suficientes datos para el modelo.")
    m = NeuralProphet(
                    n_forecasts=N_FORECAST,
                    growth=GROWTH,
                    yearly_seasonality=YEARLY_SEASONALITY,
                    weekly_seasonality=WEEKLY_SEASONALITY,
                    daily_seasonality=DAILY_SEASONALITY,
                    n_lags=N_LAGS,
                    learning_rate=LEARNING_RATE,
                    normalize=NORMALIZE,
                    epochs=EPOCHS,
                    drop_missing=True
                    )
    metrics = m.fit(df_group, freq = '1H')
    #Guardar modelo entrenado (no ejecutar)
    pkl_path = f"{script_folder}/{str(ip)}_{forecast_name}.pkl"
    print(pkl_path)
    if os.path.exists(pkl_path):
        os.remove(pkl_path)
    with open(pkl_path, "wb") as f:
        pickle.dump(m, f)

def predict(dataframe, ip_key, script_folder, forecast_name, logging, last_hours=5):
    print(f"IP analizando: {ip_key}")
    logging.info(f"IP analizando: {ip_key}")
    
    modelo_static = f"/{ip_key}_{forecast_name}.pkl"

    # Guardar el CSV inicial para revisión
    csv_initial_path = f"{script_folder}/data_inicial_{ip_key}_{forecast_name}.csv"
    dataframe.to_csv(csv_initial_path, index=False)  # Guardar el DataFrame original como CSV
    print(f"Datos iniciales guardados en: {csv_initial_path}")
    logging.info(f"Datos iniciales guardados en: {csv_initial_path}")

    df_processed = dataframe.copy()

    # Eliminar duplicados en 'ds', manteniendo el primer valor
    df_processed = df_processed.drop_duplicates(subset=['ds'], keep='first')
    
    # Cargar el modelo
    pkl_path = script_folder + modelo_static
    print(pkl_path)
    with open(pkl_path, 'rb') as f:
        m = pickle.load(f)
    m.restore_trainer()
    
    # Obtener las últimas 'last_hours' horas
    df_processed = df_processed.reset_index()[["ds", "y"]]
    ultima_fecha = df_processed['ds'].max()
    ultimas_horas = pd.date_range(end=ultima_fecha, periods=last_hours, freq='H')
    df_processed = df_processed[df_processed['ds'].isin(ultimas_horas)]

    # Si no hay suficientes horas, rellenar con la primera hora disponible
    if len(df_processed) < last_hours:
        missing_hours = last_hours - len(df_processed)
        first_row = df_processed.loc[df_processed['ds'].idxmin()].copy()  # 🔹 Obtener la fila con la fecha más temprana
        
        new_rows = []
        for i in range(missing_hours):
            new_row = first_row.copy()
            new_row['ds'] = new_row['ds'] - pd.Timedelta(hours=i+1)  # 🔹 Restar de 1 en 1 las horas faltantes
            new_rows.append(new_row)
        
        df_processed = pd.concat([pd.DataFrame(new_rows), df_processed], ignore_index=True)

        # 🔹 Ordenar el DataFrame por fecha después de agregar las nuevas filas
        df_processed = df_processed.sort_values(by='ds').reset_index(drop=True)

    # Verificar si la cantidad de horas es suficiente
    comprobacion_horas = df_processed['ds'].to_list()
    print(f"Últimas horas: {comprobacion_horas}")
    logging.info(f"Últimas horas: {comprobacion_horas}")
    if len(comprobacion_horas) != last_hours:
        print(f"Error en la IP {ip_key}, no hay suficientes horas. Se encontraron {len(comprobacion_horas)} horas, se esperaban {last_hours}.")
        logging.warning(f"Error en la IP {ip_key}, no hay suficientes horas. Se encontraron {len(comprobacion_horas)} horas, se esperaban {last_hours}.")
        return None

    # Generar predicciones
    future = m.make_future_dataframe(df_processed)
    print(f"future: {future}")
    logging.info(f"future: {future}")
    
    forecast = m.predict(future, decompose=False)
    print(f"forecast: {forecast}")
    logging.info(f"forecast: {forecast}")
    
    # Obtener el primer valor válido de la predicción
    pdc = float(forecast["yhat3"].loc[forecast["yhat3"].first_valid_index()])
    datte = str(forecast["ds"].loc[forecast["yhat3"].first_valid_index()])
    
    # Mostrar valores y detalles
    print(datte)
    print(f"Predicción: {pdc}")

    # Preparar los detalles de la predicción
    q = {}
    q['ip'] = ip_key
    q['fecha'] = str(datetime.now())
    oid = ""
    CodeName = None
    nodo = "ap"
    q["fecha_prediccion"] = datte
    
    if forecast_name == "SNR_V":
        q["tipo_prediccion"] = "Predict SNR V"
        q["detalles"] = {"mensaje": f"Prediccion SNR V - {datte} - {ip_key}: {pdc}"}
    elif forecast_name == "SNR_H":
        q["tipo_prediccion"] = "Predict SNR H"
        q["detalles"] = {"mensaje": f"Prediccion SNR H - {datte} - {ip_key}: {pdc}"}
    elif forecast_name == "RX":
        q["tipo_prediccion"] = "Predict RX"
        q["detalles"] = {"mensaje": f"Prediccion Link Radio RX - {datte} - {ip_key}: {pdc}"}
    else:
        logging.warning(f"No se ha especificado un tipo de forecast en el IP {ip_key}")
        print(f"No se ha especificado un tipo de forecast en el IP {ip_key}")
        return {}
    
    q["value"] = round(pdc, ndigits=2)

    return q


def predict_air_rx(dataframe, ip_key, script_folder, forecast_name, logging, last_hours):
    print(f"IP analizando: {ip_key}")
    logging.info(f"IP analizando: {ip_key}")
    
    modelo_static = f"/{ip_key}_{forecast_name}.pkl"
    df_grouped = dataframe.get_group(ip_key)
    df_grouped.rename(columns={"Timestamp": "ds", "Lat": "y"}, inplace=True)
    df_processed = df_grouped[["ds", 'y']]
    df_processed['ds'] = df_processed['ds'].apply(lambda x: x.to_pydatetime().replace(second=0, microsecond=0))
    df_processed = df_processed.sort_values(by=['ds'])
    
    pkl_path = script_folder + modelo_static
    print(pkl_path)
    with open(pkl_path, 'rb') as f:
        m = pickle.load(f)
    m.restore_trainer()

    # Obtención de las últimas `last_hours` horas
    df_processed = df_processed.reset_index()[["ds", "y"]]
    ultima_fecha = df_processed['ds'].max()
    ultimas_horas = pd.date_range(end=ultima_fecha, periods=last_hours, freq='H')
    
    # Comprobar si faltan horas y repetir el primer valor si es necesario
    if len(df_processed) < last_hours:
        missing_hours = last_hours - len(df_processed)
        first_value = df_processed.iloc[0]
        # Rellenamos con la primera hora faltante, pero retrasando una hora en cada copia
        for _ in range(missing_hours):
            print(f"Repetir valor: {first_value}")
            first_value['ds'] = first_value['ds'] - pd.Timedelta(hours=1)
            print(f"Valor repetido: {first_value} modificada")
            repeated_values = pd.DataFrame([first_value] * missing_hours, columns=df_processed.columns)
            df_processed = pd.concat([repeated_values, df_processed], ignore_index=True)

    df_processed = df_processed[df_processed['ds'].isin(ultimas_horas)]
    
    # Verificación de que haya suficientes horas
    comprobacion_horas = df_processed['ds'].to_list()
    print(f"Últimas horas: {comprobacion_horas}")
    logging.info(f"Últimas horas: {comprobacion_horas}")
    
    # Ajuste de las predicciones, ya no es necesario verificar si faltan horas
    future = m.make_future_dataframe(df_processed)
    print("future es:")
    print(future)
    print(future.shape)
    logging.info(f"future es: \n {future}")
    
    forecast = m.predict(future, decompose=False)
    print("forecast es:")
    print(forecast)
    logging.info(f"forecast es: \n {forecast}")
    
    pdc = forecast["yhat3"].loc[forecast["yhat3"].first_valid_index()]
    datte = forecast["ds"].loc[forecast["yhat3"].first_valid_index()]
    print(datte)
    print(forecast["yhat3"][forecast["yhat3"].first_valid_index()])

    fecha_ejecucion = datetime.now()
    split_key = ip_key.split("_")
    host = split_key[0]
    oid = split_key[1]
    CodeName = split_key[2]
    nodo = "ap"
    fecha_predicción = datte.strftime('%Y-%m-%d %H:%M:%S')
    tipo_prediccion = f"Predict {forecast_name}"
    value = str(pdc)
    detalle = f"Predicción {forecast_name} - {host}_{oid}_{CodeName} - {datte}: {pdc}"

    q = [None, fecha_ejecucion, host, oid, CodeName, nodo, fecha_predicción, tipo_prediccion, value, detalle]
    return q



def forecast_setting(forecast_type, script_folder):
    if forecast_type == 'V':
        forecast_name = "SNR_V"
        model_folder = f"{script_folder}/ModelsV"
    elif forecast_type == 'H':
        forecast_name = "SNR_H"
        model_folder = f"{script_folder}/ModelsH"
    elif forecast_type == 'RX':
        forecast_name = "RX"
        model_folder = f"{script_folder}/3H"
    elif forecast_type == 'AirRx':
        forecast_name = "AirRx"
        model_folder = f"{script_folder}/AirRx"
    else:
        forecast_name = None
        model_folder = None
    return forecast_name, model_folder


# Función para parsear fecha con o sin "T"
def parse_datetime(date_str: str) -> datetime:
    """Parsea una fecha en formato con espacio o con 'T'."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha inválido: {date_str}")

# Función para asegurar formato ISO con "T"
def parse_iso_string(date_str: str) -> str:
    """Convierte cualquier fecha al formato ISO con 'T'."""
    return parse_datetime(date_str).strftime("%Y-%m-%dT%H:%M:%S")

def get_prediction_column(forecast_name: str) -> str:
    if forecast_name == "SNR_V":
        return "snr_v"
    elif forecast_name == "SNR_H":
        return "snr_h"
    elif forecast_name == "RX":
        return "rx"
    else:
        raise ValueError(f"Unknown forecast type: {forecast_name}")
    

def extract_value(column, key):
    """ Extrae un valor de un JSON o string JSON, promediando si es una lista. """
    if pd.isna(column):  # Si es NaN, devolver None
        return None
    try:
        # Si es un string, intenta cargarlo como JSON
        if isinstance(column, str):
            column = json.loads(column)

        # Si es un diccionario, intenta obtener la clave deseada
        if isinstance(column, dict):
            value = column.get(key, None)

            # Si el valor es una lista, calcular el promedio
            if isinstance(value, list) and len(value) > 0:
                return sum(value) / len(value)
            
            return value  # Retornar el valor si es un número
        else:
            return None  # Si no es diccionario, devolver None
    except (json.JSONDecodeError, TypeError, ValueError):
        return None  # Si hay error al parsear, devolver None