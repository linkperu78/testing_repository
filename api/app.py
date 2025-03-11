from fastapi                        import FastAPI
from routes.routes                  import router
from routes.usuarios_router         import router as usuarios_router
from routes.eventos_router          import router as eventos_router
from routes.inventario_router       import router as inventario_router
from routes.rol_router              import router as roles_router
from routes.marcas_router           import router as marcas_router
from routes.sensores_router         import router as sensores_router
from routes.tipos_router            import router as tipos_router
from routes.estructura_red_router   import router as estructura_red_router
from routes.snmp_conf_router        import router as snmp_conf_router
from routes.ubicacion_gps_router    import router as ubicacion_gps_router
from routes.rajant_data_router      import router as rajant_data_router
from routes.latencia_router         import router as latencia_router
from routes.cambium_data_router     import router as cambium_data
from routes.instamesh_router        import router as instamesh_router
from routes.wired_router            import router as wired_router
from routes.wireless_router         import router as wireless_router
from routes.LTE_data_router         import router as LTE_data_router
from routes.servidor_router         import router as servidor_router
from routes.clustering_data_router  import router as clustering_data_router
from routes.predicciones_router     import router as predicciones_router
# from routes.websocket_lte.websocket_lte_router import router as websocket_lte_router

app = FastAPI()

# Rutas de la aplicacion Websockets
# app.include_router(websocket_lte_router, prefix="/ws", tags=["Websockets LTE"])


# Rutas de la aplicación HTTP
app.include_router(router)
app.include_router(usuarios_router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(roles_router, prefix="/roles", tags=["Roles"])
app.include_router(marcas_router, prefix="/marcas", tags=["Marcas"])
app.include_router(tipos_router, prefix="/tipos", tags=["Tipos"])
app.include_router(LTE_data_router, prefix="/LTE_data", tags=["Datos LTE"])
app.include_router(snmp_conf_router, prefix="/snmp_conf", tags=["Configuración SNMP"])
app.include_router(inventario_router, prefix="/inventario", tags=["Inventario"])
app.include_router(estructura_red_router, prefix="/estructura", tags=["Estructura de red"])
app.include_router(ubicacion_gps_router, prefix="/ubicacion_gps", tags=["Ubicación GPS"])
app.include_router(latencia_router, prefix="/latencia", tags=["Latencia"])
app.include_router(cambium_data, prefix="/cambium_data", tags=["Datos Cambium"])
app.include_router(sensores_router, prefix="/sensores", tags=["Sensores"])
app.include_router(eventos_router, prefix="/eventos", tags=["Eventos"])
app.include_router(rajant_data_router, prefix="/rajant_data", tags=["Datos Rajant"])
app.include_router(instamesh_router, prefix="/instamesh", tags=["Instamesh"])
app.include_router(wired_router, prefix="/wired", tags=["Wired"])
app.include_router(wireless_router, prefix="/wireless", tags=["Wireless"])
app.include_router(servidor_router, prefix="/servidor", tags=["Servidor"])
app.include_router(clustering_data_router, prefix="/clustering", tags=["Clustering"])
app.include_router(predicciones_router, prefix="/predicciones", tags=["Predicciones"])



# Listar todas las rutas de la aplicacion
for route in app.routes:
    if hasattr(route, 'methods'):  # Solo rutas HTTP tienen 'methods'
        print(f"{route.path} - {route.methods}")
    else:
        print(f"{route.path} - WebSocket")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
