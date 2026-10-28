# Preguntas para el oral

Cómo usarlo: leé la pregunta, tapá la respuesta, contestá en voz alta y después compará.

Las que más conviene tener firmes, porque son las más probables y muestran que entendés cómo funciona por dentro: **6, 9, 11, 14, 25, 33, 36, 39, 49 y 61**.

---

## 1. Generales

**1. ¿Qué hace la app, en una oración?**
Autentica a las personas en las terminales de un banco por reconocimiento facial: compara la cara con la biometría registrada, decide si pasa el 85% de similitud y guarda cada intento para auditoría.

**2. ¿Qué problema resuelve?**
Que la persona se identifique sin tarjeta ni contraseña, y que el banco tenga registro de cada intento: quién, dónde, cuándo y con qué similitud.

**3. ¿Quiénes usan el sistema?**
- El **cliente**, que se autentica (HU2).
- El **operador**, que lo enrola (HU1).
- El **auditor**, que revisa el historial (HU3).
- El **administrador de TI**, que gestiona las terminales (HU4).

**4. ¿Qué tecnologías usaron?**
- **Python 3.12**.
- **OpenCV**, para la cámara y para dibujar.
- **face_recognition** (sobre **dlib**), para detectar y codificar caras.
- **NumPy**, para los vectores.
- **SQLite**, como base de datos.
- **CustomTkinter**, para la interfaz.

**5. ¿Por qué Python?**
Tiene las librerías de visión más maduras y simples (OpenCV, face_recognition), y es el lenguaje de la materia.

---

## 2. Reconocimiento facial

**6. ¿Cómo reconoce una cara, paso a paso?**
1. Toma el frame de la cámara.
2. Lo pasa de BGR a RGB.
3. **Localiza** los rostros, es decir, dónde hay una cara.
4. **Codifica** cada rostro en un vector de 128 números.
5. **Compara** ese vector contra los de las personas registradas y elige la más parecida.

**7. ¿Qué es el "encoding" o vector facial?**
128 números que resumen los rasgos de la cara. Los genera una red neuronal de dlib entrenada para que la misma persona dé vectores parecidos y personas distintas den vectores lejanos.

**8. ¿Por qué 128 números?**
Así está entrenado el modelo de dlib. Alcanza para distinguir personas y es liviano para guardar y comparar.

**9. ¿Cómo se comparan dos caras?**
Con la **distancia euclidiana** entre los dos vectores. Cuanto más chica la distancia, más parecidas. Un valor de 0 significa idénticas.

**10. ¿Qué es la tolerancia 0.6?**
Es el límite por defecto de face_recognition: por debajo de 0.6 de distancia considera que es la misma persona.

**11. ¿Cómo pasan de distancia a porcentaje de similitud?**
Con la función `distancia_a_similitud()`. La distancia 0.6 equivale a 50%; más cerca sube hacia 100% y más lejos baja hacia 0%. Por ejemplo, 0.35 da 95% y 0.82 da 23%.

**12. ¿Qué distancia corresponde al 85%?**
Aproximadamente **0.526**. Es más estricta que el 0.6 por defecto, como corresponde a un banco.

**13. ¿Cómo encuentran la "mejor coincidencia"?**
`face_distance` calcula la distancia contra todas las personas registradas y `argmin` elige la más cercana. Si esa no supera el umbral, el resultado es RECHAZADO.

**14. ¿Por qué hay que convertir de BGR a RGB?**
OpenCV lee las imágenes en orden Azul-Verde-Rojo, pero face_recognition/dlib espera Rojo-Verde-Azul. Sin la conversión, los colores llegan invertidos y el reconocimiento empeora.

**15. ¿Qué método usa para detectar la cara?**
El detector por defecto de face_recognition, **HOG**, que analiza los bordes y gradientes de la imagen. Es rápido y funciona sin GPU.

**16. ¿Por qué achican el frame?**
Se procesa al 25% del tamaño (`ESCALA_FRAME = 0.25`) para que el video no se trabe. Después las coordenadas se multiplican por 4 para dibujar el recuadro en la imagen original.

**17. ¿Qué pasa si hay dos personas frente a la cámara?**
Se lee a la que está más cerca, que es el rostro más grande. En el enrolamiento, en cambio, se exige **exactamente una** cara.

**18. ¿Por qué toman 5 capturas y no una?**
Un solo cuadro puede salir movido o con mala luz y rechazar a una persona válida. Se juntan 5 y se queda la mejor.

