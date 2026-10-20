import os
import cv2

# Caracteres que Windows no acepta en un nombre de archivo
CARACTERES_INVALIDOS = '\\/:*?"<>|'

class AplicacionController:
    def __init__(self, cargador, reconocedor, registro, vista, ajustes):
        self.cargador = cargador
        self.reconocedor = reconocedor
        self.registro = registro
        self.vista = vista
        self.ajustes = ajustes
        self.camara = None

    # --- Empleados ---------------------------------------------------------
    def cargar_empleados(self):
        """Lee y codifica todas las fotos de la carpeta. Devuelve los nombres cargados."""
        os.makedirs(self.ajustes.CARPETA_EMPLEADOS, exist_ok=True)
        empleados = self.cargador.cargar_carpeta(
            self.ajustes.CARPETA_EMPLEADOS, self.ajustes.EXTENSIONES_IMAGEN
        )
        self.reconocedor.cargar_empleados(empleados)
        return list(self.reconocedor.nombres_conocidos)

    def agregar_empleado(self, nombre, imagen_bgr):
        """Guarda la foto de un empleado nuevo y lo suma al reconocedor.

        La foto tiene que tener un solo rostro. Lanza ValueError con un mensaje
        para mostrarle al usuario si algo no está bien.
        """
        nombre = ''.join(c for c in nombre if c not in CARACTERES_INVALIDOS).strip()
        if not nombre:
            raise ValueError("Ingresá un nombre válido.")
        if nombre in self.reconocedor.nombres_conocidos:
            raise ValueError(f"Ya hay un empleado llamado {nombre}.")

        imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
        ubicaciones = self.reconocedor.localizar_rostros(imagen_rgb)
        if not ubicaciones:
            raise ValueError("No se encontró ningún rostro en la imagen.")
        if len(ubicaciones) > 1:
            raise ValueError("Hay más de un rostro: usá una foto con una sola persona.")

        ruta = os.path.join(self.ajustes.CARPETA_EMPLEADOS, f'{nombre}.jpg')
        self.cargador.guardar_imagen(ruta, imagen_bgr)
        self.reconocedor.agregar_empleado(
            nombre, self.reconocedor.codificar_rostros(imagen_rgb, ubicaciones)[0]
        )
        return nombre

    def asistencias_de_hoy(self):
        return self.registro.registros_del_dia()

    # --- Cámara ------------------------------------------------------------
    def abrir_camara(self):
        # En Windows DirectShow abre la cámara mucho más rápido que el backend por defecto
        if os.name == 'nt':
            self.camara = cv2.VideoCapture(self.ajustes.INDICE_CAMARA, cv2.CAP_DSHOW)
        else:
            self.camara = cv2.VideoCapture(self.ajustes.INDICE_CAMARA)
        return self.camara.isOpened()

    def leer_frame(self):
        if self.camara is None:
            return None
        ret, frame = self.camara.read()
        return frame if ret else None

    def cerrar_camara(self):
        if self.camara is not None:
            self.camara.release()
            self.camara = None

    def procesar_frame(self, frame):
        """Reconoce los rostros del frame. Devuelve [(ubicacion, nombre o None)]."""
        escala = self.ajustes.ESCALA_FRAME
        chico = cv2.resize(frame, (0, 0), fx=escala, fy=escala)
        chico_rgb = cv2.cvtColor(chico, cv2.COLOR_BGR2RGB)

        ubicaciones = self.reconocedor.localizar_rostros(chico_rgb)
        codificaciones = self.reconocedor.codificar_rostros(chico_rgb, ubicaciones)

        rostros = []
        for ubicacion, codificacion in zip(ubicaciones, codificaciones):
            nombre, _ = self.reconocedor.identificar(codificacion)
            # Las coordenadas salen del frame achicado: se vuelven al tamaño real
            ubicacion_real = tuple(int(valor / escala) for valor in ubicacion)
            rostros.append((ubicacion_real, nombre))
        return rostros

    def reconocer_y_registrar(self, frame):
        """Reconoce el frame y registra la asistencia de los empleados que aparecen.

        Devuelve (rostros, nombres registrados recién ahora).
        """
        rostros = self.procesar_frame(frame)
        nuevos = [nombre for _, nombre in rostros
                  if nombre and self.registro.registrar_ingreso(nombre)]
        return rostros, nuevos

    # --- Modo asistencia por consola (ventana de OpenCV) --------------------
    def iniciar(self):
        self.cargar_empleados()
        self.abrir_camara()
        try:
            while True:
                frame = self.leer_frame()
                if frame is None:
                    print("Error al acceder a la cámara.")
                    break

                rostros, _ = self.reconocer_y_registrar(frame)
                self.vista.renderizar_frame(frame, rostros)
                if self.vista.escuchar_teclado() == 'q':
                    break
        finally:
            self.cerrar_camara()
            self.vista.cerrar_ventanas()

    # --- Imagen de control contra imagen de prueba ---------------------------
    def comparar(self, ruta_control, ruta_prueba):
        """Compara el primer rostro de cada imagen.

        Devuelve un dict con las dos imágenes (BGR, con el rostro marcado), si son
        la misma persona y la distancia. Lanza ValueError si falta algún rostro.
        """
        control = self.cargador.leer_archivo(ruta_control)
        prueba = self.cargador.leer_archivo(ruta_prueba)
        control_rgb = cv2.cvtColor(control, cv2.COLOR_BGR2RGB)
        prueba_rgb = cv2.cvtColor(prueba, cv2.COLOR_BGR2RGB)

        ubicaciones_control = self.reconocedor.localizar_rostros(control_rgb)
        ubicaciones_prueba = self.reconocedor.localizar_rostros(prueba_rgb)
        if not ubicaciones_control:
            raise ValueError("No se encontró un rostro en la imagen de control.")
        if not ubicaciones_prueba:
            raise ValueError("No se encontró un rostro en la imagen de prueba.")

        codificacion_control = self.reconocedor.codificar_rostros(control_rgb, ubicaciones_control)[0]
        codificacion_prueba = self.reconocedor.codificar_rostros(prueba_rgb, ubicaciones_prueba)[0]
        misma_persona, distancia = self.reconocedor.comparar(codificacion_control, codificacion_prueba)

        # Se dibuja sobre las copias BGR, que es el orden de colores de la vista
        self.vista.dibujar_rostro(control, ubicaciones_control[0], 'Control')
        self.vista.dibujar_rostro(prueba, ubicaciones_prueba[0], 'Prueba', misma_persona)
        return {
            'control': control,
            'prueba': prueba,
            'misma_persona': misma_persona,
            'distancia': distancia,
            'tolerancia': self.reconocedor.tolerancia,
        }

    def comparar_imagenes(self, ruta_control, ruta_prueba):
        """Versión de consola: imprime el resultado y muestra las dos imágenes."""
        try:
            resultado = self.comparar(ruta_control, ruta_prueba)
        except (ValueError, IOError) as e:
            print(e)
            return

        texto = 'Misma persona' if resultado['misma_persona'] else 'Distinta persona'
        print(f"{texto} (distancia: {resultado['distancia']:.2f})")

        self.vista.mostrar_imagen('Imagen de control', resultado['control'])
        self.vista.mostrar_imagen('Imagen de prueba', resultado['prueba'])
        self.vista.esperar_tecla()
        self.vista.cerrar_ventanas()
