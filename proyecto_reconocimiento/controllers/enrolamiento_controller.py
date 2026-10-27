import sqlite3

import cv2

def normalizar_dni(dni):
    """Saca puntos y espacios ("30.123.456" -> "30123456"). Lanza ValueError si no es un DNI."""
    dni = ''.join(c for c in dni if c not in '. -')
    if not dni.isdigit() or not 7 <= len(dni) <= 8:
        raise ValueError("El DNI tiene que tener 7 u 8 números.")
    return dni


class EnrolamientoController:
    """Caso de uso 2 / HU1: el operador registra la biometría facial de un cliente."""

    def __init__(self, clientes, biometria, reconocedor):
        self.clientes = clientes
        self.biometria = biometria
        self.reconocedor = reconocedor

    def buscar(self, dni):
        """Devuelve el cliente con la fecha de su biometría, o None si no existe."""
        cliente = self.clientes.buscar_por_dni(normalizar_dni(dni))
        if cliente:
            cliente['fecha_actualizacion'] = self.biometria.obtener_fecha(cliente['id_cliente'])
        return cliente

    def crear_cliente(self, dni, nombre, apellido):
        dni = normalizar_dni(dni)
        nombre, apellido = nombre.strip().title(), apellido.strip().title()
        if not nombre or not apellido:
            raise ValueError("Completá el nombre y el apellido.")
        try:
            self.clientes.crear(dni, nombre, apellido)
        except sqlite3.IntegrityError:
            raise ValueError(f"Ya existe un cliente con DNI {dni}.")
        return self.buscar(dni)

    def listar_clientes(self):
        return self.clientes.listar()

    def enrolar(self, dni, imagen_bgr):
        """Genera el vector facial del cliente y lo guarda en biometria_facial.

        La imagen tiene que tener un solo rostro. Lanza ValueError con un mensaje
        para mostrarle al operador si algo no está bien.
        """
        # HU1: el cliente tiene que existir antes de registrar su biometría
        cliente = self.clientes.buscar_por_dni(normalizar_dni(dni))
        if not cliente:
            raise ValueError("No existe un cliente con ese DNI.")

        imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
        ubicaciones = self.reconocedor.localizar_rostros(imagen_rgb)
        if not ubicaciones:
            raise ValueError("No se encontró ningún rostro en la imagen.")
        if len(ubicaciones) > 1:
            raise ValueError("Hay más de un rostro: tiene que haber una sola persona.")

        vector = self.reconocedor.codificar_rostros(imagen_rgb, ubicaciones)[0]
        fecha, actualizado = self.biometria.guardar(cliente['id_cliente'], vector)
        nombre = f"{cliente['nombre']} {cliente['apellido']}"
        self.reconocedor.actualizar_cliente(cliente['id_cliente'], nombre, vector)
        return {'cliente': cliente, 'nombre': nombre, 'fecha_actualizacion': fecha,
                'actualizado': actualizado}