**19. ¿Por qué la persona tiene que salir de cuadro antes de la siguiente lectura?**
Cada lectura es una transacción en la base. Si no, mientras la persona sigue parada se registrarían decenas de transacciones repetidas. Además hay una espera mínima de 4 segundos.

---

## 3. Historias de usuario y casos de uso

**20. ¿Qué pide la HU1 y cómo la resolvieron?**
Registrar la biometría de un cliente. Se valida que exista por DNI, se captura la cara y se guarda el vector en `biometria_facial` con su `fecha_actualizacion`.

**21. ¿Qué pasa si enrolan dos veces a la misma persona?**
Se **reemplaza** el registro anterior: hay un solo registro vigente por persona. Lo asegura el `UNIQUE` en `id_cliente` junto con `INSERT … ON CONFLICT DO UPDATE`.

**22. ¿Qué pasa si el DNI no existe?**
La app permite darlo de alta en el momento, con nombre, apellido y rango. El DNI tiene que tener 7 u 8 dígitos.

**23. ¿Qué pide la HU2?**
Autenticarse en una terminal ACTIVA. Si la similitud es mayor a 85%, es EXITOSO y se muestran nombre, apellido y rango. Si no, es RECHAZADO. Todo intento se registra.

**24. ¿Qué es el flujo alternativo A1?**
Similitud insuficiente: se registra RECHAZADO con `id_cliente` NULL y se le pide a la persona que ingrese con su DNI o pida ayuda al personal.

**25. ¿Por qué `id_cliente` queda NULL si es rechazado?**
Porque no se confirmó quién es. Guardar al "más parecido" sería afirmar una identidad que el sistema no validó.

**26. ¿Qué es el flujo A2?**
La terminal no está ACTIVA: se interrumpe la lectura, se muestra "fuera de servicio" y no se genera transacción.

**27. ¿Qué pide la HU3?**
Que un auditor vea el historial filtrando por sucursal, dispositivo y rango horario, y que detecte rechazos con similitud alta.

**28. ¿Qué es un rechazo "sospechoso"?**
Un RECHAZADO con 70% o más de similitud. Es alguien muy parecido a una persona registrada sin llegar al 85%: puede ser un intento de suplantación o alguien al que la cámara no validó bien.

**29. ¿Qué pide la HU4?**
Que un administrador vea los dispositivos por sucursal y cambie su estado. En INACTIVO o MANTENIMIENTO, la terminal no acepta transacciones.

---

## 4. Base de datos

**30. ¿Qué tablas tiene?**
`sucursales`, `dispositivos`, `rangos`, `clientes`, `biometria_facial` y `registro_reconocimiento`.

**31. ¿Cómo se relacionan?**
- Una sucursal tiene muchos dispositivos.
- Un rango lo tienen muchas personas.
- Una persona tiene una biometría.
- Cada registro de reconocimiento apunta a un dispositivo y, si fue exitoso, a una persona.

**32. ¿Por qué SQLite y no MySQL?**
Viene incluido con Python, no requiere instalar ni configurar un servidor y la base es un solo archivo (`banco.db`). Para una demo es ideal. En producción se usaría un motor como MySQL o PostgreSQL, y el modelo de tablas es el mismo.

**33. ¿Qué es el trigger y para qué sirve?**
`bloquear_dispositivo_no_activo` rechaza cualquier INSERT en `registro_reconocimiento` de un dispositivo que no esté ACTIVO. El bloqueo de la HU4 queda garantizado **por la base**, aunque la aplicación tuviera un error.

**34. ¿Qué otras restricciones tiene la base?**
- CHECK del estado del dispositivo: ACTIVO, INACTIVO o MANTENIMIENTO.
- CHECK del resultado: EXITOSO o RECHAZADO.
- UNIQUE en el DNI, en la biometría por persona y en el nombre del rango.
- Claves foráneas activadas.
- Índices para que las consultas de auditoría sean rápidas.

**35. ¿Cómo guardan el vector en la base?**
Como bytes (BLOB). Al leerlo se reconstruye con `np.frombuffer`.

**36. ¿Guardan las fotos de las personas?**
No. Solo se guarda el vector de 128 números, y a partir del vector no se puede reconstruir la foto. Es más liviano y más respetuoso de la privacidad.

