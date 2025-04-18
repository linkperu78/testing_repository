from typing import Dict, Any, Optional, List, Union
from mariadb import IntegrityError
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

def round_to_nearest_15_minutes(dt):
    """Redondea un datetime al múltiplo de 15 minutos más cercano."""
    # Calcular el múltiplo más cercano de 15 minutos
    new_minute = round(dt.minute / 15) * 15

    # Si los minutos redondeados son 60, hay que ajustar la hora
    if new_minute == 60:
        new_minute = 0
        dt = dt.replace(hour=dt.hour + 1)

    return dt.replace(minute=new_minute, second=0, microsecond=0)

def insert_data(conn, table: str, model: BaseModel) -> Dict[str, str]:
    """
    Función genérica para insertar datos en una tabla desde un modelo de Pydantic.

    Args:
        table (str): Nombre de la tabla.
        model (BaseModel): Modelo de Pydantic con los datos a insertar.
        conn: Conexión a la base de datos (obtenida con Depends(get_db_connection)).

    Returns:
        Dict[str, str]: Mensaje de éxito o error.
    """
    try:
        data = model.model_dump()  # Convertir modelo a diccionario
        cursor = conn.cursor()

        # Preparar la consulta SQL
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        # Convertir valores a JSON si es necesario y manejar `null`
        values = [json.dumps(value) if isinstance(value, (dict, list)) else value for value in data.values()]

        # Ejecutar la consulta
        cursor.execute(query, values)
        conn.commit()

        return {"message": f"Datos insertados exitosamente en la tabla {table}"}
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al insertar datos en {table}: {str(e)}")


