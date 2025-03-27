from datetime import datetime, timedelta
import sys
import pandas as pd
import os
import warnings
import yaml
import argparse
import pytz
from urllib.parse import urljoin

warnings.filterwarnings("ignore")

from IA.ia_utils import api_request
from IA.forecast_neuralprophet.forecast_utils import *

now = datetime.now()
seven_days_ago = now - timedelta(days=1)

parser = argparse.ArgumentParser(description="Script para construir modelos de NeuralProphet.")
parser.add_argument('--forecast', type=str, default=None, 
                    help='Indica qué modelo de forecast se desea crear (V, H, RX o AirRx)')
parser.add_argument('--from_date', type=str, default=seven_days_ago.strftime("%Y-%m-%d %H:%M:%S"), 
                    help='Fecha de inicio en formato YYYY-MM-DD HH:MM:SS o YYYY-MM-DDTHH:MM:SS. Por defecto es 1 día atrás.')
parser.add_argument('--to_date', type=str, default=now.strftime("%Y-%m-%d %H:%M:%S"), 
                    help='Fecha de fin en formato YYYY-MM-DD HH:MM:SS o YYYY-MM-DDTHH:MM:SS. Por defecto es hoy.')
parser.add_argument('--zone', type=str, default=None, help='Zona horaria (opcional).')
parser.add_argument('--limit', type=int, default=20000, help='Número máximo de registros.')
parser.add_argument('--offset', type=int, default=0, help='Offset en la consulta.')
args = parser.parse_args()


if args.forecast is not None and args.forecast not in ['H', 'V', 'RX']:
    print(f"No se ingreso Forecast valido '{args.forecast}'. No es 'V', 'H', 'RX'.")
    sys.exit(1)

forecast_types = [args.forecast] if args.forecast else ['H', 'V', 'RX']
from_date = parse_iso_string(args.from_date)
to_date = parse_iso_string(args.to_date)
zone = args.zone
limit = args.limit
offset = args.offset
from_date_dt = parse_datetime(from_date)
to_date_dt = parse_datetime(to_date)

if zone is not None:
    try:
        timezone = pytz.timezone(zone)
        from_date_dt = from_date_dt.astimezone(timezone)
        to_date_dt = to_date_dt.astimezone(timezone)
        from_date = from_date_dt.strftime("%Y-%m-%dT%H:%M:%S")
        to_date = to_date_dt.strftime("%Y-%m-%dT%H:%M:%S")
    except pytz.UnknownTimeZoneError:
        print(f"Zona horaria desconocida: {zone}")
        sys.exit(1)

print(f"Periodo de los datos: {from_date} - {to_date}")

for forecast_type in forecast_types:
    print(f"\n=== Procesando forecast: {forecast_type} ===")

    forecast_name, model_folder = forecast_setting(forecast_type, script_folder)
    if not forecast_name or not model_folder:
        print(f"Error al configurar el forecast. {forecast_type}")
        continue

    if not os.path.exists(model_folder):
        os.makedirs(model_folder)
        print(f'Carpeta "{model_folder}" creada.')

    with open(f'{script_folder}/configForecast.yml', 'r') as file:
        config = yaml.safe_load(file)

    N_FORECAST = config[forecast_name]['neuralprophet_parameters']['n_forecasts']
    GROWTH = config[forecast_name]['neuralprophet_parameters']['growth']
    YEARLY_SEASONALITY = config[forecast_name]['neuralprophet_parameters']['yearly_seasonality']
    WEEKLY_SEASONALITY = config[forecast_name]['neuralprophet_parameters']['weekly_seasonality']
    DAILY_SEASONALITY = config[forecast_name]['neuralprophet_parameters']['daily_seasonality']
    N_LAGS = config[forecast_name]['neuralprophet_parameters']['n_lags']
    NUM_HIDDEN_LAYERS = config[forecast_name]['neuralprophet_parameters'].get('num_hidden_layers', 1)
    D_HIDDEN = config[forecast_name]['neuralprophet_parameters'].get('d_hidden', 64)
    LEARNING_RATE = config[forecast_name]['neuralprophet_parameters']['learning_rate']
    OPTIMIZER = config[forecast_name]['neuralprophet_parameters'].get('optimizer', 'AdamW')
    AR_REG = config[forecast_name]['neuralprophet_parameters'].get('ar_reg', 0.0)
    NORMALIZE = config[forecast_name]['neuralprophet_parameters']['normalize']
    EPOCHS = config[forecast_name]['neuralprophet_parameters']['epochs']
    DROP_MISSING = config[forecast_name]['neuralprophet_parameters'].get('drop_missing', False)

    DB_API_URL = config["db_api_url"]
    INVENTORY_PMP_URL = urljoin(DB_API_URL, config["inventario_pmp_url"])
    CAMBIUM_DATA_IP_URL_BASE = urljoin(DB_API_URL, config["cambium_data_ip_url_base"])

    pmp_files = api_request(url=INVENTORY_PMP_URL, dataframe=True)
    subscribers = pmp_files[pmp_files["tipo"].str.contains("PMP", na=False, case=False)]["ip"].unique()

    print(f"Suscriptores: {subscribers}")
    print(f"Rango de fechas para que funcione en la API: {from_date} - {to_date}")

    lstfinal = []
    for subs in subscribers:
        url = urljoin(CAMBIUM_DATA_IP_URL_BASE, f"{subs}?start_date={from_date}&end_date={to_date}&limit={limit}&offset={offset}")
        print(url)
        results = api_request(url, dataframe=False)

        if results:
            lstfinal.extend(results)

    df_raw = pd.DataFrame(lstfinal)
    if df_raw.empty:
        print("No hay datos para procesar.")
        continue

    df_raw['snr_h'] = df_raw['snr'].apply(lambda x: extract_value(x, 'H'))
    df_raw['snr_v'] = df_raw['snr'].apply(lambda x: extract_value(x, 'V'))
    df_raw['rx'] = df_raw['link_radio'].apply(lambda x: extract_value(x, 'rx'))

    prediction_column = get_prediction_column(forecast_name)

    df = df_raw[['fecha', 'ip', prediction_column]]
    df = df.rename(columns={'fecha': 'ds', prediction_column: 'y'})

    df['ds'] = pd.to_datetime(df['ds'])
    df['ds'] = df['ds'].apply(lambda x: x.replace(second=0, microsecond=0))
    df['ds'] = df['ds'].dt.round('15min')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')

    if df['y'].isna().sum() > 0:
        print(f"Advertencia: {df['y'].isna().sum()} valores no convertibles a numérico. Se imputarán con la media.")
        df['y'] = df['y'].fillna(df['y'].mean())

    df.to_csv(f"{model_folder}/df_query_{forecast_name}.csv", index=False)

    df_group = df.groupby('ip')

    for ip in df_group.groups.keys():
        print("Procesando IP:", ip)
        try:
            create_model(
                df_group, ip, model_folder, 
                N_FORECAST, GROWTH, YEARLY_SEASONALITY, 
                WEEKLY_SEASONALITY, DAILY_SEASONALITY, 
                N_LAGS, LEARNING_RATE, NORMALIZE, EPOCHS, forecast_name
            )
        except Exception as e:
            print(f"Error con IP {ip}: {e}")
