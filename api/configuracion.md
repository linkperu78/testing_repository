# Configuración de la API en un Servidor con Acceso desde una VPN

Esta guía detalla los pasos para configurar una API basada en FastAPI y Uvicorn en un servidor Linux, ejecutándola como un servicio de sistema para mantenerla activa y accesible desde otros dispositivos conectados a la VPN.

---

## Prerrequisitos
- Acceso al servidor Linux con privilegios de superusuario.
- Instalación de Python 3.
- Acceso a una red VPN.

---

### Paso 1: Configuración de la API como un Servicio de Sistema

1. **Crear un archivo de servicio para systemd:**
   
   Ejecuta el siguiente comando para crear un archivo de configuración:
   
   ```bash
   sudo nano /etc/systemd/system/smartlink_api.service
   ```

2. **Definir el contenido del archivo de servicio:**

   Copia y pega el siguiente contenido:

   ```ini
   [Unit]
   Description=SmartLink API Service
   After=network.target

   [Service]
   User=allpa
   Group=backend
   #### CODIGO ANTIGUO
   # WorkingDirectory=/etc/pythonsmartlink
   # ExecStart=/etc/pythonsmartlink/run_api.sh
   #### CODIGO ANTIGUO
   WorkingDirectory=/usr/smartlink/api_sql/fastapi
   ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   # Tambien es valido (y mejor en producción) usar este ExecStart
   ## ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 10
   Restart=always
   Environment=PATH=/etc/pythonsmartlink/my_env/bin:$PATH
   Environment=VIRTUAL_ENV=/etc/pythonsmartlink/my_env

   [Install]
   WantedBy=multi-user.target
   ```

   Ajusta las rutas y el usuario según sea necesario.

3. **Recargar los servicios de systemd:**

   ```bash
   sudo systemctl daemon-reload
   ```

4. **Habilitar y comenzar el servicio:**

   ```bash
   sudo systemctl enable smartlink_api.service
   sudo systemctl start smartlink_api.service
   ```

5. **Verificar el estado del servicio y o detener el servicio:**
   Para revisar el estado del servidor ante cualquier fallo:
   ```bash
   sudo systemctl status smartlink_api.service
   ```

   Para detener el servidor:
   ```bash
   sudo systemctl stop smartlink_api.service
   ```

---

### Paso 2: Configurar las Reglas de Firewall

Asegúrate de que el puerto 8000 esté abierto para las conexiones desde la VPN.

1. **Revisar las reglas actuales:**

   ```bash
   sudo ufw status
   ```

2. **Permitir el puerto 8000:**

   ```bash
   sudo ufw allow 8000
   ```

**Nota**: Si no esta instalado ufw:

1. **Ver las reglas actuales de iptables:**

   ```bash
   sudo iptables -L -n -v
   ```
2. **Permitir el tráfico en el puerto 8000:**

   ```bash
   sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
   ```

3. **Guardar las reglas para que persistan después de reiniciar, En distribuciones modernas:**

   ```bash
   sudo apt install iptables-persistent
   sudo netfilter-persistent save
   sudo netfilter-persistent reload
   ```

### Paso 3: Verificar la Dirección IP del Servidor 

Utiliza el siguiente comando para encontrar la dirección IP:

```bash
ip a
```

Busca la dirección IP asociada a la interfaz de red activa (como `eth0`, `ens33` o similar).

---


### Paso 4: Acceso a la API desde una PC Conectada a la VPN

1. Asegúrate de que el dispositivo cliente esté conectado a la misma VPN que el servidor.
2. Abre un navegador web o utiliza una herramienta como `curl` o Postman para acceder a la API.
3. Usa la siguiente URL:

   ```
   http://<ip_del_servidor>:8000
   ```

   Reemplaza `<ip_del_servidor>` con la dirección IP obtenida en el paso 2.

---

### Paso 5: Solución de Problemas

- **Ver puertos abiertos:**

  ```bash
  sudo ss -tulnp
  ```

  Asegúrate de que el puerto `8000` esté en uso por Uvicorn.

- **Revisar logs del servicio:**

  ```bash
  sudo journalctl -u smartlink_api.service -n 20
  ```

- **Revisar logs del servicio en tiempo real:**
   ```bash
   sudo journalctl -u smartlink_api.service -f
   ```

- **Verificar conectividad desde el cliente:**

  ```bash
  ping <ip_del_servidor>
  ```

---

Esta configuración permite mantener la API activa y accesible mientras la conexión a la VPN esté establecida.

## Lista de todas las rutas

http://<ip_del_servidor>:8000/docs

FastAPI trae por defecto una documentación de las rutas que se desarrollen (y una plataforma rápida para probarlas) utilizando Swagger, el cual se configura automáticamente.

## Observaciones para cuando este en produccion
- Con --reload permite dejar ejecutar el servidor una vez, para luego poder editar los archivos al agregar nuevas rutas y que este al guardarlo recargue automaticamente. Pero para cambios grandes se recomienda cerrar y prender el daemon asociado a la API.
- Esta guía esta pensada para http, pero en el futuro se recomienda para mayor seguridad subirlo como https.
- Idealmente esto debe tener un servername