def insert_bulk_data(
    conn,
    table: str,
    data: List[BaseModel],
    columns: List[str],
):
    """
    Inserta múltiples registros en una tabla específica.

    :param table: Nombre de la tabla en la base de datos.
    :param data: Lista de modelos Pydantic con los datos a insertar.
    :param columns: Lista de nombres de columnas en la tabla.
    :param conn: Conexión de base de datos (manejada automáticamente por FastAPI).
    """

    if not data:
        raise HTTPException(status_code=400, detail="La lista de datos está vacía.")

    try:
        cursor = conn.cursor()
        placeholders = ", ".join(["?" for _ in columns])  # Genera "?, ?, ?"
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # Convertir objetos Pydantic a listas de valores
        array_data = [
            tuple(
                json.dumps(getattr(item, col)) if isinstance(getattr(item, col), (dict, list)) else getattr(item, col)
                for col in columns
            )
            for item in data
        ]

        cursor.executemany(query, array_data)
        conn.commit()

        return {"message": f"Datos insertados en {table} exitosamente", "total_registros": len(array_data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al insertar datos en {table}: {str(e)}")


def fetch_data(conn, table: str):
    """Función genérica para recuperar datos de una tabla específica."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos de {table}: {str(e)}")



def fetch_data_with_filter(
    conn,
    table: str, 
    column: str, 
    value: str, 
    operator: str = "LIKE", 
) -> List[Dict[str, Any]]:
    """
    Función genérica para realizar una consulta con un WHERE en una tabla.

    Args:
        table (str): Nombre de la tabla.
        column (str): Columna a la que se le aplicará el filtro.
        value (str): Valor para filtrar la columna.
        operator (str): Operador para la comparación, puede ser 'LIKE' o '='. Por defecto es 'LIKE'.
        conn: Conexión a la base de datos (obtenida con Depends(get_db_connection)).

    Returns:
        List[Dict[str, Any]]: Lista de resultados como diccionarios.
    """

    if operator not in ["LIKE", "="]:
        raise ValueError("El operador debe ser 'LIKE' o '='")

    try:
        cursor = conn.cursor()

        # Preparar la consulta según el operador
        if operator == "LIKE":
            query = f"SELECT * FROM {table} WHERE {column} LIKE ?"
            value = f"%{value}%"  # Para LIKE, agregamos los comodines
        else:
            query = f"SELECT * FROM {table} WHERE {column} = ?"

        cursor.execute(query, (value,))
        
        # Obtener los nombres de las columnas
        column_names = [desc[0] for desc in cursor.description]
        
        # Obtener todas las filas
        rows = cursor.fetchall()

        # Si no hay resultados, devolver una lista vacía
        return [dict(zip(column_names, row)) for row in rows] if rows else []
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos de la tabla {table}: {str(e)}")



def fetch_data_with_dates(
    conn,
    table: str, 
    start_date: Optional[str], 
    end_date: Optional[str], 
    limit: int, 
    offset: int,
    round_to_quarter_hour: Optional[bool] = False  # Parámetro opcional para redondeo
) -> List[Dict[str, Any]]:
    """Función genérica para recuperar datos con paginación y opción de redondeo de fechas."""

    try:
        cursor = conn.cursor()
        
        query = f"SELECT * FROM {table} WHERE 1=1"
        params = []

        if start_date:
            query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= %s"
            params.append(end_date)

        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        result = [dict(zip(column_names, row)) for row in rows]

        # Si se pasa el parámetro 'round_to_quarter_hour' como True, redondeamos las fechas
        if round_to_quarter_hour:
            for row in result:
                if 'fecha' in row and isinstance(row['fecha'], datetime):
                    row['fecha'] = round_to_nearest_15_minutes(row['fecha'])

        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")



def fetch_data_with_filter_and_pagination(
    conn, 
    table: str, 
    ip_column: str, 
    ip: str, 
    start_date: Optional[str], 
    end_date: Optional[str], 
    limit: int, 
    offset: int,
) -> List[Dict[str, Any]]:
    """
    Función genérica para obtener datos con filtros por IP, rango de fechas y paginación.

    Args:
        table (str): Nombre de la tabla.
        ip_column (str): Nombre de la columna de IP en la tabla.
        ip (str): Dirección IP a filtrar.
        start_date (Optional[str]): Fecha de inicio del rango.
        end_date (Optional[str]): Fecha de fin del rango.
        limit (int): Número de registros a devolver.
        offset (int): Número de registros a omitir para la paginación.
        conn: Conexión a la base de datos (obtenida con Depends(get_db_connection)).

    Returns:
        List[Dict[str, Any]]: Lista de resultados como diccionarios.
    """

    try:
        cursor = conn.cursor()

        query = f"SELECT * FROM {table} WHERE {ip_column} = %s"
        params = [ip]

        if start_date:
            query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= %s"
            params.append(end_date)

        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(column_names, row)) for row in rows] if rows else []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos de la tabla {table}: {str(e)}")


def fetch_data_with_single_filter_and_datetime(
    conn, 
    table: str,
    filter_column: str,
    filter_operator: str,
    filter_value: Union[str, int, float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Obtiene datos filtrados por una sola columna, con rango de fechas opcional y paginación.

    Args:
        table (str): Nombre de la tabla.
        filter_column (str): Columna para filtrar.
        filter_operator (str): Operador de comparación (Ej: "=", ">", "<", "LIKE").
        filter_value (Union[str, int, float]): Valor para filtrar.
        start_date (Optional[str]): Fecha de inicio (opcional).
        end_date (Optional[str]): Fecha de fin (opcional).
        limit (int): Número máximo de registros.
        offset (int): Desplazamiento para paginación.
        conn: Conexión a la base de datos (obtenida con Depends(get_db_connection)).

    Returns:
        List[Dict[str, Any]]: Lista de resultados.
    """

    if filter_operator not in ["=", ">", "<", ">=", "<=", "LIKE"]:
        raise ValueError("Operador inválido. Debe ser '=', '>', '<', '>=', '<=', o 'LIKE'.")

    try:
        cursor = conn.cursor()

        query = f"SELECT * FROM {table} WHERE {filter_column} {filter_operator} %s"
        params = [filter_value]

        if start_date:
            query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= %s"
            params.append(end_date)

        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(column_names, row)) for row in rows] if rows else []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos de {table}: {str(e)}")
