import os

# Carpeta raíz del proyecto (un nivel arriba de config/)
RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Base de datos SQLite con las tablas de los casos de uso: clientes,
# biometria_facial, sucursales, dispositivos y registro_reconocimiento.
ARCHIVO_BD = os.path.join(RUTA_PROYECTO, 'banco.db')

# Nombre, fecha y hora de cada cliente validado, una vez por día (consigna del CSV)
ARCHIVO_ASISTENCIA = os.path.join(RUTA_PROYECTO, 'asistencia.csv')

# Nivel de similitud que hay que superar para que la autenticación sea EXITOSA (HU2).
UMBRAL_SIMILITUD = 0.85

# Distancia de face_recognition a la que la similitud vale 50%. Es el límite
# por defecto de la librería y sirve de punto medio para pasar de distancia a %.
TOLERANCIA = 0.6

# Rechazos con al menos esta similitud se marcan como sospechosos en la auditoría (HU3):
# alguien muy parecido a un cliente, o un cliente al que la cámara no validó.
SIMILITUD_SOSPECHOSA = 0.70

# Una lectura junta varias capturas seguidas y se queda con la mejor, para que
# un cuadro movido no rechace a un cliente.
CAPTURAS_POR_LECTURA = 5

# Segundos mínimos entre una lectura y la siguiente en la terminal. Además, la
# persona tiene que salir de cuadro: cada lectura es una transacción en
# registro_reconocimiento y no tiene que repetirse mientras sigue frente a la cámara.
ESPERA_ENTRE_LECTURAS = 4

# Se procesa cada frame achicado para que el video no se trabe.
ESCALA_FRAME = 0.25

INDICE_CAMARA = 0
