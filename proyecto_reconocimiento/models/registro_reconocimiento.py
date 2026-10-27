import sqlite3
from datetime import datetime

class DispositivoNoActivoError(Exception):
    pass

# Consulta del reporte de auditoría: cruza las cuatro tablas (HU3)
CONSULTA_REPORTE = """
    SELECT r.id_registro, r.fecha_hora, r.resultado, r.nivel_similitud,
           d.id_dispositivo, d.nombre AS dispositivo,
           s.id_sucursal, s.nombre AS sucursal,
           c.dni, c.nombre, c.apellido
    FROM registro_reconocimiento r
    JOIN dispositivos d ON d.id_dispositivo = r.id_dispositivo
    JOIN sucursales s ON s.id_sucursal = d.id_sucursal
    LEFT JOIN clientes c ON c.id_cliente = r.id_cliente
"""

class RegistroReconocimientoModel:
    def __init__(self, bd):
        self.bd = bd

    def registrar(self, id_dispositivo, id_cliente, resultado, nivel_similitud):
        """Guarda una transacción de autenticación con la fecha y hora actuales.

        Lanza DispositivoNoActivoError si el trigger de la base la rechaza.
        """
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.bd.ejecutar("""
                INSERT INTO registro_reconocimiento
                    (id_dispositivo, id_cliente, fecha_hora, resultado, nivel_similitud)
                VALUES (?, ?, ?, ?, ?)
            """, (id_dispositivo, id_cliente, fecha_hora, resultado, round(float(nivel_similitud), 4)))
        except sqlite3.IntegrityError as e:
            if 'no está ACTIVO' in str(e):
                raise DispositivoNoActivoError(str(e)) from e
            raise
        return fecha_hora

    def consultar(self, id_sucursal=None, id_dispositivo=None, desde=None, hasta=None,
                  resultado=None, similitud_minima=None, limite=None):
        """Reporte filtrado. Las fechas van como texto 'AAAA-MM-DD HH:MM[:SS]'."""
        condiciones, parametros = [], []
        for condicion, valor in (('s.id_sucursal = ?', id_sucursal),
                                 ('d.id_dispositivo = ?', id_dispositivo),
                                 ('r.fecha_hora >= ?', desde),
                                 ('r.fecha_hora <= ?', hasta),
                                 ('r.resultado = ?', resultado),
                                 ('r.nivel_similitud >= ?', similitud_minima)):
            if valor is not None:
                condiciones.append(condicion)
                parametros.append(valor)

        sql = CONSULTA_REPORTE
        if condiciones:
            sql += ' WHERE ' + ' AND '.join(condiciones)
        sql += ' ORDER BY r.fecha_hora DESC, r.id_registro DESC'
        if limite:
            sql += f' LIMIT {int(limite)}'
        return self.bd.consultar(sql, parametros)
