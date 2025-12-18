
from app.controllers.caja_crud import buscar_caja_abierta


def buscar_cajas_abierta(db):
    caja = buscar_caja_abierta(db)
    if caja:
        return True
    else:
        return False