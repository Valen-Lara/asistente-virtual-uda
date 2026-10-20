# Registro de asistencia por reconocimiento facial

Reconoce a los empleados con la cámara web y registra su nombre y hora de ingreso en `asistencia.csv`. Se maneja todo desde una interfaz gráfica, sin usar la terminal.

## Funcionalidades

| Consigna | Dónde está |
|---|---|
| Carga de imágenes desde archivos y conversión BGR → RGB | `models/cargador_imagenes.py` |
| Localizar rostros y codificar sus características | `models/reconocedor_facial.py` (`localizar_rostros`, `codificar_rostros`) |
| Comparar dos rostros y buscar la mejor coincidencia por distancia | `models/reconocedor_facial.py` (`comparar`, `identificar`) |
| Captura desde la cámara web en tiempo real | `controllers/app_controller.py` (`abrir_camara`, `leer_frame`) |
| Registro de nombre y hora de ingreso en CSV | `models/registro_asistencia.py` |
| Rectángulos, nombres e imágenes de control y prueba | `views/interfaz_video.py`, `views/interfaz_grafica.py` |

## Estructura

```
proyecto_reconocimiento/
├── main.py                       # arma modelos, vista y controlador
├── config/ajustes.py             # rutas, tolerancia, cámara
├── models/
│   ├── cargador_imagenes.py      # lee/guarda imágenes y pasa de BGR a RGB
│   ├── reconocedor_facial.py     # detecta, codifica y compara rostros
│   └── registro_asistencia.py    # escribe y lee asistencia.csv
├── views/
│   ├── interfaz_grafica.py       # ventana principal (CustomTkinter)
│   └── interfaz_video.py         # dibuja recuadros y nombres; ventanas de OpenCV
├── controllers/app_controller.py # une modelos y vistas
└── empleados/                    # una foto por empleado
```

## Instalación

Hace falta **Python 3.12** ([python.org](https://www.python.org/downloads/release/python-31210/), marcando "Add Python to PATH" al instalar). Con versiones más nuevas puede no haber `dlib` ya compilado.

```bash
git clone https://github.com/Valen-Lara/asistente-virtual-uda.git
cd asistente-virtual-uda/proyecto_reconocimiento

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install --no-deps face_recognition
```

`face_recognition` depende de `dlib`, que normalmente se compila al instalarse (y en Windows pide CMake y Visual Studio Build Tools). Para evitarlo, `requirements.txt` trae `dlib-bin`, que ya viene compilado, y `face_recognition` se instala con `--no-deps` para que pip no intente compilar `dlib` igual. Probado con Python 3.12.

## Uso

Doble clic en **`iniciar.bat`**, o desde la terminal:

```bash
python main.py
```

Se abre la ventana principal:

- **Iniciar cámara**: muestra el video en vivo. Cada empleado reconocido aparece con un recuadro verde y su nombre (los desconocidos, en rojo) y su ingreso se registra solo, una vez por día. El panel de la derecha muestra quiénes llegaron hoy y a qué hora.
- **Registrar con la cámara**: con la cámara encendida y la persona de frente, saca la foto y pide el nombre. Ya queda reconocible, sin reiniciar.
- **Agregar desde una foto**: lo mismo, eligiendo una imagen del disco.
- **Comparar dos imágenes**: elegís una imagen de control y una de prueba, y muestra las dos lado a lado con el rostro marcado, si son la misma persona y la distancia entre ambas.
- **Carpeta de empleados** / **Abrir asistencia.csv**: abren los archivos en el explorador o en Excel.
- **Apariencia**: modo claro, oscuro o el del sistema.

Las fotos de los empleados se guardan en `empleados/` con el nombre como nombre del archivo (`Juan Perez.jpg` → `Juan Perez`). También se pueden copiar ahí a mano: tienen que tener un solo rostro y de frente.

`asistencia.csv` queda así:

```
Nombre,Fecha,Hora
Juan Perez,2026-10-20,08:59:12
```

### Sin interfaz gráfica

```bash
python main.py --consola                                        # cámara en una ventana de OpenCV ('q' para salir)
python main.py --comparar "empleados/Juan Perez.jpg" prueba.jpg # compara dos imágenes
```

La tolerancia para considerar que dos rostros son la misma persona se ajusta en `config/ajustes.py` (`TOLERANCIA`, 0.6 por defecto; más bajo es más estricto).
