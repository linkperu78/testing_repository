from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from connection import get_db_connection

router = APIRouter()

@router.delete("/limpiar", summary="Limpiar registros antiguos en todas las tablas que tengan columna 'fecha'")
def limpiar_base_completa(
    dias: int = Query(15, description="Eliminar registros con mas de X dias (por defecto: 14)"),
    dry_run: bool = Query(False, description="Si es True, no elimina nada, solo muestra lo que eliminaria")
):
    """
    Recorre todas las tablas de la base de datos y elimina (o simula eliminar) registros con columna 'fecha'
    que sean anteriores a la fecha calculada segun los dias indicados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cutoff = datetime.now() - timedelta(days=dias)
        cursor.execute("SHOW TABLES")
        tablas = [fila[0] for fila in cursor.fetchall()]
        
        resultado = {}

        for tabla in tablas:
            try:
                # Verifica si la tabla tiene una columna 'fecha'
                cursor.execute(f"SHOW COLUMNS FROM {tabla} LIKE 'fecha'")
                if not cursor.fetchone():
                    resultado[tabla] = "No tiene columna 'fecha', se omitio"
                    continue

                if dry_run:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE fecha < %s", (cutoff,))
                    count = cursor.fetchone()[0]
                    resultado[tabla] = f"Se eliminarian {count} registros anteriores a {cutoff.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    cursor.execute(f"DELETE FROM {tabla} WHERE fecha < %s", (cutoff,))
                    conn.commit()
                    count = cursor.rowcount
                    resultado[tabla] = f"Se eliminaron {count} registros anteriores a {cutoff.strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception as inner_e:
                resultado[tabla] = f"Error al procesar: {str(inner_e)}"

        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el mantenimiento: {str(e)}")
    finally:
        cursor.close()
        conn.close()
