import os
from datetime import date
from tkinter import filedialog, messagebox, ttk

import cv2
import customtkinter as ctk
from PIL import Image

from models.base_datos import ESTADOS_DISPOSITIVO

# Paleta: cada color va como (modo claro, modo oscuro)
AZUL = ("#2563EB", "#3B82F6")
AZUL_HOVER = ("#1D4ED8", "#2563EB")
VERDE = ("#16A34A", "#22C55E")
VERDE_HOVER = ("#15803D", "#16A34A")
ROJO = ("#DC2626", "#EF4444")
ROJO_HOVER = ("#B91C1C", "#DC2626")
AMBAR = ("#D97706", "#F59E0B")
AMBAR_HOVER = ("#B45309", "#D97706")
GRIS = ("#64748B", "#94A3B8")
GRIS_HOVER = ("#475569", "#64748B")
FONDO = ("#F1F5F9", "#0F172A")
TARJETA = ("#FFFFFF", "#1E293B")
BARRA = ("#FFFFFF", "#111827")
TEXTO_SUAVE = ("#64748B", "#94A3B8")
BOTON_SECUNDARIO = ("#E2E8F0", "#334155")
BOTON_SECUNDARIO_HOVER = ("#CBD5E1", "#475569")
NAV_SELECCIONADO = ("#DBEAFE", "#1E3A8A")
TEXTO_ETIQUETA = ("#1D4ED8", "#BFDBFE")
TEXTO = ("#0F172A", "#F1F5F9")

COLOR_ESTADO = {'ACTIVO': VERDE, 'INACTIVO': GRIS, 'MANTENIMIENTO': AMBAR}

TIPOS_IMAGEN = [("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*")]


def a_imagen_ctk(imagen_bgr, ancho_max, alto_max):
    """Convierte una imagen de OpenCV en CTkImage, achicada para entrar en el espacio dado."""
    alto, ancho = imagen_bgr.shape[:2]
    escala = min(ancho_max / ancho, alto_max / alto)
    tamano = (max(1, int(ancho * escala)), max(1, int(alto * escala)))
    pil = Image.fromarray(cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB))
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=tamano)


def fuente(tamano=13, negrita=False):
    return ctk.CTkFont(family="Segoe UI", size=tamano, weight="bold" if negrita else "normal")


