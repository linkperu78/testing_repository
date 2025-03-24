from hcglib     import InterfaceStats, _ROLES, _DEFAULT_PASSWORD

_HCG_RAJANT_USER = _ROLES['co']
_HCG_RAJANT_PASS = "breadcrumb-co"

def getRajantData(  ipv4        : str, 
                    user        : str   = _ROLES['co'], 
                    passw       : str   = _DEFAULT_PASSWORD["co"],
                    timeout     : int   = 5, 
                    debug_mode  : bool  = False
                  ):
    session_interface                   = InterfaceStats()
    session_interface._role             = user
    session_interface._passphrase       = passw
    session_interface._target           = ipv4
    session_interface._session_timeout  = timeout
    #data_proto_rajant                   = session_interface._printstate(_debug_mode)
    return session_interface._printstate(debug_mode)

