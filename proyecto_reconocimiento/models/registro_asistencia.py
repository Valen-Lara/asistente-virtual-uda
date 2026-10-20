import csv
import os
from datetime import datetime

class RegistroAsistenciaModel:
    ENCABEZADO = ['Nombre', 'Fecha', 'Hora']

    def __init__(self, ruta_csv):
        self.ruta_csv = ruta_csv
        # Quienes ya se sabe que tienen el ingreso de hoy: evita releer el CSV
        # en cada frame mientras la persona sigue frente a la cámara.
        self._registrados = set()
        if not os.path.exists(self.ruta_csv):
            with open(self.ruta_csv, 'w', newline='', encoding='utf-8') as archivo:
                csv.writer(archivo).writerow(self.ENCABEZADO)

    def registros_del_dia(self, fecha=None):
        """Devuelve [{'Nombre', 'Fecha', 'Hora'}] de la fecha pedida (hoy por defecto)."""
        fecha = fecha or datetime.now().strftime('%Y-%m-%d')
        with open(self.ruta_csv, newline='', encoding='utf-8') as archivo:
            return [fila for fila in csv.DictReader(archivo) if fila['Fecha'] == fecha]

    def _ya_registrado_hoy(self, nombre, fecha):
        if (nombre, fecha) in self._registrados:
            return True
        if any(fila['Nombre'] == nombre for fila in self.registros_del_dia(fecha)):
            self._registrados.add((nombre, fecha))
            return True
        return False

    def registrar_ingreso(self, nombre):
        """Guarda nombre, fecha y hora de ingreso. Solo una vez por día por empleado.

        Devuelve True si se registró, False si ya tenía el ingreso de hoy.
        """
        ahora = datetime.now()
        fecha = ahora.strftime('%Y-%m-%d')
        if self._ya_registrado_hoy(nombre, fecha):
            return False

        with open(self.ruta_csv, 'a', newline='', encoding='utf-8') as archivo:
            csv.writer(archivo).writerow([nombre, fecha, ahora.strftime('%H:%M:%S')])
        self._registrados.add((nombre, fecha))
        print(f"Asistencia registrada: {nombre} a las {ahora.strftime('%H:%M:%S')}")
        return True
