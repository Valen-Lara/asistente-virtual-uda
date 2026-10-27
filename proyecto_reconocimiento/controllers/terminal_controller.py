import time

from models.registro_reconocimiento import DispositivoNoActivoError

class TerminalController:
    """Caso de uso 1 / HU2: el cliente se autentica frente a la cámara de una terminal."""

    def __init__(self, app, dispositivos, registro, asistencia, ajustes):
        self.app = app
        self.dispositivos = dispositivos
        self.registro = registro
        self.asistencia = asistencia
        self.ajustes = ajustes
        self.id_dispositivo = None
        self._capturas = []
        self._proxima_lectura = 0.0
        # Después de cada transacción la persona tiene que salir de cuadro antes de la siguiente
        self._esperando_que_se_retire = False

    def seleccionar(self, id_dispositivo):
        self.id_dispositivo = id_dispositivo
        self._capturas = []
        self._proxima_lectura = 0.0
        self._esperando_que_se_retire = False

    def dispositivo(self):
        return self.dispositivos.obtener(self.id_dispositivo) if self.id_dispositivo else None

    def ultimas_lecturas(self, cantidad=8):
        return self.registro.consultar(id_dispositivo=self.id_dispositivo, limite=cantidad)

    def procesar(self, frame):
        """Reconoce el frame y, cuando junta suficientes capturas, registra la transacción.

        Devuelve un dict con:
          rostros: [(ubicacion, etiqueta, conocido)] para dibujar
          estado: el estado del dispositivo
          progreso: de 0 a 1, cuántas capturas lleva la lectura en curso
          en_pausa: True si todavía no se puede empezar otra lectura
          evento: None, o el resultado de la transacción que se acaba de registrar
        """
        lectura = {'rostros': [], 'estado': None, 'progreso': 0.0, 'en_pausa': False, 'evento': None}
        dispositivo = self.dispositivo()
        lectura['estado'] = dispositivo['estado'] if dispositivo else None

        # A2: si la terminal no está ACTIVA se interrumpe la lectura y no se registra nada
        if lectura['estado'] != 'ACTIVO':
            self._capturas = []
            return lectura

        rostros = []
        for ubicacion, codificacion in self.app.detectar(frame):
            id_cliente, nombre, similitud = self.app.reconocedor.identificar(codificacion)
            rostros.append((ubicacion, id_cliente, nombre, similitud))
        lectura['rostros'] = [
            (ubicacion, f"{nombre or 'Desconocido'} {similitud:.0%}", id_cliente is not None)
            for ubicacion, id_cliente, nombre, similitud in rostros
        ]

        if not rostros:
            # Si la persona se va a mitad de la lectura, se empieza de cero
            self._capturas = []
            self._esperando_que_se_retire = False
        if time.monotonic() < self._proxima_lectura or self._esperando_que_se_retire:
            lectura['en_pausa'] = True
            return lectura
        if not rostros:
            return lectura

        # Se lee a quien está más cerca de la terminal: el rostro más grande
        _, id_cliente, nombre, similitud = max(
            rostros, key=lambda r: (r[0][1] - r[0][3]) * (r[0][2] - r[0][0]))
        self._capturas.append((similitud, id_cliente, nombre))
        lectura['progreso'] = len(self._capturas) / self.ajustes.CAPTURAS_POR_LECTURA
        if len(self._capturas) < self.ajustes.CAPTURAS_POR_LECTURA:
            return lectura

        # Se queda con la mejor de las capturas
        similitud, id_cliente, nombre = max(self._capturas, key=lambda c: c[0])
        self._capturas = []
        self._proxima_lectura = time.monotonic() + self.ajustes.ESPERA_ENTRE_LECTURAS
        self._esperando_que_se_retire = True
        resultado = 'EXITOSO' if id_cliente is not None else 'RECHAZADO'

        try:
            fecha_hora = self.registro.registrar(self.id_dispositivo, id_cliente, resultado, similitud)
        except DispositivoNoActivoError:
            # Cambiaron el estado justo durante la lectura: la base no dejó registrarla
            lectura['estado'] = 'INACTIVO'
            lectura['rostros'] = []
            return lectura

        if resultado == 'EXITOSO':
            self.asistencia.registrar_ingreso(nombre)
        lectura['evento'] = {'resultado': resultado, 'nombre': nombre,
                             'similitud': similitud, 'fecha_hora': fecha_hora}
        return lectura
