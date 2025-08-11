from smartlink.error_utils import RAJANT_SESSION_FAILED, RAJANT_QUERY_INVALID
from bcutilshcg import bcsession
from datetime import datetime as dt
import bcapihcg
import time

_PASSWORDS = {
    "co"    : "breadcrumb-co",
    "admin" : "breadcrumb-admin",
    "view"  : "breadcrumb-view"
}

_ROLES = {
    'co'    : bcsession.SESSION_ROLE_CO,
    'admin' : bcsession.SESSION_ROLE_ADMIN,
    'view'  : bcsession.SESSION_ROLE_VIEW
}

def get_amplifiers(model, state):
    amplifier = {}
    for interface in state.wireless:
        model_wireless = None
        for mw in model.wireless:
            if mw.name == interface.name:
                model_wireless = mw
                break
        if model_wireless is not None:
            for rw in model.radiodb:
                if rw.model == model_wireless.model:
                    amplifier[interface.name] = rw.amplifier
    return amplifier


class iperf3_broker():
    _session            = None
    _OFFSET_TIME_SCAN   = 10
    _SLEEP_TIME_RESULT  = 10

    def __init__(self, ip_cliente, role : str = "admin", timeout : int = 1, debug_mode : bool = False):
        self._client    = ip_cliente
        self._timeout   = timeout
        self._debug     = debug_mode
        valid_role      = role if role in _ROLES and role in _PASSWORDS else "view"
        if self._debug and valid_role != role:
            print(f"⚠️ Rol '{role}' no válido. Usando 'view' por defecto.")
        self._role      = _ROLES[valid_role]
        self._passw     = _PASSWORDS[valid_role]
        self._int_time  = time.time()

    def _get_session(self):
        if self._session is not None:
            return self._session
        else:
            try:
                self._session = bcsession.BcSession()
                self._session.start(
                    self._client,
                    port        = 2300,
                    role        = self._role,
                    passphrase  = self._passw,
                    timeout     = self._timeout,
                )
                if self._debug:
                    print(f"Sesion {self._client} iniciada correctamente")

            except Exception as e:
                self._session = None
                if self._debug:
                    print(f"♦ Rajant session: |{self._client}|{self._role}|{self._passw}|{self._timeout}\n -> -> Error = {e}")
                    
            finally:
                return self._session


    def _destroy_session(self):
        if self._session is not None:
            try:
                self._session.stop()
            except Exception:
                pass
            finally:
                self._session = None


    def _request_format_iperf3(self, id_server : str, time_duration : int):
        try:
            if not id_server:
                raise ValueError("ID del servidor no puede estar vacío")

            if time_duration <= 0:
                raise ValueError("La duración debe ser mayor a 0")

            # Construir comando iperf3
            iperf3_time = min(60, time_duration)
            if self._debug and time_duration > 60:
                print("⚠️  Duración máxima para iperf3 es 60 segundos. Se limitará automáticamente.")

            task_cmd = bcapihcg.Common_pb2.TaskCommand()
            task_cmd.action = bcapihcg.Common_pb2.TaskCommand.TaskAction.IPERF3

            iperf3_cmd = task_cmd.iperf3
            iperf3_cmd.server = id_server
            iperf3_cmd.testMode = bcapihcg.Common_pb2.TaskCommand.Iperf3.TestMode.TCP
            iperf3_cmd.time = iperf3_time
            iperf3_cmd.reverse = False

            request = bcapihcg.Message_pb2.BCMessage()
            request.runTask.CopyFrom(task_cmd)

            return request

        except Exception as e:
            print(f"↓ Error en _request_format_iperf3(): {e}")
            return None


    def start_test_iperf3(self, ip_server_target : str = None, duration_time : int = 15) -> list:
        fecha_resultado = dt.now().replace(microsecond=0).isoformat(sep=' ')
        data_result_iperf3 = [self._client, ip_server_target, "-", "-", "-", "-", "-", fecha_resultado]

        try:
            if self._debug:
                print(f"-> {self._client} -> {ip_server_target} : Started.")
            session = self._get_session()
            if not session:
                raise RuntimeError("Unable to start BreadCrumb session")

            iperf3_request = self._request_format_iperf3(ip_server_target, duration_time)
            if not iperf3_request:
                raise ValueError("No se pudo crear el mensaje de testing IPERF3")

            # Enviar solicitud de test
            session.sendmsg(iperf3_request)
            response = session.recvmsg()
            result = response.runTaskResult

            if result.status != bcapihcg.Message_pb2.BCMessage.Result.SUCCESS:
                raise RuntimeError("IPERF3 Performance Failed")

            # Esperar a que el test finalice
            if self._debug:
                print(f"-> {self._client} -> {ip_server_target} : Ejecutando test_iperf3 / {duration_time}s ...")
            wait_time = min(60, duration_time) + self._OFFSET_TIME_SCAN
            time.sleep(wait_time)

            if self._debug:
                print(f"-> {self._client} -> {ip_server_target} : Solicitando resultados")

            # Solicitar resultados del test
            output_request = bcapihcg.Common_pb2.TaskOutputRequest(id=result.id)
            result_request = bcapihcg.Message_pb2.BCMessage(taskOutputRequest=output_request)

            session.sendmsg(result_request)
            response = session.recvmsg()

            if response.taskOutputResponse.status != bcapihcg.Message_pb2.BCMessage.Result.SUCCESS:
                raise RuntimeError("Error al recibir resultado del IPERF3 | Rajant")

            result_data = response.taskOutputResponse.data
            parsed_result = bcapihcg.Common_pb2.Iperf3Result()
            parsed_result.ParseFromString(result_data)
            # Parsear resultados
            data_result_iperf3 = [
                parsed_result.sender,                                       # 0    
                parsed_result.receiver,                                     # 1
                round(parsed_result.latency, 3),                            # 2
                round(parsed_result.sendresults.bps / 1_000_000, 3),        # 3
                parsed_result.sendresults.coreUtilization,                  # 4
                round(parsed_result.receiveresults.bps / 1_000_000, 3),     # 5
                parsed_result.receiveresults.coreUtilization,               # 6
                fecha_resultado                                             # 7
            ]
            if self._debug:
                print(f"-> {self._client} -> {ip_server_target} : Finalizado. Esperando {self._SLEEP_TIME_RESULT} para continuar")
            
            # Tiempo de espera entre pruebas
            time.sleep(self._SLEEP_TIME_RESULT)

        except Exception as e:
            if self._debug:
                print(f" ✘ Error server = {ip_server_target} con cliente = {self._client}:\n{e} ")

        finally:
            if self._session:
                self._destroy_session()

            if self._debug:
                print(f"-> . . . \n")

            return data_result_iperf3



