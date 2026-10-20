import os

# Carpeta raíz del proyecto (un nivel arriba de config/)
RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Una foto por empleado. El nombre del archivo es el nombre que se muestra
# y se registra: "Juan Perez.jpg" -> "Juan Perez"
CARPETA_EMPLEADOS = os.path.join(RUTA_PROYECTO, 'empleados')
EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png')

ARCHIVO_ASISTENCIA = os.path.join(RUTA_PROYECTO, 'asistencia.csv')

# Distancia máxima entre codificaciones para considerar que es la misma persona.
# Más bajo = más estricto. 0.6 es el valor por defecto de face_recognition.
TOLERANCIA = 0.6

# Se procesa cada frame achicado para que el video no se trabe.
ESCALA_FRAME = 0.25

INDICE_CAMARA = 0