class InterfazGraficaView(ctk.CTk):
    def __init__(self, controlador):
        super().__init__()
        self.app = controlador
        self.tablas = []
        self.camara_activa = False
        self.pagina_camara = None
        self._proximo_frame = None

        ctk.set_appearance_mode("system")
        self.title("Reconocimiento Facial · Sistema bancario")
        self.geometry("1320x800")
        self.minsize(1140, 700)
        self.configure(fg_color=FONDO)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Campos de texto con los colores de la paleta en lugar del gris por defecto
        tema = ctk.ThemeManager.theme
        for widget in ("CTkEntry", "CTkComboBox"):
            tema[widget]["fg_color"] = list(FONDO)
            tema[widget]["border_color"] = list(BOTON_SECUNDARIO)
        tema["CTkComboBox"]["button_color"] = list(BOTON_SECUNDARIO)
        tema["CTkComboBox"]["button_hover_color"] = list(BOTON_SECUNDARIO_HOVER)

        self.estilo = ttk.Style(self)
        self.estilo.theme_use("clam")

        self._armar_barra_lateral()
        self.contenido = ctk.CTkFrame(self, fg_color="transparent")
        self.contenido.grid(row=0, column=1, padx=20, pady=(20, 6), sticky="nsew")
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(0, weight=1)
        self.barra_estado = ctk.CTkLabel(self, text="", font=fuente(12), text_color=TEXTO_SUAVE, anchor="w")
        self.barra_estado.grid(row=1, column=1, padx=26, pady=(0, 12), sticky="ew")

        cantidad = self.app.cargar_clientes()

        self.paginas = {
            'terminal': PaginaTerminal(self.contenido, self),
            'enrolamiento': PaginaEnrolamiento(self.contenido, self),
            'auditoria': PaginaAuditoria(self.contenido, self),
            'dispositivos': PaginaDispositivos(self.contenido, self),
        }
        for pagina in self.paginas.values():
            pagina.grid(row=0, column=0, sticky="nsew")

        self._estilo_tablas(ctk.get_appearance_mode())
        ctk.AppearanceModeTracker.add(self._estilo_tablas, self)
        self.pagina_actual = None
        self.mostrar('terminal')
        self.estado(f"✅  Listo. {cantidad} clientes con biometría registrada.")

    # =====================================================================
    # Barra lateral y navegación
    # =====================================================================
    def _armar_barra_lateral(self):
        barra = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=BARRA)
        barra.grid(row=0, column=0, rowspan=2, sticky="nsw")
        barra.grid_propagate(False)
        barra.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(barra, text="🏦  Biometría", font=fuente(20, True)).grid(
            row=0, column=0, padx=24, pady=(28, 0), sticky="w")
        ctk.CTkLabel(barra, text="Reconocimiento facial bancario", font=fuente(12),
                     text_color=TEXTO_SUAVE).grid(row=1, column=0, padx=26, pady=(0, 20), sticky="w")

        self.botones_nav = {}
        secciones = (
            ("ATENCIÓN", [('terminal', "🖥   Terminal"), ('enrolamiento', "🧑   Enrolamiento")]),
            ("CONTROL", [('auditoria', "🔎   Auditoría"), ('dispositivos', "📟   Dispositivos")]),
        )
        fila = 2
        for titulo, botones in secciones:
            self._etiqueta_grupo(barra, titulo, fila)
            fila += 1
            for clave, texto in botones:
                boton = ctk.CTkButton(
                    barra, text=texto, command=lambda c=clave: self.mostrar(c),
                    height=44, corner_radius=12, font=fuente(14, True), anchor="w", border_spacing=12,
                    fg_color="transparent", hover_color=BOTON_SECUNDARIO, text_color=TEXTO)
                boton.grid(row=fila, column=0, padx=18, pady=3, sticky="ew")
                self.botones_nav[clave] = boton
                fila += 1

        self._etiqueta_grupo(barra, "HERRAMIENTAS", fila)
        self._boton(barra, "⚖   Comparar dos imágenes", self.comparar_imagenes).grid(
            row=fila + 1, column=0, padx=18, pady=4, sticky="ew")
        self._boton_secundario(barra, "📄   Abrir asistencia.csv", self.abrir_csv).grid(
            row=fila + 2, column=0, padx=18, pady=4, sticky="ew")

        barra.grid_rowconfigure(fila + 3, weight=1)
        ctk.CTkLabel(barra, text="Apariencia", font=fuente(12), text_color=TEXTO_SUAVE).grid(
            row=fila + 4, column=0, padx=24, pady=(0, 6), sticky="w")
        modo = ctk.CTkSegmentedButton(
            barra, values=["Claro", "Oscuro", "Sistema"], font=fuente(12),
            command=lambda valor: ctk.set_appearance_mode(
                {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}[valor]),
        )
        modo.set("Sistema")
        modo.grid(row=fila + 5, column=0, padx=18, pady=(0, 24), sticky="ew")

    def _etiqueta_grupo(self, padre, texto, fila):
        ctk.CTkLabel(padre, text=texto, font=fuente(11, True), text_color=TEXTO_SUAVE).grid(
            row=fila, column=0, padx=26, pady=(16, 4), sticky="w")

    def _boton(self, padre, texto, comando, color=AZUL, hover=AZUL_HOVER, texto_color="#FFFFFF", **kwargs):
        opciones = dict(height=44, corner_radius=12, font=fuente(14, True), fg_color=color,
                        hover_color=hover, text_color=texto_color, anchor="w", border_spacing=12)
        opciones.update(kwargs)
        return ctk.CTkButton(padre, text=texto, command=comando, **opciones)

    def _boton_secundario(self, padre, texto, comando, **kwargs):
        return self._boton(padre, texto, comando, BOTON_SECUNDARIO, BOTON_SECUNDARIO_HOVER, TEXTO, **kwargs)

    def mostrar(self, clave):
        if clave == self.pagina_actual:
            return
        # La cámara es de una sola pantalla: al cambiar de sección se apaga
        self.detener_camara()
        for nombre, boton in self.botones_nav.items():
            boton.configure(fg_color=NAV_SELECCIONADO if nombre == clave else "transparent")
        self.pagina_actual = clave
        pagina = self.paginas[clave]
        pagina.tkraise()
        pagina.al_mostrar()

    # =====================================================================
    # Tablas (ttk.Treeview no sigue el tema de CustomTkinter: se pinta a mano)
    # =====================================================================
    def crear_tabla(self, padre, columnas, alto=10):
        """columnas: [(clave, título, ancho, alineación)]. Devuelve (marco, tabla)."""
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings",
                             style="Banco.Treeview", selectmode="browse", height=alto)
        for clave, titulo, ancho, alineacion in columnas:
            tabla.heading(clave, text=titulo, anchor=alineacion)
            tabla.column(clave, width=ancho, minwidth=60, anchor=alineacion, stretch=True)
        barra = ctk.CTkScrollbar(marco, command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y", padx=(4, 0))
        self.tablas.append(tabla)
        return marco, tabla

    def _estilo_tablas(self, modo):
        i = 0 if modo == "Light" else 1
        escala = ctk.ScalingTracker.get_widget_scaling(self)
        fondo, texto, encabezado = TARJETA[i], TEXTO[i], FONDO[i]
        self.estilo.configure("Banco.Treeview", background=fondo, fieldbackground=fondo, foreground=texto,
                              rowheight=int(32 * escala), borderwidth=0, font=("Segoe UI", 10))
        self.estilo.configure("Banco.Treeview.Heading", background=encabezado, foreground=TEXTO_SUAVE[i],
                              relief="flat", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(8, 6))
        self.estilo.map("Banco.Treeview.Heading", background=[("active", encabezado)])
        self.estilo.map("Banco.Treeview", background=[("selected", NAV_SELECCIONADO[i])],
                        foreground=[("selected", texto)])
        self.estilo.layout("Banco.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        for tabla in self.tablas:
            tabla.tag_configure('RECHAZADO', foreground=ROJO[i])
            tabla.tag_configure('SOSPECHOSO', foreground=AMBAR[i])
            tabla.tag_configure('INACTIVO', foreground=GRIS[i])
            tabla.tag_configure('MANTENIMIENTO', foreground=AMBAR[i])
            tabla.tag_configure('SIN_BIOMETRIA', foreground=TEXTO_SUAVE[i])

    # =====================================================================
    # Cámara: la usa la pantalla que la encendió
    # =====================================================================
    def iniciar_camara(self, pagina):
        self.estado("⏳  Encendiendo la cámara…")
        self.update_idletasks()
        if not self.app.abrir_camara():
            self.app.cerrar_camara()
            self.estado("⚠  No se encontró ninguna cámara.")
            messagebox.showerror("Cámara", "No se pudo abrir la cámara. Revisá que esté conectada "
                                           "y que ninguna otra aplicación la esté usando.")
            return False
        self.camara_activa = True
        self.pagina_camara = pagina
        pagina.panel_video.encender()
        self.estado("🎥  Cámara encendida.")
        self._actualizar_video()
        return True

    def detener_camara(self):
        if not self.camara_activa:
            return
        self.camara_activa = False
        self._cancelar_proximo_frame()
        self.app.cerrar_camara()
        pagina, self.pagina_camara = self.pagina_camara, None
        pagina.panel_video.apagar()
        pagina.al_apagar_camara()
        self.estado("Cámara apagada.")

    def _actualizar_video(self):
        if not self.camara_activa:
            return
        frame = self.app.leer_frame()
        if frame is None:
            self.detener_camara()
            self.estado("⚠  Se perdió la señal de la cámara.")
            return
        self.pagina_camara.procesar_frame(frame)
        self.pagina_camara.panel_video.mostrar(frame)
        self._proximo_frame = self.after(15, self._actualizar_video)

    def _cancelar_proximo_frame(self):
        if self._proximo_frame is not None:
            self.after_cancel(self._proximo_frame)
            self._proximo_frame = None

    # =====================================================================
    # Herramientas
    # =====================================================================
    def comparar_imagenes(self):
        control = filedialog.askopenfilename(title="1 de 2 · Elegí la imagen de CONTROL", filetypes=TIPOS_IMAGEN)
        if not control:
            return
        prueba = filedialog.askopenfilename(title="2 de 2 · Elegí la imagen de PRUEBA", filetypes=TIPOS_IMAGEN)
        if not prueba:
            return

        self.estado("⏳  Comparando rostros…")
        self.update_idletasks()
        try:
            resultado = self.app.comparar(control, prueba)
        except (ValueError, IOError) as e:
            self.estado("")
            messagebox.showwarning("Comparar imágenes", str(e))
            return
        self.estado("")
        VentanaComparacion(self, resultado)

    def abrir_csv(self):
        if os.path.exists(self.app.ajustes.ARCHIVO_ASISTENCIA):
            os.startfile(self.app.ajustes.ARCHIVO_ASISTENCIA)

    def estado(self, texto):
        self.barra_estado.configure(text=texto)

    def cerrar(self):
        self.camara_activa = False
        self._cancelar_proximo_frame()
        self.app.cerrar_camara()
        ctk.AppearanceModeTracker.remove(self._estilo_tablas)
        self.destroy()


# =========================================================================
# Piezas comunes
# =========================================================================
class Pagina(ctk.CTkFrame):
    def __init__(self, padre, ventana, titulo, etiqueta, subtitulo):
        super().__init__(padre, fg_color=FONDO, corner_radius=0)
        self.ventana = ventana
        self.app = ventana.app
        self.grid_columnconfigure(0, weight=1)

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        linea = ctk.CTkFrame(encabezado, fg_color="transparent")
        linea.pack(anchor="w")
        ctk.CTkLabel(linea, text=titulo, font=fuente(24, True)).pack(side="left")
        # Qué historia de usuario / caso de uso resuelve la pantalla
        ctk.CTkLabel(linea, text=etiqueta, font=fuente(12, True), fg_color=NAV_SELECCIONADO, text_color=TEXTO_ETIQUETA,
                     corner_radius=8, height=26).pack(side="left", padx=12, ipadx=8)
        ctk.CTkLabel(encabezado, text=subtitulo, font=fuente(13), text_color=TEXTO_SUAVE).pack(anchor="w")

    def tarjeta(self, padre=None, **kwargs):
        return ctk.CTkFrame(padre or self, corner_radius=18, fg_color=TARJETA, **kwargs)

    def titulo_tarjeta(self, padre, texto):
        return ctk.CTkLabel(padre, text=texto, font=fuente(15, True))

    def al_mostrar(self):
        pass

    def procesar_frame(self, frame):
        pass

    def al_apagar_camara(self):
        pass


class PanelVideo(ctk.CTkFrame):
    """Video en vivo con su botón de encendido y un cartel cuando está apagado."""

    def __init__(self, padre, ventana, pagina, titulo, ayuda):
        super().__init__(padre, corner_radius=18, fg_color=TARJETA)
        self.ventana = ventana
        self.pagina = pagina
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")
        encabezado.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(encabezado, text=titulo, font=fuente(15, True)).grid(row=0, column=0, sticky="w")
        self.indicador = ctk.CTkLabel(encabezado, text="●  Apagada", font=fuente(12), text_color=TEXTO_SUAVE)
        self.indicador.grid(row=0, column=1, padx=12)
        self.boton = ventana._boton(encabezado, "▶  Encender cámara", self.alternar, VERDE, VERDE_HOVER,
                                    height=36, width=190, anchor="center", border_spacing=6)
        self.boton.grid(row=0, column=2)

        # El video y el cartel de "cámara apagada" comparten la celda: se muestra uno u otro
        self.contenedor = ctk.CTkFrame(self, corner_radius=14, fg_color=FONDO)
        self.contenedor.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.contenedor.grid_columnconfigure(0, weight=1)
        self.contenedor.grid_rowconfigure(0, weight=1)

        self.cartel = ctk.CTkFrame(self.contenedor, fg_color="transparent")
        self.cartel.grid(row=0, column=0)
        ctk.CTkLabel(self.cartel, text="📷", font=ctk.CTkFont(family="Segoe UI Emoji", size=52),
                     text_color=TEXTO_SUAVE).pack()
        ctk.CTkLabel(self.cartel, text="La cámara está apagada", font=fuente(18, True)).pack(pady=(8, 2))
        ctk.CTkLabel(self.cartel, text=ayuda, font=fuente(13), text_color=TEXTO_SUAVE).pack()
        self.video = ctk.CTkLabel(self.contenedor, text="")

    def alternar(self):
        if self.ventana.camara_activa:
            self.ventana.detener_camara()
        else:
            self.ventana.iniciar_camara(self.pagina)

    def encender(self):
        self.boton.configure(text="■  Apagar cámara", fg_color=ROJO, hover_color=ROJO_HOVER)
        self.indicador.configure(text="●  En vivo", text_color=ROJO)
        self.cartel.grid_remove()
        self.video.grid(row=0, column=0, sticky="nsew")

    def apagar(self):
        self.boton.configure(text="▶  Encender cámara", fg_color=VERDE, hover_color=VERDE_HOVER)
        self.indicador.configure(text="●  Apagada", text_color=TEXTO_SUAVE)
        self.video.grid_remove()
        self.cartel.grid()

    def mostrar(self, frame):
        ancho = max(self.contenedor.winfo_width() - 16, 50)
        alto = max(self.contenedor.winfo_height() - 16, 50)
        self.video.configure(image=a_imagen_ctk(frame, ancho, alto))


class SelectorDispositivo(ctk.CTkFrame):
    """Menú con 'Sucursal · Dispositivo' y una etiqueta con su estado."""

    def __init__(self, padre, al_cambiar):
        super().__init__(padre, fg_color="transparent")
        self.al_cambiar = al_cambiar
        self.opciones = {}
        self.menu = ctk.CTkOptionMenu(self, values=["—"], command=self._elegido, width=300, height=36,
                                      font=fuente(13), dropdown_font=fuente(13), corner_radius=10,
                                      fg_color=AZUL, button_color=AZUL_HOVER, button_hover_color=AZUL_HOVER)
        self.menu.pack(side="left")
        self.etiqueta_estado = ctk.CTkLabel(self, text="", font=fuente(12, True), corner_radius=10,
                                            text_color="#FFFFFF", height=30, width=130)
        self.etiqueta_estado.pack(side="left", padx=10)

    def cargar(self, dispositivos, id_actual=None):
        self.opciones = {f"{d['sucursal']} · {d['nombre']}": d for d in dispositivos}
        if not self.opciones:
            self.menu.configure(values=["Sin dispositivos"])
            self.menu.set("Sin dispositivos")
            return None
        self.menu.configure(values=list(self.opciones))
        elegido = next((d for d in self.opciones.values() if d['id_dispositivo'] == id_actual),
                       next(iter(self.opciones.values())))
        self.menu.set(f"{elegido['sucursal']} · {elegido['nombre']}")
        self.mostrar_estado(elegido['estado'])
        return elegido

    def _elegido(self, texto):
        dispositivo = self.opciones[texto]
        self.mostrar_estado(dispositivo['estado'])
        self.al_cambiar(dispositivo)

    def mostrar_estado(self, estado):
        self.etiqueta_estado.configure(text=estado or "—", fg_color=COLOR_ESTADO.get(estado, GRIS))


# =========================================================================
# HU2 · Caso de uso 1: autenticación en la terminal
# =========================================================================
class PaginaTerminal(Pagina):
    def __init__(self, padre, ventana):
        super().__init__(padre, ventana, "Terminal de atención", "HU2 · Caso de uso 1",
                         "El cliente se ubica frente a la cámara y el sistema valida su identidad.")
        self.ultimos_rostros = []
        self.numero_frame = 0

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(barra, text="Terminal:", font=fuente(13, True)).pack(side="left", padx=(2, 10))
        self.selector = SelectorDispositivo(barra, self._dispositivo_elegido)
        self.selector.pack(side="left")
        ctk.CTkLabel(barra, text=f"Umbral de similitud: {self.app.ajustes.UMBRAL_SIMILITUD:.0%}",
                     font=fuente(12), text_color=TEXTO_SUAVE).pack(side="right", padx=4)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=380)
        self.grid_rowconfigure(2, weight=1)

        self.panel_video = PanelVideo(self, ventana, self, "Cámara de la terminal",
                                      "Encendé la cámara para empezar a atender")
        self.panel_video.grid(row=2, column=0, sticky="nsew", padx=(0, 16))

        derecha = ctk.CTkFrame(self, fg_color="transparent", width=380)
        derecha.grid(row=2, column=1, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(1, weight=1)

        # Cartel grande con lo que ve el cliente
        self.cartel = ctk.CTkFrame(derecha, corner_radius=18, fg_color=TARJETA, height=230)
        self.cartel.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.cartel.grid_propagate(False)
        self.cartel.grid_columnconfigure(0, weight=1)
        self.icono = ctk.CTkLabel(self.cartel, text="", font=ctk.CTkFont(family="Segoe UI Emoji", size=44))
        self.icono.grid(row=0, column=0, pady=(26, 4))
        self.titulo = ctk.CTkLabel(self.cartel, text="", font=fuente(20, True), wraplength=330)
        self.titulo.grid(row=1, column=0, padx=20)
        self.detalle = ctk.CTkLabel(self.cartel, text="", font=fuente(13), wraplength=330, justify="center")
        self.detalle.grid(row=2, column=0, padx=20, pady=(4, 0))
        self.progreso = ctk.CTkProgressBar(self.cartel, height=8, corner_radius=4, progress_color="#FFFFFF")
        self.cartel.grid_rowconfigure(3, weight=1)

        lecturas = self.tarjeta(derecha)
        lecturas.grid(row=1, column=0, sticky="nsew")
        self.titulo_tarjeta(lecturas, "Últimas lecturas de esta terminal").pack(anchor="w", padx=18, pady=(16, 6))
        self.lista = ctk.CTkScrollableFrame(lecturas, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    # --- Estado del cartel --------------------------------------------------
    def _cartel(self, icono, titulo, detalle, color=None, progreso=None):
        texto = "#FFFFFF" if color else TEXTO
        self.cartel.configure(fg_color=color or TARJETA)
        self.icono.configure(text=icono, text_color=texto)
        self.titulo.configure(text=titulo, text_color=texto)
        self.detalle.configure(text=detalle, text_color="#FFFFFF" if color else TEXTO_SUAVE)
        if progreso is None:
            self.progreso.grid_remove()
        else:
            self.progreso.configure(fg_color=AZUL_HOVER)
            self.progreso.set(progreso)
            self.progreso.grid(row=3, column=0, padx=40, pady=(10, 0), sticky="ew")

    def _cartel_segun_estado(self, estado):
        if estado != 'ACTIVO':
            self._cartel("⛔", "Terminal fuera de servicio",
                         f"El dispositivo está en estado {estado}. No se procesan lecturas.", AMBAR)
        elif self.ventana.camara_activa and self.ventana.pagina_camara is self:
            self._cartel("🙂", "Ubíquese frente a la cámara", "La validación es automática.")
        else:
            self._cartel("🖥", "Terminal en espera", "Encendé la cámara para empezar a atender.")

    # --- Eventos --------------------------------------------------------------
    def al_mostrar(self):
        elegido = self.selector.cargar(self.app.dispositivos.listar(), self.app.terminal.id_dispositivo)
        if elegido:
            self.app.terminal.seleccionar(elegido['id_dispositivo'])
            self._cartel_segun_estado(elegido['estado'])
        self.refrescar_lecturas()

    def _dispositivo_elegido(self, dispositivo):
        self.app.terminal.seleccionar(dispositivo['id_dispositivo'])
        self._cartel_segun_estado(dispositivo['estado'])
        self.refrescar_lecturas()

    def al_apagar_camara(self):
        self.ultimos_rostros = []
        # Al volver a encender se empieza de cero, aunque la última persona no se haya retirado
        self.app.terminal.seleccionar(self.app.terminal.id_dispositivo)
        dispositivo = self.app.terminal.dispositivo()
        self._cartel_segun_estado(dispositivo['estado'] if dispositivo else None)

    def procesar_frame(self, frame):
        # Reconocer es lo más costoso: se hace un frame sí y uno no, y en el
        # intermedio se reutilizan los recuadros anteriores.
        if self.numero_frame % 2 == 0:
            lectura = self.app.terminal.procesar(frame)
            self.ultimos_rostros = lectura['rostros']
            self.selector.mostrar_estado(lectura['estado'])
            evento = lectura['evento']
            if evento:
                self._mostrar_evento(evento)
            elif lectura['estado'] != 'ACTIVO':
                self._cartel_segun_estado(lectura['estado'])
            elif lectura['en_pausa']:
                pass  # Sigue el cartel del último resultado hasta que la persona se retire
            elif lectura['progreso']:
                self._cartel("🔍", "Verificando identidad…", "Mire a la cámara, por favor.", AZUL,
                             lectura['progreso'])
            else:
                self._cartel_segun_estado('ACTIVO')
        self.numero_frame += 1
        self.app.vista.dibujar_rostros(frame, self.ultimos_rostros)

    def _mostrar_evento(self, evento):
        hora = evento['fecha_hora'][11:16]
        if evento['resultado'] == 'EXITOSO':
            self._cartel("✔", f"Bienvenido/a, {evento['nombre']}",
                         f"Identidad validada · similitud {evento['similitud']:.0%}", VERDE)
            self.ventana.estado(f"✅  {hora}  EXITOSO: {evento['nombre']} ({evento['similitud']:.0%})")
        else:
            self._cartel("✘", "No pudimos validar su identidad",
                         "Ingrese con su DNI o solicite asistencia al personal.\n"
                         f"Similitud {evento['similitud']:.0%} (mínimo {self.app.ajustes.UMBRAL_SIMILITUD:.0%})",
                         ROJO)
            self.ventana.estado(f"⛔  {hora}  RECHAZADO ({evento['similitud']:.0%})")
        self.refrescar_lecturas()

    def refrescar_lecturas(self):
        for hijo in self.lista.winfo_children():
            hijo.destroy()
        filas = self.app.terminal.ultimas_lecturas()
        if not filas:
            ctk.CTkLabel(self.lista, text="Todavía no hay lecturas en esta terminal.", font=fuente(12),
                         text_color=TEXTO_SUAVE).pack(pady=24)
        for f in filas:
            exitoso = f['resultado'] == 'EXITOSO'
            fila = ctk.CTkFrame(self.lista, corner_radius=10, fg_color=FONDO)
            fila.pack(fill="x", pady=3, padx=2)
            ctk.CTkLabel(fila, text="✔" if exitoso else "✘", width=32, height=32, corner_radius=16,
                         fg_color=VERDE if exitoso else ROJO, text_color="#FFFFFF",
                         font=fuente(13, True)).pack(side="left", padx=10, pady=7)
            nombre = f"{f['nombre']} {f['apellido']}" if exitoso else "Rechazado"
            ctk.CTkLabel(fila, text=nombre, font=fuente(13), anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(fila, text=f"{f['nivel_similitud']:.0%}  ·  {f['fecha_hora'][11:16]}",
                         font=fuente(12), text_color=TEXTO_SUAVE).pack(side="right", padx=12)


# =========================================================================
# HU1 · Caso de uso 2: enrolamiento biométrico
# =========================================================================
class PaginaEnrolamiento(Pagina):
    def __init__(self, padre, ventana):
        super().__init__(padre, ventana, "Enrolamiento biométrico", "HU1 · Caso de uso 2",
                         "El operador busca al cliente por DNI y registra su rostro. "
                         "Se guarda el vector facial, no la foto.")
        self.cliente = None
        self.ultimo_frame = None
        self.ultimos_rostros = []
        self.numero_frame = 0

        self.grid_columnconfigure(0, weight=0, minsize=420)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        izquierda = ctk.CTkFrame(self, fg_color="transparent", width=420)
        izquierda.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        izquierda.grid_columnconfigure(0, weight=1)
        izquierda.grid_rowconfigure(1, weight=1)

        # Paso 1: buscar el cliente
        ficha = self.tarjeta(izquierda)
        ficha.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ficha.grid_columnconfigure(0, weight=1)
        self.titulo_tarjeta(ficha, "1 · Buscar cliente por DNI").grid(row=0, column=0, columnspan=2,
                                                                      padx=18, pady=(16, 8), sticky="w")
        self.entrada_dni = ctk.CTkEntry(ficha, placeholder_text="Ej: 30123456", height=38, font=fuente(14),
                                        corner_radius=10)
        self.entrada_dni.grid(row=1, column=0, padx=(18, 8), sticky="ew")
        self.entrada_dni.bind("<Return>", lambda _: self.buscar())
        ventana._boton(ficha, "Buscar", self.buscar, height=38, width=100, anchor="center",
                       border_spacing=4).grid(row=1, column=1, padx=(0, 18))

        self.datos = ctk.CTkLabel(ficha, text="Ingresá un DNI para empezar.", font=fuente(13),
                                  text_color=TEXTO_SUAVE, justify="left", anchor="w", wraplength=370)
        self.datos.grid(row=2, column=0, columnspan=2, padx=18, pady=(12, 4), sticky="ew")

        # Alta del cliente si no existe (precondición del caso de uso 2)
        self.alta = ctk.CTkFrame(ficha, fg_color="transparent")
        self.alta.grid_columnconfigure((0, 1), weight=1)
        self.entrada_nombre = ctk.CTkEntry(self.alta, placeholder_text="Nombre", height=36, corner_radius=10)
        self.entrada_nombre.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        self.entrada_apellido = ctk.CTkEntry(self.alta, placeholder_text="Apellido", height=36, corner_radius=10)
        self.entrada_apellido.grid(row=0, column=1, padx=(4, 0), sticky="ew")
        ventana._boton_secundario(self.alta, "＋  Dar de alta al cliente", self.dar_de_alta, height=36,
                                  anchor="center").grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")

        # Paso 2: capturar el rostro
        self.titulo_tarjeta(ficha, "2 · Capturar el rostro").grid(row=4, column=0, columnspan=2,
                                                                  padx=18, pady=(16, 8), sticky="w")
        self.boton_camara = ventana._boton(ficha, "📸   Capturar con la cámara", self.capturar_desde_camara)
        self.boton_camara.grid(row=5, column=0, columnspan=2, padx=18, pady=3, sticky="ew")
        self.boton_foto = ventana._boton_secundario(ficha, "🖼   Usar una foto del disco", self.capturar_desde_archivo)
        self.boton_foto.grid(row=6, column=0, columnspan=2, padx=18, pady=(3, 18), sticky="ew")

        clientes = self.tarjeta(izquierda)
        clientes.grid(row=1, column=0, sticky="nsew")
        self.titulo_tarjeta(clientes, "Clientes").pack(anchor="w", padx=18, pady=(16, 8))
        marco, self.tabla = ventana.crear_tabla(clientes, [
            ('dni', "DNI", 90, "w"), ('cliente', "Cliente", 160, "w"), ('biometria', "Biometría", 120, "w")])
        marco.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tabla.bind("<<TreeviewSelect>>", self._cliente_elegido)

        self.panel_video = PanelVideo(self, ventana, self, "Cámara de enrolamiento",
                                      "Encendela para capturar el rostro del cliente")
        self.panel_video.grid(row=1, column=1, sticky="nsew")
        self._habilitar_captura()

    def al_mostrar(self):
        self.refrescar_clientes()

    def refrescar_clientes(self):
        self.tabla.delete(*self.tabla.get_children())
        for c in self.app.enrolamiento.listar_clientes():
            fecha = c['fecha_actualizacion']
            self.tabla.insert("", "end", iid=c['dni'], tags=() if fecha else ('SIN_BIOMETRIA',),
                              values=(c['dni'], f"{c['apellido']}, {c['nombre']}",
                                      fecha[:16] if fecha else "Sin registrar"))

    def _cliente_elegido(self, _):
        seleccion = self.tabla.selection()
        if seleccion and (not self.cliente or self.cliente['dni'] != seleccion[0]):
            self.entrada_dni.delete(0, "end")
            self.entrada_dni.insert(0, seleccion[0])
            self.buscar()

    def _habilitar_captura(self):
        estado = "normal" if self.cliente else "disabled"
        self.boton_camara.configure(state=estado)
        self.boton_foto.configure(state=estado)

    def buscar(self):
        self.alta.grid_remove()
        try:
            self.cliente = self.app.enrolamiento.buscar(self.entrada_dni.get())
        except ValueError as e:
            self.cliente = None
            self.datos.configure(text=f"⚠  {e}", text_color=ROJO)
            self._habilitar_captura()
            return
        if self.cliente:
            self._mostrar_cliente()
        else:
            self.datos.configure(text="No existe un cliente con ese DNI. Podés darlo de alta:", text_color=AMBAR)
            self.alta.grid(row=3, column=0, columnspan=2, padx=18, pady=(4, 0), sticky="ew")
        self._habilitar_captura()

    def _mostrar_cliente(self):
        c = self.cliente
        if c['fecha_actualizacion']:
            biometria = f"Biometría vigente desde {c['fecha_actualizacion'][:16]}. Capturar de nuevo la reemplaza."
        else:
            biometria = "Sin biometría registrada."
        self.datos.configure(text=f"✔  {c['nombre']} {c['apellido']}  ·  DNI {c['dni']}\n{biometria}",
                             text_color=TEXTO)

    def dar_de_alta(self):
        try:
            self.cliente = self.app.enrolamiento.crear_cliente(
                self.entrada_dni.get(), self.entrada_nombre.get(), self.entrada_apellido.get())
        except ValueError as e:
            messagebox.showwarning("Alta de cliente", str(e))
            return
        self.alta.grid_remove()
        self.entrada_nombre.delete(0, "end")
        self.entrada_apellido.delete(0, "end")
        self._mostrar_cliente()
        self._habilitar_captura()
        self.refrescar_clientes()
        self.ventana.estado(f"✅  Cliente {self.cliente['nombre']} {self.cliente['apellido']} dado de alta.")

    def _enrolar(self, imagen_bgr):
        try:
            resultado = self.app.enrolamiento.enrolar(self.cliente['dni'], imagen_bgr)
        except (ValueError, IOError) as e:
            messagebox.showwarning("No se pudo registrar", str(e))
            return
        self.cliente['fecha_actualizacion'] = resultado['fecha_actualizacion']
        self._mostrar_cliente()
        self.refrescar_clientes()
        accion = "actualizado" if resultado['actualizado'] else "activado"
        self.ventana.estado(f"✅  Perfil biométrico de {resultado['nombre']} {accion} "
                            f"({resultado['fecha_actualizacion'][11:16]}).")
        messagebox.showinfo("Enrolamiento", f"Perfil biométrico de {resultado['nombre']} {accion} correctamente.")

    def capturar_desde_camara(self):
        if self.ventana.pagina_camara is not self or self.ultimo_frame is None:
            messagebox.showinfo("Capturar con la cámara",
                                "Primero encendé la cámara de enrolamiento y ubicá al cliente de frente.")
            return
        self._enrolar(self.ultimo_frame.copy())

    def capturar_desde_archivo(self):
        ruta = filedialog.askopenfilename(title="Elegí la foto del cliente", filetypes=TIPOS_IMAGEN)
        if not ruta:
            return
        try:
            imagen = self.app.cargador.leer_archivo(ruta)
        except IOError as e:
            messagebox.showerror("Foto", str(e))
            return
        self._enrolar(imagen)

    def procesar_frame(self, frame):
        self.ultimo_frame = frame.copy()
        # Marca si hay exactamente un rostro, que es lo que pide el enrolamiento
        if self.numero_frame % 3 == 0:
            rostros = self.app.detectar(frame)
            uno = len(rostros) == 1
            etiqueta = "Listo para capturar" if uno else "Una sola persona"
            self.ultimos_rostros = [(ubicacion, etiqueta, uno) for ubicacion, _ in rostros]
        self.numero_frame += 1
        self.app.vista.dibujar_rostros(frame, self.ultimos_rostros)

    def al_apagar_camara(self):
        self.ultimo_frame = None
        self.ultimos_rostros = []


# =========================================================================
# HU3: auditoría de lecturas
# =========================================================================
class PaginaAuditoria(Pagina):
    TODAS = "Todas"
    TODOS = "Todos"

    def __init__(self, padre, ventana):
        super().__init__(padre, ventana, "Auditoría de lecturas", "HU3",
                         "Historial de autenticaciones por sucursal, dispositivo y rango horario.")
        self.filas = []
        self.sucursales = {}
        self.dispositivos = {}
        self.grid_rowconfigure(3, weight=1)

        filtros = self.tarjeta()
        filtros.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for columna, texto in enumerate(("Sucursal", "Dispositivo", "Desde", "Hasta")):
            ctk.CTkLabel(filtros, text=texto, font=fuente(12, True), text_color=TEXTO_SUAVE).grid(
                row=0, column=columna, padx=(18 if columna == 0 else 6, 6), pady=(14, 2), sticky="w")
        self.menu_sucursal = ctk.CTkOptionMenu(filtros, values=[self.TODAS], width=200, height=34,
                                               command=lambda _: self._cargar_dispositivos(), **self._estilo_menu())
        self.menu_sucursal.grid(row=1, column=0, padx=(18, 6), sticky="w")
        self.menu_dispositivo = ctk.CTkOptionMenu(filtros, values=[self.TODOS], width=220, height=34,
                                                  **self._estilo_menu())
        self.menu_dispositivo.grid(row=1, column=1, padx=6, sticky="w")
        hoy = date.today().isoformat()
        self.entrada_desde = ctk.CTkEntry(filtros, width=160, height=34, corner_radius=10,
                                          placeholder_text="AAAA-MM-DD HH:MM")
        self.entrada_desde.insert(0, f"{hoy} 00:00")
        self.entrada_desde.grid(row=1, column=2, padx=6, sticky="w")
        self.entrada_hasta = ctk.CTkEntry(filtros, width=160, height=34, corner_radius=10,
                                          placeholder_text="AAAA-MM-DD HH:MM")
        self.entrada_hasta.insert(0, f"{hoy} 23:59")
        self.entrada_hasta.grid(row=1, column=3, padx=6, sticky="w")

        segunda = ctk.CTkFrame(filtros, fg_color="transparent")
        segunda.grid(row=2, column=0, columnspan=6, padx=18, pady=(12, 14), sticky="ew")
        self.resultado = ctk.CTkSegmentedButton(segunda, values=["Todos", "Exitosos", "Rechazados"],
                                                font=fuente(12), height=34, selected_color=AZUL,
                                                selected_hover_color=AZUL_HOVER, command=lambda _: self.buscar())
        self.resultado.set("Todos")
        self.resultado.pack(side="left")
        self.sospechosos = ctk.CTkCheckBox(
            segunda, font=fuente(12), command=self.buscar,
            text=f"Solo rechazos con similitud alta (≥ {self.app.ajustes.SIMILITUD_SOSPECHOSA:.0%})")
        self.sospechosos.pack(side="left", padx=16)
        ventana._boton_secundario(segunda, "⬇  Exportar CSV", self.exportar, height=34, width=140,
                                  anchor="center", border_spacing=4).pack(side="right")
        ventana._boton(segunda, "🔎  Buscar", self.buscar, height=34, width=120, anchor="center",
                       border_spacing=4).pack(side="right", padx=8)

        totales = ctk.CTkFrame(self, fg_color="transparent")
        totales.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        totales.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="t")
        self.total = self._dato(totales, "Lecturas", 0, AZUL)
        self.total_exitosos = self._dato(totales, "Exitosas", 1, VERDE)
        self.total_rechazados = self._dato(totales, "Rechazadas", 2, ROJO)
        self.total_sospechosos = self._dato(totales, "Rechazos sospechosos", 3, AMBAR)

        tabla = self.tarjeta()
        tabla.grid(row=3, column=0, sticky="nsew")
        marco, self.tabla = ventana.crear_tabla(tabla, [
            ('fecha', "Fecha y hora", 150, "w"), ('sucursal', "Sucursal", 140, "w"),
            ('dispositivo', "Dispositivo", 150, "w"), ('dni', "DNI", 90, "w"),
            ('cliente', "Cliente", 170, "w"), ('resultado', "Resultado", 110, "w"),
            ('similitud', "Similitud", 90, "e")])
        marco.pack(fill="both", expand=True, padx=14, pady=14)

    def _estilo_menu(self):
        return dict(font=fuente(13), dropdown_font=fuente(13), corner_radius=10, fg_color=BOTON_SECUNDARIO,
                    button_color=BOTON_SECUNDARIO_HOVER, button_hover_color=BOTON_SECUNDARIO_HOVER,
                    text_color=TEXTO)

    def _dato(self, padre, titulo, columna, color):
        tarjeta = self.tarjeta(padre)
        tarjeta.grid(row=0, column=columna, padx=(0 if columna == 0 else 6, 0 if columna == 3 else 6), sticky="ew")
        valor = ctk.CTkLabel(tarjeta, text="0", font=fuente(26, True), text_color=color)
        valor.pack(padx=18, pady=(10, 0), anchor="w")
        ctk.CTkLabel(tarjeta, text=titulo, font=fuente(12), text_color=TEXTO_SUAVE).pack(
            padx=18, pady=(0, 10), anchor="w")
        return valor

    def al_mostrar(self):
        self.sucursales = {s['nombre']: s['id_sucursal'] for s in self.app.dispositivos.sucursales()}
        actual = self.menu_sucursal.get()
        self.menu_sucursal.configure(values=[self.TODAS] + list(self.sucursales))
        if actual not in self.sucursales:
            self.menu_sucursal.set(self.TODAS)
        self._cargar_dispositivos()

    def _cargar_dispositivos(self):
        id_sucursal = self.sucursales.get(self.menu_sucursal.get())
        self.dispositivos = {
            (d['nombre'] if id_sucursal else f"{d['sucursal']} · {d['nombre']}"): d['id_dispositivo']
            for d in self.app.dispositivos.listar() if id_sucursal in (None, d['id_sucursal'])}
        actual = self.menu_dispositivo.get()
        self.menu_dispositivo.configure(values=[self.TODOS] + list(self.dispositivos))
        if actual not in self.dispositivos:
            self.menu_dispositivo.set(self.TODOS)
        self.buscar()

    def buscar(self):
        resultado = {"Exitosos": 'EXITOSO', "Rechazados": 'RECHAZADO'}.get(self.resultado.get())
        try:
            self.filas = self.app.auditoria.reporte(
                id_sucursal=self.sucursales.get(self.menu_sucursal.get()),
                id_dispositivo=self.dispositivos.get(self.menu_dispositivo.get()),
                desde=self.entrada_desde.get(), hasta=self.entrada_hasta.get(),
                resultado=resultado, solo_sospechosos=bool(self.sospechosos.get()))
        except ValueError as e:
            messagebox.showwarning("Auditoría", str(e))
            return

        umbral_sospecha = self.app.ajustes.SIMILITUD_SOSPECHOSA
        self.tabla.delete(*self.tabla.get_children())
        contadores = {'EXITOSO': 0, 'RECHAZADO': 0, 'SOSPECHOSO': 0}
        for f in self.filas:
            etiqueta = f['resultado']
            contadores[etiqueta] += 1
            if etiqueta == 'RECHAZADO' and f['nivel_similitud'] >= umbral_sospecha:
                etiqueta = 'SOSPECHOSO'
                contadores['SOSPECHOSO'] += 1
            cliente = f"{f['apellido']}, {f['nombre']}" if f['dni'] else "—"
            self.tabla.insert("", "end", tags=(etiqueta,), values=(
                f['fecha_hora'], f['sucursal'], f['dispositivo'], f['dni'] or "—", cliente,
                f['resultado'], f"{f['nivel_similitud']:.0%}"))

        self.total.configure(text=str(len(self.filas)))
        self.total_exitosos.configure(text=str(contadores['EXITOSO']))
        self.total_rechazados.configure(text=str(contadores['RECHAZADO']))
        self.total_sospechosos.configure(text=str(contadores['SOSPECHOSO']))

    def exportar(self):
        if not self.filas:
            messagebox.showinfo("Exportar", "No hay lecturas para exportar con estos filtros.")
            return
        ruta = filedialog.asksaveasfilename(title="Guardar reporte", defaultextension=".csv",
                                            initialfile=f"auditoria_{date.today().isoformat()}.csv",
                                            filetypes=[("CSV", "*.csv")])
        if ruta:
            self.app.auditoria.exportar_csv(self.filas, ruta)
            self.ventana.estado(f"✅  Reporte exportado: {ruta}")


# =========================================================================
# HU4: gestión de dispositivos
# =========================================================================
class PaginaDispositivos(Pagina):
    def __init__(self, padre, ventana):
        super().__init__(padre, ventana, "Dispositivos", "HU4",
                         "Terminales de cada sucursal. Las que no están ACTIVAS no pueden registrar lecturas.")
        self.dispositivos = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=360)
        self.grid_rowconfigure(1, weight=1)

        lista = self.tarjeta()
        lista.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self.titulo_tarjeta(lista, "Dispositivos por sucursal").pack(anchor="w", padx=18, pady=(16, 8))
        marco, self.tabla = ventana.crear_tabla(lista, [
            ('sucursal', "Sucursal", 160, "w"), ('dispositivo', "Dispositivo", 180, "w"),
            ('estado', "Estado", 130, "w"), ('lecturas', "Lecturas hoy", 100, "e")])
        marco.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tabla.bind("<<TreeviewSelect>>", lambda _: self._mostrar_seleccion())

        derecha = ctk.CTkFrame(self, fg_color="transparent", width=360)
        derecha.grid(row=1, column=1, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)

        estado = self.tarjeta(derecha)
        estado.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        estado.grid_columnconfigure(0, weight=1)
        self.titulo_tarjeta(estado, "Cambiar estado").grid(row=0, column=0, padx=18, pady=(16, 4), sticky="w")
        self.seleccion = ctk.CTkLabel(estado, text="Elegí un dispositivo de la lista.", font=fuente(13),
                                      text_color=TEXTO_SUAVE, wraplength=320, justify="left", anchor="w")
        self.seleccion.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.botones_estado = {}
        for fila, (valor, texto, color, hover) in enumerate((
                ('ACTIVO', "✔   Activo", VERDE, VERDE_HOVER),
                ('MANTENIMIENTO', "🛠   En mantenimiento", AMBAR, AMBAR_HOVER),
                ('INACTIVO', "⏻   Inactivo", GRIS, GRIS_HOVER)), start=2):
            boton = ventana._boton(estado, texto, lambda v=valor: self.cambiar_estado(v), color, hover, height=40)
            boton.grid(row=fila, column=0, padx=18, pady=3, sticky="ew")
            self.botones_estado[valor] = boton
        ctk.CTkLabel(estado, text="Un dispositivo INACTIVO o en MANTENIMIENTO no puede registrar lecturas: "
                                  "lo bloquea un trigger de la base de datos.",
                     font=fuente(12), text_color=TEXTO_SUAVE, wraplength=320, justify="left").grid(
            row=5, column=0, padx=18, pady=(10, 16), sticky="w")

        nuevo = self.tarjeta(derecha)
        nuevo.grid(row=1, column=0, sticky="ew")
        nuevo.grid_columnconfigure(0, weight=1)
        self.titulo_tarjeta(nuevo, "Nuevo dispositivo").grid(row=0, column=0, padx=18, pady=(16, 8), sticky="w")
        self.combo_sucursal = ctk.CTkComboBox(nuevo, values=[], height=36, corner_radius=10, font=fuente(13))
        self.combo_sucursal.set("")
        self.combo_sucursal.grid(row=1, column=0, padx=18, pady=3, sticky="ew")
        self.entrada_nombre = ctk.CTkEntry(nuevo, placeholder_text="Nombre (ej: Terminal 3 - Cajas)",
                                           height=36, corner_radius=10, font=fuente(13))
        self.entrada_nombre.grid(row=2, column=0, padx=18, pady=3, sticky="ew")
        ctk.CTkLabel(nuevo, text="Si escribís una sucursal que no existe, se crea.", font=fuente(12),
                     text_color=TEXTO_SUAVE).grid(row=3, column=0, padx=18, sticky="w")
        ventana._boton(nuevo, "＋  Agregar dispositivo", self.agregar, height=40, anchor="center").grid(
            row=4, column=0, padx=18, pady=(8, 18), sticky="ew")
        self._habilitar_botones(None)

    def al_mostrar(self):
        self.refrescar()

    def refrescar(self, seleccionar=None):
        seleccionar = seleccionar or (self.tabla.selection() or [None])[0]
        hoy = date.today().isoformat()
        lecturas = {}
        for f in self.app.auditoria.reporte(desde=hoy, hasta=hoy):
            lecturas[f['id_dispositivo']] = lecturas.get(f['id_dispositivo'], 0) + 1

        self.tabla.delete(*self.tabla.get_children())
        self.dispositivos = {}
        for d in self.app.dispositivos.listar():
            iid = str(d['id_dispositivo'])
            self.dispositivos[iid] = d
            self.tabla.insert("", "end", iid=iid, tags=(d['estado'],), values=(
                d['sucursal'], d['nombre'], d['estado'], lecturas.get(d['id_dispositivo'], 0)))
        if seleccionar in self.dispositivos:
            self.tabla.selection_set(seleccionar)
        self._mostrar_seleccion()

        sucursales = [s['nombre'] for s in self.app.dispositivos.sucursales()]
        self.combo_sucursal.configure(values=sucursales)
        if not self.combo_sucursal.get() and sucursales:
            self.combo_sucursal.set(sucursales[0])

    def _seleccionado(self):
        seleccion = self.tabla.selection()
        return self.dispositivos.get(seleccion[0]) if seleccion else None

    def _mostrar_seleccion(self):
        d = self._seleccionado()
        if d:
            self.seleccion.configure(text=f"{d['sucursal']} · {d['nombre']}\nEstado actual: {d['estado']}",
                                     text_color=TEXTO)
        else:
            self.seleccion.configure(text="Elegí un dispositivo de la lista.", text_color=TEXTO_SUAVE)
        self._habilitar_botones(d)

    def _habilitar_botones(self, dispositivo):
        for valor, boton in self.botones_estado.items():
            boton.configure(state="normal" if dispositivo and dispositivo['estado'] != valor else "disabled")

    def cambiar_estado(self, estado):
        d = self._seleccionado()
        if not d or estado not in ESTADOS_DISPOSITIVO:
            return
        self.app.dispositivos.cambiar_estado(d['id_dispositivo'], estado)
        self.refrescar(str(d['id_dispositivo']))
        self.ventana.estado(f"✅  {d['sucursal']} · {d['nombre']} pasó a {estado}.")

    def agregar(self):
        try:
            id_dispositivo = self.app.dispositivos.crear(self.combo_sucursal.get(), self.entrada_nombre.get())
        except ValueError as e:
            messagebox.showwarning("Nuevo dispositivo", str(e))
            return
        self.entrada_nombre.delete(0, "end")
        self.refrescar(str(id_dispositivo))
        self.ventana.estado("✅  Dispositivo agregado en estado ACTIVO.")


class VentanaComparacion(ctk.CTkToplevel):
    """Muestra la imagen de control y la de prueba lado a lado con el resultado."""

    def __init__(self, padre, resultado):
        super().__init__(padre)
        self.title("Comparación de rostros")
        self.geometry("980x720")
        self.minsize(800, 600)
        self.configure(fg_color=FONDO)
        self.transient(padre)

        misma = resultado['misma_persona']

        # Cartel con el veredicto
        cartel = ctk.CTkFrame(self, corner_radius=16, fg_color=VERDE if misma else ROJO)
        cartel.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(cartel, text="✔  Es la misma persona" if misma else "✘  Son personas distintas",
                     font=fuente(22, True), text_color="#FFFFFF").pack(pady=(14, 0))
        ctk.CTkLabel(cartel,
                     text=f"Similitud: {resultado['similitud']:.0%}   ·   Umbral: {resultado['umbral']:.0%}   ·   "
                          f"Distancia entre rostros: {resultado['distancia']:.2f}",
                     font=fuente(13), text_color="#FFFFFF").pack(pady=(2, 14))

        # El botón se empaqueta antes que las imágenes para que nunca quede afuera de la ventana
        ctk.CTkButton(self, text="Cerrar", command=self.destroy, width=160, height=40, corner_radius=12,
                      font=fuente(14, True), fg_color=AZUL, hover_color=AZUL_HOVER).pack(side="bottom", pady=18)

        imagenes = ctk.CTkFrame(self, fg_color="transparent")
        imagenes.pack(fill="both", expand=True, padx=18)
        imagenes.grid_columnconfigure((0, 1), weight=1, uniform="col")
        imagenes.grid_rowconfigure(0, weight=1)

        for columna, (titulo, clave) in enumerate((("Imagen de control", 'control'),
                                                   ("Imagen de prueba", 'prueba'))):
            tarjeta = ctk.CTkFrame(imagenes, corner_radius=16, fg_color=TARJETA)
            tarjeta.grid(row=0, column=columna, padx=6, sticky="nsew")
            ctk.CTkLabel(tarjeta, text=titulo, font=fuente(15, True)).pack(pady=(14, 8))
            ctk.CTkLabel(tarjeta, text="", image=a_imagen_ctk(resultado[clave], 430, 400)).pack(
                padx=14, pady=(0, 14), expand=True)

        # En Windows la ventana nueva a veces aparece detrás de la principal
        self.after(100, self.lift)
        self.after(150, self.focus_force)
