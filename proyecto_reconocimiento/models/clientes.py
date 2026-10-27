class ClientesModel:
    def __init__(self, bd):
        self.bd = bd

    def buscar_por_dni(self, dni):
        """Devuelve {'id_cliente', 'dni', 'nombre', 'apellido'} o None si no existe."""
        return self.bd.consultar_uno(
            'SELECT id_cliente, dni, nombre, apellido FROM clientes WHERE dni = ?', (dni,))

    def crear(self, dni, nombre, apellido):
        return self.bd.ejecutar(
            'INSERT INTO clientes (dni, nombre, apellido) VALUES (?, ?, ?)', (dni, nombre, apellido))

    def listar(self):
        """Todos los clientes, con la fecha de su biometría (None si no están enrolados)."""
        return self.bd.consultar("""
            SELECT c.id_cliente, c.dni, c.nombre, c.apellido, b.fecha_actualizacion
            FROM clientes c
            LEFT JOIN biometria_facial b ON b.id_cliente = c.id_cliente
            ORDER BY c.apellido, c.nombre
        """)
