from fastapi                    import APIRouter, HTTPException, Depends
from connection                 import get_db_connection
from routes.__utils__           import insert_data, insert_bulk_data, fetch_data
from models.inventario_models   import Inventario
from mariadb                    import IntegrityError

router = APIRouter()

''' Se comenta para evitar que se puedan agregar equipos desde afuera
@router.post("/add")
async def add_inventory(inventario: Inventario, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return await insert_data(conn, "inventario", inventario)
'''

@router.post("/add_list")
async def add_inventory_list(list_model: list[Inventario], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "inventario", list_model, Inventario.model_fields.keys())

@router.get("/get")
async def get_inventory(conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data(conn, "inventario")

@router.get("/get/{column}/{filter_value}")
async def get_inventory_by_column(
    column: str, 
    filter_value: str, 
    conn_dep=Depends(get_db_connection)
):
    """
    Obtiene registros de la tabla `inventario` filtrando por una columna específica.
    """
    async with conn_dep as conn:
        try:
            if column not in Inventario.model_fields:
                raise HTTPException(status_code=400, detail="Invalid column name")

            field_type = Inventario.model_fields[column].annotation  

            if field_type == int:
                try:
                    filter_value_int = int(filter_value)
                    query = f"SELECT * FROM inventario WHERE {column} = ?"
                    query_params = (filter_value_int,)
                except ValueError:
                    raise HTTPException(status_code=400, detail="For integer columns, provide an integer value")
            else:
                query = f"SELECT * FROM inventario WHERE {column} LIKE ?"
                query_params = (f"%{filter_value}%",)

            cursor = conn.cursor()
            cursor.execute(query, query_params)
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(column_names, row)) for row in rows]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.delete("/delete/{ip}")
async def delete_inventory(ip: str, conn_dep=Depends(get_db_connection)):
    """
    Elimina un registro del inventario basado en la IP.
    """
    async with conn_dep as conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventario WHERE ip = ?", (ip,))
            conn.commit()
            return {"message": "Deleted successfully"}

        except IntegrityError as e:
            raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/update/{columna}/{valor_anterior}/{valor_nuevo}")
async def update_inventory(
    columna: str, 
    valor_anterior: str, 
    valor_nuevo: str, 
    conn_dep=Depends(get_db_connection)
):
    """
    Actualiza registros en la tabla `inventario` cambiando `valor_anterior` por `valor_nuevo` en una columna específica.
    """
    if columna not in Inventario.model_fields:
        raise HTTPException(status_code=400, detail="Invalid column name")

    async with conn_dep as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE inventario SET {columna} = ? WHERE {columna} = ?", 
                (valor_nuevo, valor_anterior)
            )
            conn.commit()
            return {"message": "Updated successfully"}

        except IntegrityError as e:
            raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

