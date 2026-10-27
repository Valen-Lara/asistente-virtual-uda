from models.base_datos import ESTADOS_DISPOSITIVO

class DispositivosModel:
    def __init__(self, bd):
        self.bd = bd

    def listar(self):
        """Cada dispositivo con su sucursal (HU4)."""
        return self.bd.consultar("""
            SELECT d.id_dispositivo, d.nombre, d.estado, s.id_sucursal, s.nombre AS sucursal
            FROM dispositivos d
            JOIN sucursales s ON s.id_sucursal = d.id_sucursal
            ORDER BY s.nombre, d.nombre
        """)

    def obtener(self, id_dispositivo):
        return self.bd.consultar_uno("""
            SELECT d.id_dispositivo, d.nombre, d.estado, s.nombre AS sucursal
            FROM dispositivos d
            JOIN sucursales s ON s.id_sucursal = d.id_sucursal
            WHERE d.id_dispositivo = ?
        """, (id_dispositivo,))

    def cambiar_estado(self, id_dispositivo, estado):
        if estado not in ESTADOS_DISPOSITIVO:
            raise ValueError(f"Estado inválido: {estado}")
        self.bd.ejecutar('UPDATE dispositivos SET estado = ? WHERE id_dispositivo = ?',
                         (estado, id_dispositivo))

    def sucursales(self):
        return self.bd.consultar('SELECT id_sucursal, nombre FROM sucursales ORDER BY nombre')

    def crear(self, nombre_sucursal, nombre):
        """Da de alta un dispositivo. Si la sucursal no existe, la crea."""
        sucursal = self.bd.consultar_uno(
            'SELECT id_sucursal FROM sucursales WHERE nombre = ?', (nombre_sucursal,))
        id_sucursal = sucursal['id_sucursal'] if sucursal else self.bd.ejecutar(
            'INSERT INTO sucursales (nombre) VALUES (?)', (nombre_sucursal,))
        return self.bd.ejecutar(
            'INSERT INTO dispositivos (id_sucursal, nombre) VALUES (?, ?)', (id_sucursal, nombre))
