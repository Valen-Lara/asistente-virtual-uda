CONSULTA_CLIENTE = """
    SELECT c.id_cliente, c.dni, c.nombre, c.apellido, r.nombre AS rango
    FROM clientes c
    LEFT JOIN rangos r ON r.id_rango = c.id_rango
"""

class ClientesModel:
    def __init__(self, bd):
        self.bd = bd

    def buscar_por_dni(self, dni):
        """Devuelve {'id_cliente', 'dni', 'nombre', 'apellido', 'rango'} o None si no existe."""
        return self.bd.consultar_uno(CONSULTA_CLIENTE + ' WHERE c.dni = ?', (dni,))

    def obtener(self, id_cliente):
        return self.bd.consultar_uno(CONSULTA_CLIENTE + ' WHERE c.id_cliente = ?', (id_cliente,))

    def crear(self, dni, nombre, apellido, id_rango):
        return self.bd.ejecutar(
            'INSERT INTO clientes (dni, nombre, apellido, id_rango) VALUES (?, ?, ?, ?)',
            (dni, nombre, apellido, id_rango))

    def cambiar_rango(self, id_cliente, id_rango):
        self.bd.ejecutar('UPDATE clientes SET id_rango = ? WHERE id_cliente = ?', (id_rango, id_cliente))

    def listar(self):
        """Todos los clientes, con su rango y la fecha de su biometría (None si no están enrolados)."""
        return self.bd.consultar("""
            SELECT c.id_cliente, c.dni, c.nombre, c.apellido, r.nombre AS rango, b.fecha_actualizacion
            FROM clientes c
            LEFT JOIN rangos r ON r.id_rango = c.id_rango
            LEFT JOIN biometria_facial b ON b.id_cliente = c.id_cliente
            ORDER BY c.apellido, c.nombre
        """)
