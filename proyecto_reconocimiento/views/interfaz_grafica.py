import os
import threading
from datetime import datetime
from tkinter import filedialog, messagebox

import cv2
import customtkinter as ctk
from PIL import Image

# Paleta: cada color va como (modo claro, modo oscuro)
AZUL = ("#2563EB", "#3B82F6")
AZUL_HOVER = ("#1D4ED8", "#2563EB")
VERDE = ("#16A34A", "#22C55E")
VERDE_HOVER = ("#15803D", "#16A34A")
ROJO = ("#DC2626", "#EF4444")
ROJO_HOVER = ("#B91C1C", "#DC2626")
FONDO = ("#F1F5F9", "#0F172A")
TARJETA = ("#FFFFFF", "#1E293B")
BARRA = ("#FFFFFF", "#111827")
TEXTO_SUAVE = ("#64748B", "#94A3B8")
BOTON_SECUNDARIO = ("#E2E8F0", "#334155")
BOTON_SECUNDARIO_HOVER = ("#CBD5E1", "#475569")
TEXTO = ("#0F172A", "#F1F5F9")

TIPOS_IMAGEN = [("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*")]


def a_imagen_ctk(imagen_bgr, ancho_max, alto_max):
    """Convierte una imagen de OpenCV en CTkImage, achicada para entrar en el espacio dado."""
    alto, ancho = imagen_bgr.shape[:2]
    escala = min(ancho_max / ancho, alto_max / alto)
    tamano = (max(1, int(ancho * escala)), max(1, int(alto * escala)))
    pil = Image.fromarray(cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB))
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=tamano)