**37. ¿Qué consulta usa la auditoría?**
Un JOIN entre `registro_reconocimiento`, `dispositivos`, `sucursales`, `clientes` y `rangos` (LEFT JOIN, porque los rechazados no tienen persona), con filtros opcionales en el WHERE.

**38. ¿Cómo se resetean los datos?**
Se borra `banco.db`. La próxima vez que se abre la app, se crea de nuevo con los datos de ejemplo.

---

## 5. Arquitectura y código

**39. ¿Qué es MVC y cómo lo aplicaron?**
- **Modelo** (`models/`): los datos y la lógica, es decir, la base, el reconocedor y el CSV.
- **Vista** (`views/`): lo que ve el usuario.
- **Controlador** (`controllers/`): une los dos y aplica las reglas de cada caso de uso.

**40. ¿Qué ventaja tiene MVC acá?**
Se puede cambiar la interfaz sin tocar la lógica. Por ejemplo, el modo `--consola` usa los mismos modelos y controladores sin la ventana gráfica. También se puede probar cada parte por separado.

**41. ¿Qué hace `main.py`?**
Arma la aplicación: crea los modelos, los controladores y la vista, y los conecta. También acepta `--consola` y `--comparar`.

**42. ¿Dónde se cambian el umbral y otros valores?**
En `config/ajustes.py`: `UMBRAL_SIMILITUD`, `SIMILITUD_SOSPECHOSA`, `CAPTURAS_POR_LECTURA`, `ESPERA_ENTRE_LECTURAS` y el índice de la cámara.

**43. ¿Qué controlador corresponde a cada historia?**
- `enrolamiento_controller`: HU1, y también los rangos.
- `terminal_controller`: HU2/CU1.
- `auditoria_controller`: HU3.
- `dispositivos_controller`: HU4.

**44. ¿Por qué usaron `dlib-bin` en lugar de `dlib`?**
`dlib` normalmente se compila al instalarse, y en Windows eso pide CMake y Visual Studio. `dlib-bin` ya viene compilado. Por eso `face_recognition` se instala con `--no-deps`.

---

## 6. Consigna técnica

**45. ¿Dónde cargan imágenes desde archivos?**
En `models/cargador_imagenes.py`. Se usa en "Usar una foto del disco" y en "Comparar dos imágenes".

**46. ¿Dónde está el registro de asistencia en CSV?**
En `asistencia.csv`, con **nombre, rango, fecha y hora** de cada persona validada, una vez por día. Lo maneja `models/registro_asistencia.py`.

**47. ¿Por qué solo una vez por día?**
Para registrar el **ingreso**, no cada vez que la persona pasa frente a la cámara.

**48. ¿Dónde muestran las imágenes de control y de prueba?**
En "Comparar dos imágenes": las dos fotos lado a lado, con la cara marcada, el veredicto y el porcentaje.

---

## 7. Seguridad y limitaciones (las difíciles)

**49. ¿Se puede engañar al sistema con una foto?**
Sí, es su principal limitación: no tiene **detección de vida** (*liveness*), como pedir parpadear o usar una cámara de profundidad. Sería la primera mejora para producción.

**50. ¿Y con gemelos?**
Probablemente los confundiría: sus vectores quedan muy cerca. Por eso un banco real lo combina con otro factor, como el DNI o un PIN.

**51. ¿Qué afecta la precisión?**
- La luz.
- El ángulo de la cara.
- Anteojos oscuros, barbijo o gorra.
- La calidad de la cámara.
- Una foto de enrolamiento mala.

**52. ¿Por qué 85% y no 99%?**
Es un balance. Un umbral más alto rechaza a más impostores pero también a más personas legítimas (falsos rechazos); uno más bajo hace lo contrario. El 85% lo fija el caso de uso, y se puede cambiar en `ajustes.py`.

**53. ¿Qué es un falso positivo y un falso negativo acá?**
- **Falso positivo:** aceptar a alguien que no es quien dice ser. Es el más grave en un banco.
- **Falso negativo:** rechazar a una persona real. Es molesto, pero tiene la salida del DNI.

**54. ¿Los datos biométricos están protegidos?**
En la demo están en un archivo local sin cifrar. En producción habría que cifrar la base, controlar el acceso y cumplir la ley de protección de datos personales (Ley 25.326 en Argentina), porque la biometría es un dato sensible.

**55. ¿Escala a muchas personas?**
Para cientos o pocos miles, sí: comparar contra todos los vectores con NumPy es rápido. Para millones haría falta un índice de búsqueda de vectores y una base en servidor.

