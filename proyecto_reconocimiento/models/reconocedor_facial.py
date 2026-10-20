import face_recognition
import numpy as np

class ReconocedorFacialModel:
    def __init__(self, tolerancia=0.6):
        self.tolerancia = tolerancia
        self.nombres_conocidos = []
        self.codificaciones_conocidas = []

    # --- Detección y codificación ------------------------------------------
    def localizar_rostros(self, imagen_rgb):
        """Devuelve las ubicaciones de los rostros como (arriba, derecha, abajo, izquierda)."""
        return face_recognition.face_locations(imagen_rgb)

    def codificar_rostros(self, imagen_rgb, ubicaciones=None):
        """Devuelve un vector de 128 características por cada rostro."""
        return face_recognition.face_encodings(imagen_rgb, ubicaciones)

    def agregar_empleado(self, nombre, codificacion):
        self.nombres_conocidos.append(nombre)
        self.codificaciones_conocidas.append(codificacion)

    def cargar_empleados(self, imagenes):
        """Codifica la foto de cada empleado. Recibe una lista de (nombre, imagen_rgb).

        Reemplaza a los empleados cargados antes, así se puede volver a llamar
        cuando cambian las fotos.
        """
        self.nombres_conocidos = []
        self.codificaciones_conocidas = []
        for nombre, imagen in imagenes:
            codificaciones = self.codificar_rostros(imagen)
            if not codificaciones:
                print(f"No se encontró un rostro en la foto de {nombre}, se omite.")
                continue
            self.agregar_empleado(nombre, codificaciones[0])
        print(f"Empleados cargados: {len(self.nombres_conocidos)}")

    # --- Comparación -------------------------------------------------------
    def comparar(self, codificacion_a, codificacion_b):
        """Compara dos rostros. Devuelve (misma_persona, distancia)."""
        distancia = float(face_recognition.face_distance([codificacion_a], codificacion_b)[0])
        return distancia <= self.tolerancia, distancia

    def identificar(self, codificacion):
        """Busca el empleado más parecido. Devuelve (nombre, distancia) o (None, distancia)."""
        if not self.codificaciones_conocidas:
            return None, None

        coincidencias = face_recognition.compare_faces(
            self.codificaciones_conocidas, codificacion, tolerance=self.tolerancia
        )
        distancias = face_recognition.face_distance(self.codificaciones_conocidas, codificacion)

        # La mejor coincidencia es la de menor distancia, siempre que pase la tolerancia
        mejor = int(np.argmin(distancias))
        if coincidencias[mejor]:
            return self.nombres_conocidos[mejor], float(distancias[mejor])
        return None, float(distancias[mejor])
