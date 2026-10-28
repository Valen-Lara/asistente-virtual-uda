class RangosModel:
    """Rangos de las personas enroladas: Cliente, Admin, Seguridad, Técnico y los que se agreguen."""

    def __init__(self, bd):
        self.bd = bd

    def listar(self):
        return [f['nombre'] for f in self.bd.consultar('SELECT nombre FROM rangos ORDER BY id_rango')]

    def obtener_o_crear(self, nombre):
        """Devuelve el id del rango. Si no existe, lo crea.

        No distingue mayúsculas ni siquiera con tildes ("TÉCNICO" es "Técnico"):
        el COLLATE NOCASE de SQLite solo cubre las letras sin tilde.
        """
        for rango in self.bd.consultar('SELECT id_rango, nombre FROM rangos'):
            if rango['nombre'].casefold() == nombre.casefold():
                return rango['id_rango']
        return self.bd.ejecutar('INSERT INTO rangos (nombre) VALUES (?)', (nombre,))