class InterfazGraficaView(ctk.CTk):
    def __init__(self, controlador):
        super().__init__()
        self.app = controlador
        self.camara_activa = False
        self.ultimo_frame = None
        self.ultimos_rostros = []
        self.numero_frame = 0
        self._proximo_frame = None

        ctk.set_appearance_mode("system")
        self.title("Asistencia por Reconocimiento Facial")
        self.geometry("1280x760")
        self.minsize(1080, 640)
        self.configure(fg_color=FONDO)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.fuente_titulo = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.fuente_seccion = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        self.fuente_boton = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.fuente = ctk.CTkFont(family="Segoe UI", size=13)
        self.fuente_chica = ctk.CTkFont(family="Segoe UI", size=12)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._armar_barra_lateral()
        self._armar_panel_video()
        self._armar_panel_derecho()
        self._armar_barra_estado()

        self._cargar_empleados_en_segundo_plano()

    # =====================================================================
    # Armado de la pantalla
    # =====================================================================
    def _boton(self, padre, texto, comando, color=AZUL, hover=AZUL_HOVER, texto_color="#FFFFFF"):
        return ctk.CTkButton(
            padre, text=texto, command=comando, height=46, corner_radius=12,
            font=self.fuente_boton, fg_color=color, hover_color=hover,
            text_color=texto_color, anchor="w", border_spacing=12,
        )

    def _boton_secundario(self, padre, texto, comando):
        return self._boton(padre, texto, comando, BOTON_SECUNDARIO, BOTON_SECUNDARIO_HOVER, TEXTO)

    def _armar_barra_lateral(self):
        barra = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=BARRA)
        barra.grid(row=0, column=0, rowspan=2, sticky="nsw")
        barra.grid_propagate(False)
        barra.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(barra, text="🛡  Asistencia", font=self.fuente_titulo).grid(
            row=0, column=0, padx=24, pady=(28, 0), sticky="w")
        ctk.CTkLabel(barra, text="Reconocimiento facial", font=self.fuente_chica,
                     text_color=TEXTO_SUAVE).grid(row=1, column=0, padx=26, pady=(0, 24), sticky="w")

        self._etiqueta_grupo(barra, "CÁMARA", 2)
        self.boton_camara = self._boton(barra, "▶   Iniciar cámara", self.alternar_camara, VERDE, VERDE_HOVER)
        self.boton_camara.grid(row=3, column=0, padx=18, pady=4, sticky="ew")
        self.boton_camara.configure(state="disabled")

        self._etiqueta_grupo(barra, "EMPLEADOS", 4)
        self.boton_capturar = self._boton(barra, "📸   Registrar con la cámara", self.registrar_desde_camara)
        self.boton_capturar.grid(row=5, column=0, padx=18, pady=4, sticky="ew")
        self._boton(barra, "🖼   Agregar desde una foto", self.registrar_desde_archivo).grid(
            row=6, column=0, padx=18, pady=4, sticky="ew")

        self._etiqueta_grupo(barra, "HERRAMIENTAS", 7)
        self._boton(barra, "⚖   Comparar dos imágenes", self.comparar_imagenes).grid(
            row=8, column=0, padx=18, pady=4, sticky="ew")
        self._boton_secundario(barra, "📁   Carpeta de empleados", self.abrir_carpeta_empleados).grid(
            row=9, column=0, padx=18, pady=4, sticky="ew")
        self._boton_secundario(barra, "📄   Abrir asistencia.csv", self.abrir_csv).grid(
            row=10, column=0, padx=18, pady=4, sticky="ew")

        barra.grid_rowconfigure(11, weight=1)

        ctk.CTkLabel(barra, text="Apariencia", font=self.fuente_chica, text_color=TEXTO_SUAVE).grid(
            row=12, column=0, padx=24, pady=(0, 6), sticky="w")
        modo = ctk.CTkSegmentedButton(
            barra, values=["Claro", "Oscuro", "Sistema"], font=self.fuente_chica,
            command=lambda valor: ctk.set_appearance_mode(
                {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}[valor]),
        )
        modo.set("Sistema")
        modo.grid(row=13, column=0, padx=18, pady=(0, 24), sticky="ew")

    def _etiqueta_grupo(self, padre, texto, fila):
        ctk.CTkLabel(padre, text=texto, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color=TEXTO_SUAVE).grid(row=fila, column=0, padx=26, pady=(18, 4), sticky="w")

    def _armar_panel_video(self):
        panel = ctk.CTkFrame(self, corner_radius=18, fg_color=TARJETA)
        panel.grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        encabezado = ctk.CTkFrame(panel, fg_color="transparent")
        encabezado.grid(row=0, column=0, padx=22, pady=(18, 8), sticky="ew")
        encabezado.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(encabezado, text="Cámara en vivo", font=self.fuente_seccion).grid(
            row=0, column=0, sticky="w")
        self.indicador_camara = ctk.CTkLabel(
            encabezado, text="●  Apagada", font=self.fuente_chica, text_color=TEXTO_SUAVE)
        self.indicador_camara.grid(row=0, column=1, sticky="e")

        # El video y el cartel de "cámara apagada" comparten la celda: se muestra uno u otro
        self.contenedor_video = ctk.CTkFrame(panel, corner_radius=14, fg_color=FONDO)
        self.contenedor_video.grid(row=1, column=0, padx=22, pady=(0, 22), sticky="nsew")
        self.contenedor_video.grid_columnconfigure(0, weight=1)
        self.contenedor_video.grid_rowconfigure(0, weight=1)

        self.cartel_video = ctk.CTkFrame(self.contenedor_video, fg_color="transparent")
        self.cartel_video.grid(row=0, column=0)
        ctk.CTkLabel(self.cartel_video, text="📷", font=ctk.CTkFont(family="Segoe UI Emoji", size=56),
                     text_color=TEXTO_SUAVE).pack()
        ctk.CTkLabel(self.cartel_video, text="La cámara está apagada",
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(self.cartel_video, text="Tocá «Iniciar cámara» para tomar asistencia",
                     font=self.fuente, text_color=TEXTO_SUAVE).pack()
        self.etiqueta_video = ctk.CTkLabel(self.contenedor_video, text="")

    def _armar_panel_derecho(self):
        panel = ctk.CTkFrame(self, width=330, corner_radius=18, fg_color=TARJETA)
        panel.grid(row=0, column=2, padx=(10, 20), pady=(20, 10), sticky="nsew")
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        # Tarjetas con los totales
        resumen = ctk.CTkFrame(panel, fg_color="transparent")
        resumen.grid(row=0, column=0, padx=16, pady=(18, 6), sticky="ew")
        resumen.grid_columnconfigure((0, 1), weight=1)
        self.total_presentes = self._tarjeta_dato(resumen, "Presentes hoy", 0, VERDE)
        self.total_empleados = self._tarjeta_dato(resumen, "Empleados", 1, AZUL)

        pestanas = ctk.CTkTabview(panel, corner_radius=12, fg_color=FONDO,
                                  segmented_button_selected_color=AZUL,
                                  segmented_button_selected_hover_color=AZUL_HOVER)
        pestanas.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        pestanas.add("Asistencia de hoy")
        pestanas.add("Empleados")

        self.lista_asistencia = ctk.CTkScrollableFrame(pestanas.tab("Asistencia de hoy"), fg_color="transparent")
        self.lista_asistencia.pack(fill="both", expand=True)
        self.lista_empleados = ctk.CTkScrollableFrame(pestanas.tab("Empleados"), fg_color="transparent")
        self.lista_empleados.pack(fill="both", expand=True)

    def _tarjeta_dato(self, padre, titulo, columna, color):
        tarjeta = ctk.CTkFrame(padre, corner_radius=12, fg_color=FONDO)
        tarjeta.grid(row=0, column=columna, padx=4, sticky="ew")
        valor = ctk.CTkLabel(tarjeta, text="0", font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
                             text_color=color)
        valor.pack(padx=14, pady=(10, 0), anchor="w")
        ctk.CTkLabel(tarjeta, text=titulo, font=self.fuente_chica, text_color=TEXTO_SUAVE).pack(
            padx=14, pady=(0, 10), anchor="w")
        return valor

    def _armar_barra_estado(self):
        self.barra_estado = ctk.CTkLabel(self, text="", font=self.fuente_chica, text_color=TEXTO_SUAVE,
                                         anchor="w")
        self.barra_estado.grid(row=1, column=1, columnspan=2, padx=26, pady=(0, 14), sticky="ew")

    # =====================================================================
    # Listas del panel derecho
    # =====================================================================
    def _fila_persona(self, padre, nombre, detalle, color):
        fila = ctk.CTkFrame(padre, corner_radius=10, fg_color=TARJETA)
        fila.pack(fill="x", pady=4, padx=2)
        ctk.CTkLabel(fila, text=nombre[:1].upper(), width=36, height=36, corner_radius=18,
                     fg_color=color, text_color="#FFFFFF", font=self.fuente_boton).pack(
            side="left", padx=10, pady=8)
        ctk.CTkLabel(fila, text=nombre, font=self.fuente, anchor="w").pack(side="left", fill="x", expand=True)
        if detalle:
            ctk.CTkLabel(fila, text=detalle, font=self.fuente_chica, text_color=TEXTO_SUAVE).pack(
                side="right", padx=12)

    def _lista_vacia(self, padre, texto):
        ctk.CTkLabel(padre, text=texto, font=self.fuente_chica, text_color=TEXTO_SUAVE,
                     justify="center").pack(pady=30)

    def refrescar_asistencia(self):
        for hijo in self.lista_asistencia.winfo_children():
            hijo.destroy()
        registros = self.app.asistencias_de_hoy()
        self.total_presentes.configure(text=str(len(registros)))
        if not registros:
            self._lista_vacia(self.lista_asistencia, "Todavía no ingresó nadie hoy.")
        # El último en llegar arriba de todo
        for fila in reversed(registros):
            self._fila_persona(self.lista_asistencia, fila['Nombre'], fila['Hora'][:5], VERDE)

    def refrescar_empleados(self):
        for hijo in self.lista_empleados.winfo_children():
            hijo.destroy()
        nombres = sorted(self.app.reconocedor.nombres_conocidos)
        self.total_empleados.configure(text=str(len(nombres)))
        if not nombres:
            self._lista_vacia(self.lista_empleados,
                              "No hay empleados cargados.\nAgregá uno con la cámara o desde una foto.")
        for nombre in nombres:
            self._fila_persona(self.lista_empleados, nombre, "", AZUL)

    # =====================================================================
    # Carga inicial
    # =====================================================================
    def _cargar_empleados_en_segundo_plano(self):
        """Codificar las fotos tarda unos segundos: se hace en otro hilo para no congelar la ventana."""
        self.estado("⏳  Cargando empleados…")
        self._resultado_carga = None

        def trabajo():
            try:
                self._resultado_carga = self.app.cargar_empleados()
            except Exception as e:
                self._resultado_carga = e

        threading.Thread(target=trabajo, daemon=True).start()
        self.after(150, self._esperar_carga)

    def _esperar_carga(self):
        if self._resultado_carga is None:
            self.after(150, self._esperar_carga)
            return
        if isinstance(self._resultado_carga, Exception):
            self.estado(f"⚠  No se pudieron cargar los empleados: {self._resultado_carga}")
        else:
            self.estado(f"✅  Listo. {len(self._resultado_carga)} empleados cargados.")
        self.boton_camara.configure(state="normal")
        self.refrescar_empleados()
        self.refrescar_asistencia()

    # =====================================================================
    # Cámara
    # =====================================================================
    def alternar_camara(self):
        if self.camara_activa:
            self.detener_camara()
        else:
            self.iniciar_camara()

    def iniciar_camara(self):
        self.estado("⏳  Encendiendo la cámara…")
        self.update_idletasks()
        if not self.app.abrir_camara():
            self.app.cerrar_camara()
            self.estado("⚠  No se encontró ninguna cámara.")
            messagebox.showerror("Cámara", "No se pudo abrir la cámara. Revisá que esté conectada "
                                           "y que ninguna otra aplicación la esté usando.")
            return

        self.camara_activa = True
        self.numero_frame = 0
        self.ultimos_rostros = []
        self.boton_camara.configure(text="■   Detener cámara", fg_color=ROJO, hover_color=ROJO_HOVER)
        self.indicador_camara.configure(text="●  En vivo", text_color=ROJO)
        self.cartel_video.grid_remove()
        self.etiqueta_video.grid(row=0, column=0, sticky="nsew")
        self.estado("🎥  Cámara encendida. Los empleados reconocidos se registran solos.")
        self._actualizar_video()

    def detener_camara(self):
        self.camara_activa = False
        self._cancelar_proximo_frame()
        self.app.cerrar_camara()
        self.ultimo_frame = None
        self.boton_camara.configure(text="▶   Iniciar cámara", fg_color=VERDE, hover_color=VERDE_HOVER)
        self.indicador_camara.configure(text="●  Apagada", text_color=TEXTO_SUAVE)
        self.etiqueta_video.grid_remove()
        self.cartel_video.grid()
        self.estado("Cámara apagada.")

    def _actualizar_video(self):
        if not self.camara_activa:
            return

        frame = self.app.leer_frame()
        if frame is None:
            self.detener_camara()
            self.estado("⚠  Se perdió la señal de la cámara.")
            return

        self.ultimo_frame = frame.copy()

        # Reconocer es lo más costoso: se hace un frame sí y uno no, y en el
        # intermedio se reutilizan los recuadros anteriores.
        if self.numero_frame % 2 == 0:
            self.ultimos_rostros, nuevos = self.app.reconocer_y_registrar(frame)
            if nuevos:
                self.refrescar_asistencia()
                self.estado(f"✅  Ingreso registrado: {', '.join(nuevos)} a las "
                            f"{datetime.now().strftime('%H:%M')}")
        self.numero_frame += 1

        self.app.vista.dibujar_rostros(frame, self.ultimos_rostros)
        ancho = max(self.contenedor_video.winfo_width() - 16, 50)
        alto = max(self.contenedor_video.winfo_height() - 16, 50)
        self.etiqueta_video.configure(image=a_imagen_ctk(frame, ancho, alto))

        self._proximo_frame = self.after(15, self._actualizar_video)

    def _cancelar_proximo_frame(self):
        if self._proximo_frame is not None:
            self.after_cancel(self._proximo_frame)
            self._proximo_frame = None

    # =====================================================================
    # Empleados
    # =====================================================================
    def _pedir_nombre(self, sugerencia=""):
        dialogo = ctk.CTkInputDialog(title="Nuevo empleado",
                                     text="¿Cómo se llama el empleado?" +
                                          (f"\n(Enter vacío usa «{sugerencia}»)" if sugerencia else ""))
        nombre = dialogo.get_input()
        if nombre is None:
            return None
        return nombre.strip() or sugerencia

    def _agregar(self, nombre, imagen_bgr):
        try:
            nombre = self.app.agregar_empleado(nombre, imagen_bgr)
        except (ValueError, IOError) as e:
            messagebox.showwarning("No se pudo agregar", str(e))
            return
        self.refrescar_empleados()
        self.estado(f"✅  {nombre} quedó registrado como empleado.")

    def registrar_desde_camara(self):
        if not self.camara_activa or self.ultimo_frame is None:
            messagebox.showinfo("Registrar con la cámara",
                                "Primero encendé la cámara y ubicá a la persona de frente.")
            return
        foto = self.ultimo_frame.copy()
        nombre = self._pedir_nombre()
        if nombre:
            self._agregar(nombre, foto)

    def registrar_desde_archivo(self):
        ruta = filedialog.askopenfilename(title="Elegí la foto del empleado", filetypes=TIPOS_IMAGEN)
        if not ruta:
            return
        try:
            imagen = self.app.cargador.leer_archivo(ruta)
        except IOError as e:
            messagebox.showerror("Foto", str(e))
            return
        nombre = self._pedir_nombre(os.path.splitext(os.path.basename(ruta))[0])
        if nombre:
            self._agregar(nombre, imagen)

    # =====================================================================
    # Herramientas
    # =====================================================================
    def comparar_imagenes(self):
        control = filedialog.askopenfilename(title="1 de 2 · Elegí la imagen de CONTROL",
                                             filetypes=TIPOS_IMAGEN,
                                             initialdir=self.app.ajustes.CARPETA_EMPLEADOS)
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

    def abrir_carpeta_empleados(self):
        os.makedirs(self.app.ajustes.CARPETA_EMPLEADOS, exist_ok=True)
        os.startfile(self.app.ajustes.CARPETA_EMPLEADOS)

    def abrir_csv(self):
        os.startfile(self.app.ajustes.ARCHIVO_ASISTENCIA)

    # =====================================================================
    def estado(self, texto):
        self.barra_estado.configure(text=texto)

    def cerrar(self):
        self.camara_activa = False
        self._cancelar_proximo_frame()
        self.app.cerrar_camara()
        self.destroy()


class VentanaComparacion(ctk.CTkToplevel):
    """Muestra la imagen de control y la de prueba lado a lado con el resultado."""

    def __init__(self, padre, resultado):
        super().__init__(padre)
        self.title("Comparación de rostros")
        self.geometry("980x720")
        self.minsize(800, 600)
        self.configure(fg_color=FONDO)
        self.transient(padre)

        fuente_titulo = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        misma = resultado['misma_persona']

        # Cartel con el veredicto
        cartel = ctk.CTkFrame(self, corner_radius=16, fg_color=VERDE if misma else ROJO)
        cartel.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(cartel, text="✔  Es la misma persona" if misma else "✘  Son personas distintas",
                     font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                     text_color="#FFFFFF").pack(pady=(14, 0))
        ctk.CTkLabel(cartel,
                     text=f"Distancia entre rostros: {resultado['distancia']:.2f}   ·   "
                          f"Límite para coincidir: {resultado['tolerancia']:.2f}",
                     font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF").pack(pady=(2, 14))

        # El botón se empaqueta antes que las imágenes para que nunca quede afuera de la ventana
        ctk.CTkButton(self, text="Cerrar", command=self.destroy, width=160, height=40, corner_radius=12,
                      font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                      fg_color=AZUL, hover_color=AZUL_HOVER).pack(side="bottom", pady=18)

        imagenes = ctk.CTkFrame(self, fg_color="transparent")
        imagenes.pack(fill="both", expand=True, padx=18)
        imagenes.grid_columnconfigure((0, 1), weight=1, uniform="col")
        imagenes.grid_rowconfigure(0, weight=1)

        for columna, (titulo, clave) in enumerate((("Imagen de control", 'control'),
                                                   ("Imagen de prueba", 'prueba'))):
            tarjeta = ctk.CTkFrame(imagenes, corner_radius=16, fg_color=TARJETA)
            tarjeta.grid(row=0, column=columna, padx=6, sticky="nsew")
            ctk.CTkLabel(tarjeta, text=titulo, font=fuente_titulo).pack(pady=(14, 8))
            ctk.CTkLabel(tarjeta, text="", image=a_imagen_ctk(resultado[clave], 430, 400)).pack(
                padx=14, pady=(0, 14), expand=True)

        # En Windows la ventana nueva a veces aparece detrás de la principal
        self.after(100, self.lift)
        self.after(150, self.focus_force)