class InterfaceStats(object):
    _METRIC_INTERFACE   = 0
    _METRIC_INSTAMESH   = 1
    _METRIC_PEERS       = 2
    _METRIC_SYSTEM      = 3

    _target             = None      #: target IP of breadcrumb to connect to
    _port               = 2300      #: target port of breadcrumb to connect to
    _role               = None      #: the breadcrumb auth role being used
    _passphrase         = None      #: the passphrase for the auth role
    _session            = None      #: the bcapi session
    _session_timeout    = 1.0       #: the socket timeout to use for the bcapi session
    _model              = None      #: the bcapi provided model info of the connected breadcrumb
    _amplifier          = {}        #: A dictionary of amplifier levels by interface

    _first_poll         = True
    _last_polls         = {}


    def __init__(self):
        # read bcutils auth db for the crumb
        auth_db             = _PASSWORDS.copy()
        self._role          = bcsession.SESSION_ROLE_VIEW
        role_string         = 'view'
        self._passphrase    = auth_db.get(role_string)


    def _create_session(self, _debug = False):
        session = bcsession.BcSession()
        if _debug:
            print(f"Rajant session: |{self._target}|{self._role}|{self._passphrase}|{self._session_timeout}\n")
        session.start(
            self._target,
            port        = self._port,
            role        = self._role,
            passphrase  = self._passphrase,
            timeout     = self._session_timeout,
        )
        return session


    def destroy_session(self):
        if self._session is not None:
            try:
                self._session.stop()
            except Exception:
                pass
            finally:
                self._session = None


    def get_session(self, _debug = False):
        if self._session is not None:
            return self._session
        else:
            try:
                self._session = self._create_session(_debug)

                # fetch model and build map of interface amplifiers
                m = bcapihcg.Message_pb2.BCMessage()
                m.state.CopyFrom(bcapihcg.State_pb2.State())
                m.model.CopyFrom(bcapihcg.ModelDatabase_pb2.BcModel())
                self._session.sendmsg(m)
                bcmsg = self._session.recvmsg()
                self._model = bcmsg.model
                self._amplifier = get_amplifiers(self._model, bcmsg.state)

            except Exception:
                if _debug:
                    print(f"No se puedo conectar a la ip = {self._target}")
                self._session = None
                time.sleep(1)

            finally:
                return self._session


    def _printstate(self, debug_mode = False):
        session = None
        try:
            # get state from the crumb
            m = bcapihcg.Message_pb2.BCMessage()
            m.state.CopyFrom(bcapihcg.State_pb2.State())

            # no session means we can't send anything
            session = self.get_session(debug_mode)
            if session is None:
                _error_msg = f"{RAJANT_SESSION_FAILED[0]}|{RAJANT_SESSION_FAILED[1]}|Error al tratar de establecer una session"
                raise RuntimeError(_error_msg)

            session.sendmsg(m)
            state= session.recvmsg().state
            self.destroy_session()
            return state
        
        except Exception as e:
            if session:
                self.destroy_session()
            if RAJANT_SESSION_FAILED[0] in str(e):
                raise
            _error_msg = f"{RAJANT_QUERY_INVALID[0]}|{RAJANT_QUERY_INVALID[1]}|No se pudo comunicar con BreadCrumb: {str(e)}"
            raise RuntimeError(_error_msg) from e


