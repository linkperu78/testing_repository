#!/usr/bin/python3
# coding=utf-8

'''
hcgscan
==========
Crea un listado de los Breadcrumb disponibles

'''
from bcutilshcg import bcsession

import bcapihcg.Common_pb2
import bcutilshcg.discovery.constants
import bcutilshcg.discovery.sup
import bcapihcg
import json
import subprocess
import time
import logging
import signal
_logger = logging.getLogger('query')

_ROLES = {
    'view'  : bcsession.SESSION_ROLE_VIEW,
    'admin' : bcsession.SESSION_ROLE_ADMIN,
    'co'    : bcsession.SESSION_ROLE_CO
}

_DEFAULT_PASSWORD = {
    "co"    : "breadcrumb-co",
    "admin" : "breadcrumb-admin",
    "view"  : "breadcrumb-view"
}

_APT_STATE_CODE = {
    bcapihcg.State_pb2.State.APT_STATE_MASTER   : "APT_STATE_MASTER",
    bcapihcg.State_pb2.State.APT_STATE_SLAVE    : "APT_STATE_SLAVE",
    bcapihcg.State_pb2.State.APT_STATE_LINK     : "APT_STATE_LINK",
    bcapihcg.State_pb2.State.APT_STATE_NONE     : "APT_STATE_NONE",
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


def mac_to_string(mac_string):
    if isinstance(mac_string, bytes):
        return ':'.join('%02x' % b for b in mac_string)
    else:
        return ':'.join('%02x' % ord(b) for b in mac_string)


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
        auth_db             = _DEFAULT_PASSWORD.copy()
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
        try:
            # get state from the crumb
            m = bcapihcg.Message_pb2.BCMessage()
            m.state.CopyFrom(bcapihcg.State_pb2.State())

            if m is None:
                return None
    
            # no session means we can't send anything
            session = self.get_session(debug_mode)
            if session is None:
                return None

            try:
                session.sendmsg(m)
                state= session.recvmsg().state
                self.destroy_session()

            except Exception as e:
                #_logger.error("Unable to communicate with BreadCrumb: {}".format(e))
                self.destroy_session()
                state="No se pudo comunicar con BreadCrumb"
                return None

        except Exception as e:
            state="No se ha pudo obtener el estado"
            return None

        return state
          


