import argparse

from config import ajustes
from models.base_datos import BaseDatos
from models.cargador_imagenes import CargadorImagenesModel
from models.reconocedor_facial import ReconocedorFacialModel
from models.clientes import ClientesModel
from models.rangos import RangosModel
from models.biometria_facial import BiometriaFacialModel
from models.dispositivos import DispositivosModel
from models.registro_reconocimiento import RegistroReconocimientoModel
from models.registro_asistencia import RegistroAsistenciaModel
from views.interfaz_video import InterfazVideoView
from controllers.app_controller import AplicacionController
from controllers.terminal_controller import TerminalController
from controllers.enrolamiento_controller import EnrolamientoController
from controllers.auditoria_controller import AuditoriaController
from controllers.dispositivos_controller import DispositivosController

def armar_aplicacion():
    # Modelos
    bd = BaseDatos(ajustes.ARCHIVO_BD)
    reconocedor = ReconocedorFacialModel(ajustes.UMBRAL_SIMILITUD, ajustes.TOLERANCIA)
    clientes = ClientesModel(bd)
    biometria = BiometriaFacialModel(bd)
    dispositivos = DispositivosModel(bd)
    registro = RegistroReconocimientoModel(bd)
    asistencia = RegistroAsistenciaModel(ajustes.ARCHIVO_ASISTENCIA)

    # Controladores, con los modelos y la vista inyectados
    app = AplicacionController(CargadorImagenesModel(), reconocedor, biometria, InterfazVideoView(), ajustes)
    app.terminal = TerminalController(app, dispositivos, clientes, registro, asistencia, ajustes)
    app.enrolamiento = EnrolamientoController(clientes, RangosModel(bd), biometria, reconocedor)
    app.auditoria = AuditoriaController(registro, dispositivos, ajustes)
    app.dispositivos = DispositivosController(dispositivos)
    return app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autenticación de clientes por reconocimiento facial.")
    parser.add_argument('--consola', action='store_true',
                        help="Abre la terminal en una ventana de OpenCV, sin la interfaz gráfica.")
    parser.add_argument('--comparar', nargs=2, metavar=('CONTROL', 'PRUEBA'),
                        help="Compara dos imágenes y muestra si son la misma persona.")
    args = parser.parse_args()

    app = armar_aplicacion()

    if args.comparar:
        app.comparar_imagenes(*args.comparar)
    elif args.consola:
        print("Iniciando cámara... Presiona 'q' en la ventana de video para salir.")
        app.iniciar()
    else:
        from views.interfaz_grafica import InterfazGraficaView
        InterfazGraficaView(app).mainloop()
