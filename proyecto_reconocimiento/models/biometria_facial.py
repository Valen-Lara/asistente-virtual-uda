from datetime import datetime

import numpy as np

class BiometriaFacialModel:
    """Guarda el vector de 128 características de cada cliente, nunca la foto."""

    def __init__(self, bd):
        self.bd = bd

    def guardar(self, id_cliente, vector):
        """Inserta o reemplaza el vector del cliente (un solo registro vigente por persona).

        Devuelve (fecha_actualizacion, si ya tenía uno antes).
        """
        ya_tenia = self.obtener_fecha(id_cliente) is not None
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.bd.ejecutar("""
            INSERT INTO biometria_facial (id_cliente, vector_facial, fecha_actualizacion)
            VALUES (?, ?, ?)
            ON CONFLICT (id_cliente) DO UPDATE SET
                vector_facial = excluded.vector_facial,
                fecha_actualizacion = excluded.fecha_actualizacion
        """, (id_cliente, np.asarray(vector, dtype=np.float64).tobytes(), fecha))
        return fecha, ya_tenia

    def obtener_fecha(self, id_cliente):
        fila = self.bd.consultar_uno(
            'SELECT fecha_actualizacion FROM biometria_facial WHERE id_cliente = ?', (id_cliente,))
        return fila['fecha_actualizacion'] if fila else None

    def listar_vectores(self):
        """Devuelve [(id_cliente, 'Nombre Apellido', vector)] de todos los clientes enrolados."""
        filas = self.bd.consultar("""
            SELECT c.id_cliente, c.nombre, c.apellido, b.vector_facial
            FROM biometria_facial b
            JOIN clientes c ON c.id_cliente = b.id_cliente
        """)
        return [(f['id_cliente'], f"{f['nombre']} {f['apellido']}",
                 np.frombuffer(f['vector_facial'], dtype=np.float64)) for f in filas]
