import cv2
import numpy as np

class CargadorImagenesModel:
    def leer_archivo(self, ruta):
        """Lee una imagen en BGR (el formato de OpenCV).

        cv2.imread no abre rutas con acentos en Windows ("José.jpg"), por eso
        se lee el archivo como bytes y se decodifica aparte.
        """
        try:
            datos = np.fromfile(ruta, dtype=np.uint8)
        except OSError:
            datos = None
        imagen_bgr = cv2.imdecode(datos, cv2.IMREAD_COLOR) if datos is not None and datos.size else None
        if imagen_bgr is None:
            raise IOError(f"No se pudo leer la imagen: {ruta}")
        return imagen_bgr

    def cargar_imagen(self, ruta):
        """Carga una imagen desde archivo y la devuelve en RGB.

        OpenCV lee en BGR, pero face_recognition espera RGB: sin la conversión
        los colores quedan invertidos y la codificación facial sale peor.
        """
        return cv2.cvtColor(self.leer_archivo(ruta), cv2.COLOR_BGR2RGB)
