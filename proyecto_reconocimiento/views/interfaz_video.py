import cv2

# Colores en BGR, el orden que usa OpenCV
VERDE = (94, 158, 46)
ROJO = (69, 69, 214)
BLANCO = (255, 255, 255)

class InterfazVideoView:
    def __init__(self, nombre_ventana='Reconocimiento Facial - Terminal'):
        self.nombre_ventana = nombre_ventana

    def dibujar_rostro(self, imagen, ubicacion, etiqueta, conocido=True):
        """Dibuja el rectángulo y el nombre. La ubicación viene como (arriba, derecha, abajo, izquierda)."""
        arriba, derecha, abajo, izquierda = ubicacion
        color = VERDE if conocido else ROJO
        grosor = max(2, (derecha - izquierda) // 80)
        cv2.rectangle(imagen, (izquierda, arriba), (derecha, abajo), color, grosor)

        escala = max(0.5, (derecha - izquierda) / 250)
        (ancho, alto), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, escala, 1)
        cv2.rectangle(imagen, (izquierda, abajo), (max(derecha, izquierda + ancho + 12), abajo + alto + 14),
                      color, cv2.FILLED)
        cv2.putText(imagen, etiqueta, (izquierda + 6, abajo + alto + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, escala, BLANCO, 1, cv2.LINE_AA)

    def dibujar_rostros(self, frame, rostros):
        """rostros: lista de (ubicacion, etiqueta, conocido)."""
        for ubicacion, etiqueta, conocido in rostros:
            self.dibujar_rostro(frame, ubicacion, etiqueta, conocido)

    def renderizar_frame(self, frame, rostros):
        self.dibujar_rostros(frame, rostros)

        # Instrucciones en pantalla
        cv2.putText(frame, "Presiona 'q' para salir", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLANCO, 1)

        cv2.imshow(self.nombre_ventana, frame)

    def mostrar_imagen(self, titulo, imagen_bgr):
        cv2.imshow(titulo, imagen_bgr)

    def esperar_tecla(self):
        """Deja las ventanas abiertas hasta que se presione una tecla."""
        cv2.waitKey(0)

    def escuchar_teclado(self):
        """Retorna la tecla presionada (en formato string) o None"""
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('q'):
            return 'q'
        return None

    def cerrar_ventanas(self):
        cv2.destroyAllWindows()
