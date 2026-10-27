# Reconocimiento facial para sistema bancario

Los clientes del banco se autentican mirando la cámara de una terminal de la sucursal. El sistema compara su rostro con la biometría registrada, decide si la identidad es válida (similitud mayor a 85%) y guarda cada lectura para auditoría. Se maneja todo desde una interfaz gráfica.

## Historias de usuario y casos de uso

| | Qué pide | Dónde está |
|---|---|---|
| **HU1 · CU2** Registro biométrico | Validar el cliente por DNI, guardar `vector_facial` y `fecha_actualizacion` en `biometria_facial`, un solo registro vigente por persona | Pantalla **Enrolamiento** · `controllers/enrolamiento_controller.py`, `models/biometria_facial.py` |
| **HU2 · CU1** Autenticación en terminal | Dispositivo `ACTIVO`, comparar contra `biometria_facial`, más de 85% = `EXITOSO`, si no `RECHAZADO` con `id_cliente = NULL`, cada transacción en `registro_reconocimiento`, mostrar nombre y apellido | Pantalla **Terminal** · `controllers/terminal_controller.py` |
| **CU1 · A2** Dispositivo inactivo | Interrumpir la lectura, mostrar "fuera de servicio" y no generar la transacción | `terminal_controller.py` y un trigger en la base |
| **HU3** Auditoría | Cruzar `registro_reconocimiento`, `dispositivos`, `sucursales` y `clientes`; filtrar por sucursal, dispositivo y rango horario, y los rechazos con similitud alta | Pantalla **Auditoría** · `controllers/auditoria_controller.py`, `models/registro_reconocimiento.py` |
| **HU4** Gestión de dispositivos | Listar cada dispositivo con su sucursal; pasarlo a `INACTIVO` o `MANTENIMIENTO` bloquea nuevas transacciones | Pantalla **Dispositivos** · `controllers/dispositivos_controller.py`, `models/dispositivos.py` |

## Consigna técnica

| Consigna | Dónde está |
|---|---|
| Carga de imágenes desde archivos y conversión BGR → RGB | `models/cargador_imagenes.py` |
| Localizar rostros y codificar sus características | `models/reconocedor_facial.py` (`localizar_rostros`, `codificar_rostros`) |
| Comparar dos rostros y buscar la mejor coincidencia por distancia | `models/reconocedor_facial.py` (`comparar`, `identificar`) |
| Captura desde la cámara web en tiempo real | `controllers/app_controller.py` (`abrir_camara`, `leer_frame`, `detectar`) |
| Registro de nombre y hora de ingreso en CSV | `models/registro_asistencia.py` → `asistencia.csv` (cada cliente validado, una vez por día) |
| Rectángulos, nombres e imágenes de control y prueba | `views/interfaz_video.py`, botón **Comparar dos imágenes** |

## Base de datos

SQLite (`banco.db`), que viene con Python: no hace falta instalar un servidor. Se crea sola la primera vez, con tres sucursales y cuatro terminales de ejemplo (una en mantenimiento, para mostrar el bloqueo).

```
sucursales (id_sucursal, nombre, direccion)
dispositivos (id_dispositivo, id_sucursal, nombre, estado)          estado: ACTIVO | INACTIVO | MANTENIMIENTO
clientes (id_cliente, dni UNIQUE, nombre, apellido)
biometria_facial (id_biometria, id_cliente UNIQUE, vector_facial, fecha_actualizacion)
registro_reconocimiento (id_registro, id_dispositivo, id_cliente NULL, fecha_hora, resultado, nivel_similitud)
```

- `UNIQUE` en `biometria_facial.id_cliente` asegura un solo registro vigente por persona; volver a enrolar lo reemplaza (`INSERT ... ON CONFLICT DO UPDATE`).
- El trigger `bloquear_dispositivo_no_activo` rechaza cualquier `INSERT` en `registro_reconocimiento` de un dispositivo que no esté `ACTIVO`. El bloqueo de la HU4 lo hace la base, no depende solo de la aplicación.
- Se guarda el **vector de 128 números**, nunca la foto del cliente.

## Del parecido al porcentaje

`face_recognition` mide la **distancia** entre dos rostros: 0 es idéntico y 0.6 es su límite habitual para "misma persona". Los casos de uso hablan de un **nivel de similitud** de 0 a 100%, así que `distancia_a_similitud()` convierte una en otra: la distancia 0.6 vale 50%, más cerca sube hacia 100% y más lejos baja hacia 0%.

| Distancia | Similitud | Resultado |
|---|---|---|
| 0.35 (misma persona, fotos distintas) | 95% | EXITOSO |
| 0.526 | 85% | el umbral |
| 0.82 (personas distintas) | 23% | RECHAZADO |

El umbral de 85% equivale a una distancia de 0.526, más estricto que el 0.6 por defecto, como corresponde a un banco.

## Estructura (MVC)

```
proyecto_reconocimiento/
├── main.py                              # arma modelos, vistas y controladores
├── config/ajustes.py                    # umbral, base de datos, cámara
├── models/
│   ├── base_datos.py                    # tablas, trigger y datos de ejemplo
│   ├── clientes.py                      # tabla clientes
│   ├── biometria_facial.py              # vectores faciales
│   ├── dispositivos.py                  # sucursales y dispositivos
│   ├── registro_reconocimiento.py       # transacciones y reporte de auditoría
│   ├── registro_asistencia.py           # asistencia.csv
│   ├── cargador_imagenes.py             # lee imágenes y pasa de BGR a RGB
│   └── reconocedor_facial.py            # detecta, codifica, compara; distancia → similitud
├── controllers/
│   ├── app_controller.py                # cámara, detección, comparar dos imágenes
│   ├── terminal_controller.py           # HU2 / CU1
│   ├── enrolamiento_controller.py       # HU1 / CU2
│   ├── auditoria_controller.py          # HU3
│   └── dispositivos_controller.py       # HU4
└── views/
    ├── interfaz_grafica.py              # ventana principal (CustomTkinter), una pantalla por historia
    └── interfaz_video.py                # recuadros y nombres; ventanas de OpenCV
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

1. **Enrolamiento**: buscá al cliente por DNI. Si no existe, se da de alta ahí mismo con nombre y apellido. Encendé la cámara de enrolamiento y tocá **Capturar con la cámara** (o usá una foto del disco). La imagen tiene que tener un solo rostro.
2. **Terminal**: elegí la terminal y encendé la cámara. Cuando un cliente se ubica de frente, el sistema junta 5 capturas, se queda con la mejor y registra la transacción: cartel verde con su nombre si es `EXITOSO`, rojo si es `RECHAZADO`. Para la siguiente lectura, la persona tiene que salir de cuadro.
3. **Dispositivos**: cambiá el estado de una terminal. Si está en `MANTENIMIENTO` o `INACTIVO`, la terminal muestra "fuera de servicio" y no registra nada.
4. **Auditoría**: filtrá por sucursal, dispositivo, rango horario y resultado. El filtro de rechazos con similitud alta (70% o más) muestra a quienes se parecían mucho a un cliente sin llegar al umbral: posibles suplantaciones o clientes que la cámara no validó. Se exporta a CSV para Excel.

### Sin interfaz gráfica

```bash
python main.py --consola                       # terminal en una ventana de OpenCV ('q' para salir)
python main.py --comparar control.jpg prueba.jpg   # compara dos imágenes
```

Los valores se ajustan en `config/ajustes.py`: `UMBRAL_SIMILITUD` (0.85), `SIMILITUD_SOSPECHOSA` (0.70), `CAPTURAS_POR_LECTURA` y `ESPERA_ENTRE_LECTURAS`.
