import sqlite3

ESTADOS_DISPOSITIVO = ('ACTIVO', 'INACTIVO', 'MANTENIMIENTO')

ESQUEMA = """
CREATE TABLE IF NOT EXISTS sucursales (
    id_sucursal   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL UNIQUE,
    direccion     TEXT
);

CREATE TABLE IF NOT EXISTS dispositivos (
    id_dispositivo INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sucursal    INTEGER NOT NULL REFERENCES sucursales (id_sucursal),
    nombre         TEXT NOT NULL,
    estado         TEXT NOT NULL DEFAULT 'ACTIVO'
                   CHECK (estado IN ('ACTIVO', 'INACTIVO', 'MANTENIMIENTO')),
    UNIQUE (id_sucursal, nombre)
);

-- Rango de cada persona enrolada (Cliente, Admin, Seguridad, Técnico o los que se agreguen)
CREATE TABLE IF NOT EXISTS rangos (
    id_rango INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre   TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    dni        TEXT NOT NULL UNIQUE,
    nombre     TEXT NOT NULL,
    apellido   TEXT NOT NULL,
    id_rango   INTEGER REFERENCES rangos (id_rango)
);

-- UNIQUE en id_cliente: cada persona tiene un solo registro facial vigente (HU1)
CREATE TABLE IF NOT EXISTS biometria_facial (
    id_biometria        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente          INTEGER NOT NULL UNIQUE REFERENCES clientes (id_cliente) ON DELETE CASCADE,
    vector_facial       BLOB NOT NULL,
    fecha_actualizacion TEXT NOT NULL
);

-- id_cliente queda en NULL cuando la lectura es RECHAZADA (CU1, A1)
CREATE TABLE IF NOT EXISTS registro_reconocimiento (
    id_registro     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_dispositivo  INTEGER NOT NULL REFERENCES dispositivos (id_dispositivo),
    id_cliente      INTEGER REFERENCES clientes (id_cliente),
    fecha_hora      TEXT NOT NULL,
    resultado       TEXT NOT NULL CHECK (resultado IN ('EXITOSO', 'RECHAZADO')),
    nivel_similitud REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_registro_fecha ON registro_reconocimiento (fecha_hora);
CREATE INDEX IF NOT EXISTS idx_registro_dispositivo ON registro_reconocimiento (id_dispositivo);

-- HU4: un dispositivo INACTIVO o en MANTENIMIENTO no puede generar transacciones.
-- Lo bloquea la base misma, no solo la aplicación.
CREATE TRIGGER IF NOT EXISTS bloquear_dispositivo_no_activo
BEFORE INSERT ON registro_reconocimiento
WHEN (SELECT estado FROM dispositivos WHERE id_dispositivo = NEW.id_dispositivo) IS NOT 'ACTIVO'
BEGIN
    SELECT RAISE(ABORT, 'El dispositivo no está ACTIVO');
END;
"""

# Sucursales y terminales de ejemplo para la primera vez que se abre la aplicación
DATOS_INICIALES = {
    'Casa Central': [('Terminal 1 - Hall', 'ACTIVO'), ('Terminal 2 - Cajas', 'ACTIVO')],
    'Sucursal Norte': [('Terminal 1', 'ACTIVO')],
    'Sucursal Sur': [('Terminal 1', 'MANTENIMIENTO')],
}

# El primero es el que se asigna si no se elige otro
RANGOS_INICIALES = ('Cliente', 'Admin', 'Seguridad', 'Técnico')
RANGO_POR_DEFECTO = RANGOS_INICIALES[0]


class BaseDatos:
    def __init__(self, ruta):
        self.ruta = ruta
        self.conexion = sqlite3.connect(ruta)
        self.conexion.row_factory = sqlite3.Row
        # SQLite no controla las claves foráneas si no se le pide
        self.conexion.execute('PRAGMA foreign_keys = ON')
        self.conexion.executescript(ESQUEMA)
        self._migrar()
        self._cargar_datos_iniciales()

    def _migrar(self):
        """Agrega id_rango a las bases creadas antes de que existieran los rangos."""
        columnas = [fila['name'] for fila in self.conexion.execute('PRAGMA table_info(clientes)')]
        if 'id_rango' not in columnas:
            with self.conexion:
                self.conexion.execute(
                    'ALTER TABLE clientes ADD COLUMN id_rango INTEGER REFERENCES rangos (id_rango)')

    def _cargar_datos_iniciales(self):
        with self.conexion:
            if not self.conexion.execute('SELECT COUNT(*) FROM rangos').fetchone()[0]:
                self.conexion.executemany('INSERT INTO rangos (nombre) VALUES (?)',
                                          [(rango,) for rango in RANGOS_INICIALES])
            # Quienes no tienen rango (por ejemplo, de antes de la migración) quedan como clientes
            self.conexion.execute(
                'UPDATE clientes SET id_rango = (SELECT id_rango FROM rangos WHERE nombre = ?) '
                'WHERE id_rango IS NULL', (RANGO_POR_DEFECTO,))
        if self.conexion.execute('SELECT COUNT(*) FROM sucursales').fetchone()[0]:
            return
        with self.conexion:
            for sucursal, dispositivos in DATOS_INICIALES.items():
                id_sucursal = self.conexion.execute(
                    'INSERT INTO sucursales (nombre) VALUES (?)', (sucursal,)).lastrowid
                self.conexion.executemany(
                    'INSERT INTO dispositivos (id_sucursal, nombre, estado) VALUES (?, ?, ?)',
                    [(id_sucursal, nombre, estado) for nombre, estado in dispositivos])

    def consultar(self, sql, parametros=()):
        return [dict(fila) for fila in self.conexion.execute(sql, parametros)]

    def consultar_uno(self, sql, parametros=()):
        fila = self.conexion.execute(sql, parametros).fetchone()
        return dict(fila) if fila else None

    def ejecutar(self, sql, parametros=()):
        """Ejecuta un INSERT/UPDATE en su propia transacción. Devuelve el id insertado."""
        with self.conexion:
            return self.conexion.execute(sql, parametros).lastrowid

    def cerrar(self):
        self.conexion.close()