def getRajantData(ipv4  : str, 
                  user  : str = None, 
                  passw : str = None, 
                  role  : str = None,  # Nuevo parámetro role
                  timeout: int = 5, 
                  debug_mode: bool = False
                  ):
    # Si se pasa un rol, extraer el usuario y contraseña correspondientes
    if role:
        if role not in _ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {', '.join(_ROLES.keys())}.")
        user    = _ROLES[role]
        passw   = _PASSWORDS.get(role, None)
        if passw is None:
            raise ValueError(f"No password found for role: {role}.")
    
    # Si no se pasa un rol, se debe proporcionar tanto usuario como contraseña
    elif user is None or passw is None:
        raise ValueError("If no role is provided, both 'user' and 'passw' must be specified.")
    
    if passw is None:
        raise ValueError("No hay una contraseña establecida")

    try:
        session_interface = InterfaceStats()
        session_interface._role = user
        session_interface._passphrase = passw
        session_interface._target = ipv4
        session_interface._session_timeout = timeout
        return session_interface._printstate(debug_mode)
    except Exception as e:
        raise e
        

if __name__ == "__main__":
    ip_rajant   = "192.168.2.122"
    DEFAULT_ROL = "view"
    _DEBUG_MODE = False
    data_rajant = getRajantData(ipv4    = ip_rajant, 
                                user    = _ROLES[DEFAULT_ROL], 
                                passw   = _PASSWORDS[DEFAULT_ROL],
                                timeout = 5, 
                                debug_mode = _DEBUG_MODE)
    
    
    print(data_rajant)