**56. ¿Qué mejorarían?**
- Detección de vida.
- Base en servidor con varias terminales en red.
- Cifrado de la biometría.
- Que el rango también controle permisos: por ejemplo, que solo un Admin pueda cambiar el estado de un dispositivo.
- Usar el detector CNN, más preciso, si hay GPU.

**57. ¿Qué pasa si se cae la cámara en medio de la demo?**
La app sigue funcionando con fotos del disco: el enrolamiento y "Comparar dos imágenes" no necesitan cámara.

---

## 8. Sobre la demo

**58. ¿Por qué este rechazo dio 60% y no 0%?**
Porque dos caras humanas siempre se parecen algo: tienen dos ojos, nariz y boca. La similitud mide cuánto, y el umbral decide.

**59. ¿Qué pasa si cambio el estado de la terminal mientras alguien se está leyendo?**
La app lo detecta en el frame siguiente. Si justo llegara a intentar guardar, el trigger de la base rechaza el INSERT y se muestra "fuera de servicio".

**60. ¿Dónde veo lo que acaba de pasar?**
En la lista de últimas lecturas de la Terminal, en la pantalla Auditoría y en `asistencia.csv`.

---

## 9. Rangos

**61. ¿Qué son los rangos?**
Cada persona enrolada tiene un rango que dice qué es: **Cliente, Admin, Seguridad o Técnico**, o uno que agreguemos nosotros. Cuando la Terminal la reconoce, el cartel verde muestra su rango y la asistencia lo guarda. Por ejemplo, un técnico queda como `Juan Pérez,Técnico,2026-10-29,09:12:40`.

**62. ¿Dónde se guardan?**
En la tabla `rangos` (id y nombre). La tabla `clientes` tiene la columna `id_rango`, que es una clave foránea a esa tabla.

**63. ¿Por qué una tabla aparte y no un texto en `clientes`?**
Para no repetir el nombre en cada persona y evitar variantes escritas distinto ("Tecnico", "técnico", "TÉCNICO"). Además, la lista de rangos sale directo de la tabla para mostrarla en la pantalla. Es normalización.

**64. ¿Cómo se agrega un rango nuevo?**
En Enrolamiento, en el desplegable de rango, se escribe uno que no esté en la lista, por ejemplo "Supervisor". Al dar de alta o tocar **Guardar rango**, se crea y queda disponible para los demás.

**65. ¿Qué pasa si escribo "TÉCNICO" y ya existe "Técnico"?**
Usa el que ya existe, no crea un duplicado. La comparación ignora mayúsculas, incluso con tildes. SQLite solo ignora mayúsculas en letras sin tilde, por eso la comparación se hace en Python con `casefold()`.

**66. ¿Cómo se le cambia el rango a alguien?**
En Enrolamiento se lo busca por DNI (o con un clic en la tabla), se elige el rango nuevo y se toca **Guardar rango**. No hace falta volver a capturar la cara.

**67. Si le cambio el rango a alguien, ¿la Terminal lo toma enseguida?**
Sí. Cuando la Terminal valida a alguien, lee el rango de la base en ese momento, así que usa siempre el actual.

**68. ¿Qué rango tiene alguien si no se elige?**
Cliente. Es el rango por defecto, y también el que reciben las personas que estaban cargadas antes de que existieran los rangos.

**69. ¿Qué pasó con la base y el CSV que ya existían?**
La app los actualiza sola al abrirse. A la base le agrega la columna `id_rango` (`ALTER TABLE`) y pone a todos como Cliente. Al CSV viejo le agrega la columna Rango vacía en las filas anteriores. No se pierden datos.

**70. ¿Dónde más aparece el rango?**
En la tabla de Clientes, en el cartel de bienvenida, en las últimas lecturas de la Terminal, en la Auditoría y en el CSV que se exporta.

**71. ¿El rango da permisos distintos?**
Hoy no: identifica a la persona y queda registrado. Sería la mejora natural: por ejemplo, que la pantalla Dispositivos solo la pueda usar un Admin, o que Seguridad reciba un aviso cuando hay un rechazo sospechoso.

**72. ¿Para qué le sirve al banco saber que entró un técnico?**
Para controlar quién entra además de los clientes: el personal de seguridad y los técnicos que hacen mantenimiento quedan con hora de ingreso en la asistencia, y se puede revisar en la Auditoría.
