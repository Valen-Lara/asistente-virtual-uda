import os
import cv2

class AplicacionController:
    """Cámara, detección e imágenes de control/prueba. Los casos de uso están en
    los controladores de terminal, enrolamiento, auditoría y dispositivos."""

    def __init__(self, cargador, reconocedor, biometria, vista, ajustes):
        self.cargador = cargador
        self.reconocedor = reconocedor
        self.biometria = biometria
        self.vista = vista
        self.ajustes = ajustes
        self.camara = None
        # Los asigna main.py
        self.terminal = None
        self.enrolamiento = None
        self.auditoria = None
        self.dispositivos = None

    def cargar_clientes(self):
        """Pasa los vectores de biometria_facial al reconocedor. Devuelve cuántos hay."""
        self.reconocedor.cargar_clientes(self.biometria.listar_vectores())
        return len(self.reconocedor.ids_conocidos)

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

    def detectar(self, frame):
        """Localiza y codifica los rostros del frame. Devuelve [(ubicacion, codificacion)].

        Se trabaja sobre el frame achicado para que el video no se trabe, y las
        ubicaciones se devuelven en el tamaño real.
        """
        escala = self.ajustes.ESCALA_FRAME
        chico = cv2.resize(frame, (0, 0), fx=escala, fy=escala)
        chico_rgb = cv2.cvtColor(chico, cv2.COLOR_BGR2RGB)

        ubicaciones = self.reconocedor.localizar_rostros(chico_rgb)
        codificaciones = self.reconocedor.codificar_rostros(chico_rgb, ubicaciones)
        return [(tuple(int(valor / escala) for valor in ubicacion), codificacion)
                for ubicacion, codificacion in zip(ubicaciones, codificaciones)]

    # --- Terminal por consola (ventana de OpenCV) ----------------------------
    def iniciar(self):
        activos = [d for d in self.dispositivos.listar() if d['estado'] == 'ACTIVO']
        if not activos:
            print("No hay ningún dispositivo ACTIVO.")
            return
        dispositivo = activos[0]
        self.terminal.seleccionar(dispositivo['id_dispositivo'])
        print(f"Terminal: {dispositivo['sucursal']} · {dispositivo['nombre']}")

        self.cargar_clientes()
        if not self.abrir_camara():
            print("No se pudo abrir la cámara.")
            return
        try:
            while True:
                frame = self.leer_frame()
                if frame is None:
                    print("Error al acceder a la cámara.")
                    break

                lectura = self.terminal.procesar(frame)
                evento = lectura['evento']
                if evento:
                    print(f"{evento['fecha_hora']}  {evento['resultado']}  "
                          f"{evento['nombre'] or '-'}  ({evento['similitud']:.0%})")
                self.vista.renderizar_frame(frame, lectura['rostros'])
                if self.vista.escuchar_teclado() == 'q':
                    break
        finally:
            self.cerrar_camara()
            self.vista.cerrar_ventanas()

    # --- Imagen de control contra imagen de prueba ---------------------------
    def comparar(self, ruta_control, ruta_prueba):
        """Compara el primer rostro de cada imagen.

        Devuelve un dict con las dos imágenes (BGR, con el rostro marcado), si son
        la misma persona, la distancia y la similitud. Lanza ValueError si falta algún rostro.
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
        misma_persona, distancia, similitud = self.reconocedor.comparar(
            codificacion_control, codificacion_prueba)

        # Se dibuja sobre las copias BGR, que es el orden de colores de la vista
        self.vista.dibujar_rostro(control, ubicaciones_control[0], 'Control')
        self.vista.dibujar_rostro(prueba, ubicaciones_prueba[0], f'Prueba {similitud:.0%}', misma_persona)
        return {
            'control': control,
            'prueba': prueba,
            'misma_persona': misma_persona,
            'distancia': distancia,
            'similitud': similitud,
            'umbral': self.reconocedor.umbral_similitud,
        }

    def comparar_imagenes(self, ruta_control, ruta_prueba):
        """Versión de consola: imprime el resultado y muestra las dos imágenes."""
        try:
            resultado = self.comparar(ruta_control, ruta_prueba)
        except (ValueError, IOError) as e:
            print(e)
            return

        texto = 'Misma persona' if resultado['misma_persona'] else 'Distinta persona'
        print(f"{texto} (similitud: {resultado['similitud']:.0%}, distancia: {resultado['distancia']:.2f})")

        self.vista.mostrar_imagen('Imagen de control', resultado['control'])
        self.vista.mostrar_imagen('Imagen de prueba', resultado['prueba'])
        self.vista.esperar_tecla()
        self.vista.cerrar_ventanas()
