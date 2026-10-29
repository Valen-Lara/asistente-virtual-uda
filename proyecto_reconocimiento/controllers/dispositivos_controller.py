import sqlite3

class DispositivosController:
    """HU4: el técnico lista los dispositivos de cada sucursal y cambia su estado."""

    def __init__(self, dispositivos):
        self.dispositivos = dispositivos

    def listar(self):
        return self.dispositivos.listar()

    def sucursales(self):
        return self.dispositivos.sucursales()

    def cambiar_estado(self, id_dispositivo, estado):
        self.dispositivos.cambiar_estado(id_dispositivo, estado)

    def crear(self, sucursal, nombre):
        sucursal, nombre = sucursal.strip(), nombre.strip()
        if not sucursal or not nombre:
            raise ValueError("Completá la sucursal y el nombre del dispositivo.")
        try:
            return self.dispositivos.crear(sucursal, nombre)
        except sqlite3.IntegrityError:
            raise ValueError(f"Ya hay un dispositivo «{nombre}» en {sucursal}.")
