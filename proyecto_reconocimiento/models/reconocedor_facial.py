import face_recognition
import numpy as np

def distancia_a_similitud(distancia, tolerancia=0.6):
    """Pasa la distancia de face_recognition (0 = idénticos) a un nivel de similitud de 0 a 1.

    La distancia igual a la tolerancia vale 50%. Por encima baja en línea recta
    hasta 0; por debajo sube con una curva que acerca a 100% las coincidencias
    claras. Así 0.35 (misma persona en fotos distintas) da ~95% y 0.82
    (personas distintas) da ~22%.
    """
    if distancia > tolerancia:
        return max(0.0, (1.0 - distancia) / ((1.0 - tolerancia) * 2))
    lineal = 1.0 - distancia / (tolerancia * 2)
    return lineal + (1.0 - lineal) * ((lineal - 0.5) * 2) ** 0.2


def similitud_a_distancia(similitud, tolerancia=0.6):
    """Inversa de distancia_a_similitud: la distancia máxima que alcanza esa similitud."""
    abajo, arriba = 0.0, 1.0
    # La similitud baja siempre que la distancia sube: alcanza con búsqueda binaria
    for _ in range(50):
        medio = (abajo + arriba) / 2
        if distancia_a_similitud(medio, tolerancia) >= similitud:
            abajo = medio
        else:
            arriba = medio
    return abajo


class ReconocedorFacialModel:
    def __init__(self, umbral_similitud=0.85, tolerancia=0.6):
        self.umbral_similitud = umbral_similitud
        self.tolerancia = tolerancia
        # Distancia equivalente al umbral: es la tolerancia que se le pasa a compare_faces
        self.distancia_maxima = similitud_a_distancia(umbral_similitud, tolerancia)
        self.ids_conocidos = []
        self.nombres_conocidos = []
        self.codificaciones_conocidas = []

    # --- Detección y codificación ------------------------------------------
    def localizar_rostros(self, imagen_rgb):
        """Devuelve las ubicaciones de los rostros como (arriba, derecha, abajo, izquierda)."""
        return face_recognition.face_locations(imagen_rgb)

    def codificar_rostros(self, imagen_rgb, ubicaciones=None):
        """Devuelve un vector de 128 características por cada rostro."""
        return face_recognition.face_encodings(imagen_rgb, ubicaciones)

    def similitud(self, distancia):
        return distancia_a_similitud(distancia, self.tolerancia)

    # --- Clientes enrolados ------------------------------------------------
    def cargar_clientes(self, clientes):
        """Recibe [(id_cliente, nombre, vector)] desde biometria_facial y reemplaza los anteriores."""
        self.ids_conocidos = [id_cliente for id_cliente, _, _ in clientes]
        self.nombres_conocidos = [nombre for _, nombre, _ in clientes]
        self.codificaciones_conocidas = [vector for _, _, vector in clientes]

    def actualizar_cliente(self, id_cliente, nombre, codificacion):
        """Agrega un cliente o reemplaza su vector si ya estaba (un solo registro vigente)."""
        if id_cliente in self.ids_conocidos:
            i = self.ids_conocidos.index(id_cliente)
            self.nombres_conocidos[i] = nombre
            self.codificaciones_conocidas[i] = codificacion
        else:
            self.ids_conocidos.append(id_cliente)
            self.nombres_conocidos.append(nombre)
            self.codificaciones_conocidas.append(codificacion)

    # --- Comparación -------------------------------------------------------
    def comparar(self, codificacion_a, codificacion_b):
        """Compara dos rostros. Devuelve (misma_persona, distancia, similitud)."""
        distancia = float(face_recognition.face_distance([codificacion_a], codificacion_b)[0])
        similitud = self.similitud(distancia)
        return similitud >= self.umbral_similitud, distancia, similitud

    def identificar(self, codificacion):
        """Busca el cliente más parecido.

        Devuelve (id_cliente, nombre, similitud). Si nadie supera el umbral, id y
        nombre son None y la similitud es la del más parecido (0 si no hay nadie).
        """
        if not self.codificaciones_conocidas:
            return None, None, 0.0

        coincidencias = face_recognition.compare_faces(
            self.codificaciones_conocidas, codificacion, tolerance=self.distancia_maxima
        )
        distancias = face_recognition.face_distance(self.codificaciones_conocidas, codificacion)

        # La mejor coincidencia es la de menor distancia, siempre que pase el umbral
        mejor = int(np.argmin(distancias))
        similitud = self.similitud(float(distancias[mejor]))
        if coincidencias[mejor]:
            return self.ids_conocidos[mejor], self.nombres_conocidos[mejor], similitud
        return None, None, similitud
