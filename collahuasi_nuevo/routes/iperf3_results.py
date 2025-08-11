from fastapi    import APIRouter, Query, Path
from datetime   import datetime
from typing     import Optional
from typing     import List

#from models.rajant_performance_model import rajant_performance
from models.rajant_performance_model import rajant_performance
from routes.__utils__ import fetch_data_with_dates, fetch_data_with_filter_and_pagination, insert_data, insert_bulk_data

router = APIRouter()

@router.post("/add")
def add_latencia(single_model: rajant_performance):
    return insert_data("rajant_performance", single_model)


@router.post("/add_list")
def add_latencia_list(list_model: List[rajant_performance]):
    return insert_bulk_data("rajant_performance", list_model, rajant_performance.model_fields.keys())


@router.get("/get", summary="Obtener datos de latencia de la base de datos por rangos de tiempo y con paginación")
def get_latencia(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
    round_dates: Optional[bool] = Query(False, description="Redondear la fecha a la hora más cercana")
):
    return fetch_data_with_dates("rajant_performance", start_date, end_date, limit, offset, round_dates)
        

@router.get("/get_ip/{ip}", summary="Obtener datos de latencia de la base de datos por IP, por rangos de tiempo y con paginación")
def get_latencia_by_ip(
    ip: str = Path(..., description="Dirección IP de la latencia"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    return fetch_data_with_filter_and_pagination("rajant_performance", "ip", ip, start_date, end_date, limit, offset)