import csv
from datetime import datetime

def leer_fecha(texto, fin_del_periodo=False):
    """Acepta 'AAAA-MM-DD' o 'AAAA-MM-DD HH:MM' y lo devuelve como 'AAAA-MM-DD HH:MM:SS'.

    Si es el final del rango, completa hasta el último segundo del día o del minuto.
    """
    texto = texto.strip()
    if not texto:
        return None
    for formato, completar in (('%Y-%m-%d', ' 23:59:59'), ('%Y-%m-%d %H:%M', ':59')):
        try:
            fecha = datetime.strptime(texto, formato)
        except ValueError:
            continue
        base = fecha.strftime('%Y-%m-%d' if formato == '%Y-%m-%d' else '%Y-%m-%d %H:%M')
        if fin_del_periodo:
            return base + completar
        return base + (' 00:00:00' if formato == '%Y-%m-%d' else ':00')
    raise ValueError(f"Fecha inválida: «{texto}». Usá AAAA-MM-DD o AAAA-MM-DD HH:MM.")


class AuditoriaController:
    """HU3: historial de lecturas por sucursal, dispositivo y rango horario."""

    def __init__(self, registro, dispositivos, ajustes):
        self.registro = registro
        self.dispositivos = dispositivos
        self.ajustes = ajustes

    def reporte(self, id_sucursal=None, id_dispositivo=None, desde='', hasta='',
                resultado=None, solo_sospechosos=False):
        """solo_sospechosos: rechazos con similitud alta, para evaluar falsos negativos
        o intentos de suplantación."""
        desde, hasta = leer_fecha(desde), leer_fecha(hasta, fin_del_periodo=True)
        if desde and hasta and desde > hasta:
            raise ValueError("La fecha «desde» es posterior a «hasta».")
        similitud_minima = None
        if solo_sospechosos:
            resultado = 'RECHAZADO'
            similitud_minima = self.ajustes.SIMILITUD_SOSPECHOSA
        return self.registro.consultar(id_sucursal, id_dispositivo, desde, hasta,
                                       resultado, similitud_minima)

    def exportar_csv(self, filas, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8-sig') as archivo:
            escritor = csv.writer(archivo, delimiter=';')
            escritor.writerow(['Fecha y hora', 'Sucursal', 'Dispositivo', 'DNI', 'Cliente',
                               'Resultado', 'Nivel de similitud'])
            for f in filas:
                cliente = f"{f['nombre']} {f['apellido']}" if f['dni'] else ''
                escritor.writerow([f['fecha_hora'], f['sucursal'], f['dispositivo'], f['dni'] or '',
                                   cliente, f['resultado'], f"{f['nivel_similitud']:.2f}"])
