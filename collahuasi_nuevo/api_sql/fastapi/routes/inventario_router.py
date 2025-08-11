
from fastapi                    import APIRouter, HTTPException
from connection                 import get_db_connection
from routes.__utils__           import insert_data, insert_bulk_data, fetch_data
from models.inventario_models   import Inventario
from mariadb                    import IntegrityError

router = APIRouter()

'''                     Se comenta para evitar que se puedan agregar equipos desde afuera
@router.post("/add")
def add_inventory(inventario: Inventario):
    return insert_data("inventario", inventario)
'''

@router.post("/add_list")
def add_inventory_list(list_model: list[Inventario]):
    return insert_bulk_data("inventario", list_model, Inventario.model_fields.keys())


@router.get("/get")
def get_inventory():
    return fetch_data("inventario")

# Generic endpoint to filter based on column and value
@router.get("/get/{column}/{filter_value}")
def get_inventory_by_column(column: str, filter_value: str):
    try:
        if column not in Inventario.model_fields:
            raise HTTPException(status_code=400, detail="Invalid column name")

        # Get the type of the field from the Pydantic model
        field_type = Inventario.model_fields[column].annotation  # Use `.annotation` for field type

        # Determine the filter value based on field type (int or str)
        if field_type == int:
            # Try to convert the filter_value to an integer
            try:
                filter_value_int = int(filter_value)
                query = f"SELECT * FROM inventario WHERE {column} = ?"
                query_params = (filter_value_int,)
            except ValueError:
                raise HTTPException(status_code=400, detail="For integer columns, provide an integer value")
        else:
            # Treat as string, and perform LIKE search
            query = f"SELECT * FROM inventario WHERE {column} LIKE ?"
            query_params = (f"%{filter_value}%",)  # Adding % for LIKE query

        # Execute the query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, query_params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        # Return the results as a list of dictionaries
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        conn.close()

# Ruta para eliminar
@router.delete("/delete/{ip}")
def delete_inventory(ip: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventario WHERE ip = ?", (ip,))
        conn.commit()
        return {"message": "Deleted successfully"}
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        conn.close()

# Ruta para actualizar
@router.put("/update/{columna}/{valor_anterior}/{valor_nuevo}")
def update_inventory(columna: str, valor_anterior: str, valor_nuevo: str):
    if columna not in Inventario.model_fields:
        raise HTTPException(status_code=400, detail="Invalid column name")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE inventario SET {columna} = ? WHERE {columna} = ?", (valor_nuevo, valor_anterior))
        conn.commit()
        return {"message": "Updated successfully"}
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        conn.close()
