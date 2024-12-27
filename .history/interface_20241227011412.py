import customtkinter as ctk
import os
import json
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import math
from pathlib import Path
import subprocess
import threading
import tempfile
import time
import ctypes


class ModernApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("DOWNTUBE")
        self.root.iconbitmap("metal.ico")
        self.root.geometry("1000x755")
        
        down_data = {
                "titles": [],
                "title": "",
                "tot": 0,
                "progress": 0,
                "suc": 0,
                "fail":0
            }
            
        with open("Down_Current_Stats.json", "w", encoding="utf-8") as file:
            json.dump(down_data, file, indent=4) 

        log_data ={
            "downloaded": [],
            "failed": [],
            "skipped": []
        }
        with open("download_log.json", "w", encoding="utf-8") as file:
            json.dump(log_data, file, indent=4, ensure_ascii=False) 

          # Define el archivo de señalización
        self.signal_flag = 0
        self.signal_file = os.path.join(tempfile.gettempdir(), "reload_stats_signal")

        config_data = self.load_config("config.json")
        self.down_data = self.load_config("Down_Current_Stats.json")
        self.download_log = self.load_config("download_log.json")
        
        
        # Asegurarse de que no haya errores si no se encuentra el archivo de configuración
        if config_data:
            ctk.set_appearance_mode(config_data.get('set_appearance_mode', 'dark'))
            ctk.set_default_color_theme(config_data.get('set_default_color_theme', 'CTkThemesPack-main\\themes\\lavender.json'))
        else:
            ctk.set_appearance_mode('dark')  # Valor por defecto si no se encuentra el archivo
            ctk.set_default_color_theme('CTkThemesPack-main\\themes\\lavender.json')
        
        # Obtener la carpeta de Descargas usando pathlib
        if os.name == 'nt':  # Para Windows
            self.download_folder = Path(os.environ['USERPROFILE']) / 'Downloads'
        if os.name == 'posix':  # Para macOS y Linux
            self.download_folder = Path.home() / 'Downloads'
        # Lista de archivos en la carpeta
        themes_files = [
            "autumn.json", "breeze.json", "carrot.json", "cherry.json",
            "coffee.json", "lavender.json", "marsh.json", "metal.json",
            "midnight.json", "orange.json", "patina.json", "pink.json",
            "red.json", "rime.json", "rose.json", "sky.json",
            "violet.json", "yellow.json"
        ]

        self.toggle_widget = 1
        self.stop_event = threading.Event()
        self.process = None
       

        theme_names = [os.path.splitext(file)[0] for file in themes_files]
        self.create_widgets(config_data, theme_names)
        self.toggle_cookie_entry()
        self.toggle_proxy_entry()
        value_for_fill_entry = None
        self.toggle_type_entry(value_for_fill_entry)
        self.first_filesize_label(config_data["max_filesize"])
        self.update_retries_label(config_data["retries"])
        self.first_limitrate_label(int(float(config_data['limit_rate'][:-1])))

       

    def monitor_signals(self, process, config_data, theme_names, stop_event):
        """Monitorea el archivo de señalización para recargar estadísticas."""
        while (process.poll() is None) and (not stop_event.is_set()):
            if os.path.exists(self.signal_file):
                try:
                    with open(self.signal_file, "r") as f:
                        signal_content = f.read().strip()
                    if signal_content == "reload":
                        self.reload_stats()
                
                        signal_content == ""
                    elif signal_content == "extract_info":
                        self.create_extracting_window()
                        self.add_extracting_info()
                        signal_content == "" 
                        self.new_window.lift()
                        self.new_window.attributes('-topmost', 1)
                       
                    # Limpia el archivo de señalización
                    os.remove(self.signal_file)
                except Exception as e:
                    print(f"Error handling signal: {e}")
                
            time.sleep(1)

        self.toggle_widget = 0
        self.toggle_widgets(self.toggle_widget)
 
        self.url_var = ''
        self.create_widgets(config_data, theme_names)
        self.reload_stats()
        self.first_filesize_label(config_data["max_filesize"])
        self.update_retries_label(config_data["retries"])

    def create_extracting_window(self):

        self.new_window = ctk.CTkToplevel(self.root)
        self.new_window.title("Extracting...")
        self.new_window.geometry("300x400")
        self.new_window.iconbitmap("metal.ico")
        
         # Lista de éxitos
        title_frame = ctk.CTkFrame(self.new_window, corner_radius=7)
        title_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.new_window.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        self.new_window.grid_rowconfigure(0, weight=1)  # Columna derecha no debe expandirse

        ctk.CTkLabel(title_frame, text="Extracting...").grid(row=0, column=0, pady=(5, 0))
        self.title_list = ctk.CTkTextbox(title_frame, height=360, wrap="none")
        self.title_list.grid(row=1, column=0, padx=5, pady=(5, 5), sticky="nsew")
        self.title_list.configure(state="disabled")

        title_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        title_frame.grid_rowconfigure(0, weight=1)  # Columna derecha no debe expandirse

    def add_extracting_info(self):

        self.title_list.configure(state="normal")

        with open("Down_Current_Stats.json", "r") as f:
            data = json.load(f)
        for item in data["titles"]:
            self.title_list.tag_config("#d8b574", foreground="#d8b574")
            self.title_list.insert("end", f"\n{item}", "#d8b574")

        # Deshabilitar para evitar edición
        self.title_list.configure(state="disabled")


    def reload_stats(self):

        self.down_data = self.load_config("Down_Current_Stats.json")
        self.download_log = self.load_config("download_log.json")

        self.progress_bar.set(self.down_data["progress"]/(self.down_data["tot"]+0.00001))
        self.progress_label.configure(text=f"Progress: {self.down_data['progress']}/{self.down_data['tot']} (Success: {self.down_data['suc']}, Failed: {self.down_data['fail']})")

        self.success_list.configure(state="normal")
        self.success_list.delete("1.0", "end")  # Limpiar antes de agregar

        # Agregar títulos de descargas exitosas
        for item in self.download_log["downloaded"]:
            if item["status"] == "success":
                self.success_list.tag_config("green", foreground="green")
                self.success_list.insert("end", f"{item['title']}\n", "green")

        # Deshabilitar para evitar edición
        self.success_list.configure(state="disabled")
        
        self.failed_list.configure(state="normal")
        self.failed_list.delete("1.0", "end")  # Limpiar antes de agregar

        # Agregar títulos de descargas exitosas
        for item in self.download_log["failed"]:
            if item["status"] == "failed":
                self.failed_list.tag_config("red", foreground="#FF6666")  # Rojo menos saturado
                self.failed_list.insert("end", f"{item['title']}\n", "red")

        for item in self.download_log["skipped"]:
            self.failed_list.insert("end", f"{item['title']}\n")

        # Deshabilitar para evitar edición
        self.failed_list.configure(state="disabled")
        
    def load_config(self,config_path):
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as file:
                return json.load(file)
        else:
            return {}

    def save_config(self, config_data):
        with open("config.json", "w", encoding="utf-8") as file:
            json.dump(config_data, file, indent=4)  

    def select_folder(self):
        # Abrir el cuadro de diálogo para seleccionar una carpeta
        folder_selected = filedialog.askdirectory(title="Seleccionar Carpeta de Descarga")
        
        # Si el usuario selecciona una carpeta, actualizar la entrada de texto con la ruta
        if folder_selected:
            self.default_folder_var.set(folder_selected)

    def select_cookie_folder(self):
        # Abrir el cuadro de diálogo para seleccionar una carpeta
        folder_selected = filedialog.askopenfilename(title="Seleccionar Carpeta de Cookies")
        
        # Si el usuario selecciona una carpeta, actualizar la entrada de texto con la ruta
        if folder_selected:
            self.cookie_path_var.set(folder_selected)


    def create_widgets(self, config_data, theme_names):
        corner_basic_r = 7
        left_pad = 20
        up_pad = 20
      

        # Frame principal
        main_frame = ctk.CTkFrame(self.root, corner_radius=corner_basic_r)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configurar las filas y columnas del grid principal para expandir con la ventana
        self.root.grid_rowconfigure(0, weight=1)  # La fila principal debe expandirse
        self.root.grid_columnconfigure(0, weight=1)  # La columna principal debe expandirse

        # Crear imagen
        my_image = ctk.CTkImage(light_image=Image.open("metal_logo.png"),
                                dark_image=Image.open("metal_logo.png"),
                                size=(358, 88))

        # Crear Label con la imagen
        image_label = ctk.CTkLabel(main_frame, image=my_image, text="")
        image_label.grid(row=0, column=0, padx=left_pad, pady=(0, 0), sticky="n")

        # Frame superior con URL y botón
        top_frame = ctk.CTkFrame(main_frame, width=10, corner_radius=corner_basic_r)
        top_frame.grid(row=1, column=0, padx=left_pad, pady=(0, up_pad), sticky="ew")

        self.url_var = ctk.StringVar()  # Valor por defecto: 100GB value=down_data["Url"]
        self.url_entry = ctk.CTkEntry(top_frame, placeholder_text="Enter URL here", corner_radius=corner_basic_r, textvariable=self.url_var)#, textvariable=self.url_var
        self.url_entry.grid(row=0, column=0, padx=(5, 5), pady=5, sticky="ew")


        top_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        top_frame.grid_columnconfigure(1, weight=0)  # Columna derecha no debe expandirse

        # Frame de progreso
        progress_frame = ctk.CTkFrame(main_frame, width=620, corner_radius=corner_basic_r)
        progress_frame.grid(row=2, column=0, padx=left_pad, pady=0, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=370)
        self.progress_bar.grid(row=0, column=0, padx=10, sticky="ew")
        self.progress_bar.set(self.down_data["progress"]/(self.down_data["tot"]+0.01))

        self.progress_label = ctk.CTkLabel(progress_frame, text = f"Progress: {self.down_data['progress']}/{self.down_data['tot']} (Success: {self.down_data['suc']}, Failed: {self.down_data['fail']}")#, text = f"Progress: {down_data['progress']}/{down_data['tot']} (Success: {down_data['suc']}, Failed: {down_data['fail']}"
        self.progress_label.grid(row=0, column=1, padx=10)

        progress_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        progress_frame.grid_columnconfigure(1, weight=0)  # Columna derecha no debe expandirse

        # Frame central con listas
        lists_frame = ctk.CTkFrame(main_frame, width=620, corner_radius=corner_basic_r)
        lists_frame.grid(row=3, column=0, padx=left_pad, pady=up_pad, sticky="nsew")

        lists_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        lists_frame.grid_columnconfigure(1, weight=1)  # Columna derecha no debe expandirse
        lists_frame.grid_rowconfigure(0, weight=1)  # Columna derecha no debe expandirse

        # Lista de éxitos
        success_frame = ctk.CTkFrame(lists_frame, corner_radius=corner_basic_r)
        success_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(success_frame, text="Success").grid(row=0, column=0, pady=(5, 0))
        self.success_list = ctk.CTkTextbox(success_frame, width=294, wrap="none")
        self.success_list.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="nsew")
        self.success_list.configure(state="disabled")

        success_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        success_frame.grid_rowconfigure(1, weight=1)  # Columna derecha no debe expandirse

        # Lista de fallos
        failed_frame = ctk.CTkFrame(lists_frame, corner_radius=corner_basic_r)
        failed_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(failed_frame, text="Failed").grid(row=0, column=0, pady=(5, 0))
        self.failed_list = ctk.CTkTextbox(failed_frame, width=294, wrap="none")
        self.failed_list.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="nsew")
        self.failed_list.configure(state="disabled")

        failed_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        failed_frame.grid_rowconfigure(1, weight=1)  # Columna derecha no debe expandirse

        # Panel de ajustes 
        settings_frame = ctk.CTkFrame(main_frame, width=320, corner_radius=corner_basic_r)
        settings_frame.grid(row=0, column=1, padx=0, pady=up_pad, sticky="nsew", rowspan=4)

        ctk.CTkLabel(settings_frame, width=320,text="Settings").grid(row=0, column=0, pady=(5,0), sticky="nsew")
        set_frame = ctk.CTkFrame(settings_frame, corner_radius=corner_basic_r)
        set_frame.grid(row=1, column=0, padx=5, pady=(0,5), sticky="nsew", rowspan=4)

        settings_frame.grid_rowconfigure(1, weight=1)  # La fila con la imagen debe expandirse

        # 0. type
        self.type_var = ctk.StringVar(value=config_data["type"])
        self.type_menu = ctk.CTkOptionMenu(set_frame, variable=self.type_var, values=["music", "video"], command=self.toggle_type_entry)
        self.type_label = ctk.CTkLabel(set_frame, text="Download Type")
        self.type_label.grid(row=1, column=0, padx=10, pady=(10,5), sticky="w")
        self.type_menu.grid(row=1, column=1, padx=10, pady=(10,5), sticky="w")

        
         # 0.5 v_quality
        self.v_quality_var = ctk.StringVar(value=config_data["v_quality"])
        self.v_quality_menu = ctk.CTkOptionMenu(set_frame, variable=self.v_quality_var, values=["1080p", "720p", "480p"])
        self.v_q_label = ctk.CTkLabel(set_frame, text="Video Quality")
        self.v_q_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.v_quality_menu.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # 1. "no_overwrites" - Casilla de verificación
        self.no_overwrite_var = ctk.BooleanVar(value=config_data["no_overwrites"])  # Predeterminado: True

        # Etiqueta de la casilla de verificación
        self.no_overwrite_label = ctk.CTkLabel(set_frame, text="No Overwrites")
        self.no_overwrite_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación sin texto
        self.no_overwrite_checkbox = ctk.CTkCheckBox(set_frame, variable=self.no_overwrite_var, text="")
        self.no_overwrite_checkbox.grid(row=3, column=1, pady=5, sticky="e")

        # Casilla de verificación "Quiet Mode"
        self.quiet_var = ctk.BooleanVar(value=config_data["quiet"])  # Predeterminado: False

        # Etiqueta de la casilla de verificación
        self.quiet_label = ctk.CTkLabel(set_frame, text="Quiet Mode")
        self.quiet_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación
        self.quiet_checkbox = ctk.CTkCheckBox(set_frame, variable=self.quiet_var, text="")
        self.quiet_checkbox.grid(row=4, column=1, pady=5, sticky="e")

       # 3. "max_filesize" - Slider para el tamaño máximo de archivo
        self.max_filesize_var = ctk.DoubleVar(value=config_data["max_filesize"])  # Valor inicial

        # Crear el slider (1M a 1000G -> 1 a 1000000)
        self.max_filesize_slider = ctk.CTkSlider(
            set_frame,
            from_=0,
            to=600,  # Aprox 1000G
            command=self.update_filesize_label
            , width=140
        )
        self.max_filesize_slider.set(self.inv_log_scale_fs(self.max_filesize_var.get())-600)
     
        self.max_filesize_slider.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Etiqueta para mostrar el valor formateado
        self.filesize_label = ctk.CTkLabel(
            set_frame,
            text=f"Max Filesize: {config_data['max_filesize']}"
        )    
        self.filesize_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")    

        # 4. "simulate" - Casilla de verificación
        self.simulate_var = ctk.BooleanVar(value=config_data["simulate"])  # Predeterminado: False

        # Etiqueta para "Simulate"
        self.simulate_label = ctk.CTkLabel(set_frame, text="Simulate")
        self.simulate_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación para "Simulate"
        self.simulate_checkbox = ctk.CTkCheckBox(set_frame, variable=self.simulate_var, text="")
        self.simulate_checkbox.grid(row=6, column=1, pady=5, sticky="e")

        # 5. "set_proxy" - Casilla de verificación
        self.set_proxy_var = ctk.BooleanVar(value=config_data["set_proxy"])  # Predeterminado: False

        # Etiqueta para "Set Proxy"
        self.set_proxy_label = ctk.CTkLabel(set_frame, text="Set Proxy")
        self.set_proxy_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación para "Set Proxy"
        self.set_proxy_checkbox = ctk.CTkCheckBox(set_frame, variable=self.set_proxy_var, text="", command=self.toggle_proxy_entry)
        self.set_proxy_checkbox.grid(row=7, column=1, pady=5, sticky="e")

        # 6. "proxy" - Entrada de texto (URL del proxy)
        self.proxy_var = ctk.StringVar(value=config_data["proxy"])  # Valor predeterminado
        self.proxy_entry = ctk.CTkEntry(set_frame, textvariable=self.proxy_var)
        self.set_proxy_label2 = ctk.CTkLabel(set_frame, text="Proxy URL")
        self.set_proxy_label2.grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.proxy_entry.grid(row=8, column=1, padx=10, pady=5, sticky="w")


        # 7. "geo_bypass" - Casilla de verificación
        self.geo_bypass_var = ctk.BooleanVar(value=config_data["geo_bypass"])  # Predeterminado: True

        # Etiqueta para "Geo Bypass"
        self.geo_bypass_label = ctk.CTkLabel(set_frame, text="Geo Bypass")
        self.geo_bypass_label.grid(row=9, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación para "Geo Bypass"
        self.geo_bypass_checkbox = ctk.CTkCheckBox(set_frame, variable=self.geo_bypass_var, text="")
        self.geo_bypass_checkbox.grid(row=9, column=1, pady=5, sticky="e")

        

        # 8. "retries" - Entrada de texto (número de reintentos)

        self.retries_var = ctk.DoubleVar(value=config_data["retries"])  # Valor inicial

        # Crear el slider (1M a 1000G -> 1 a 1000000)
        self.retries_slider = ctk.CTkSlider(
            set_frame,
            from_=0,
            to=20,  # Aprox 1000G
            command=self.update_retries_label
            , width=140
        )
        self.retries_slider.set(self.retries_var.get())
     
        self.retries_slider.grid(row=10, column=1, padx=10, pady=5, sticky="w")

        # Etiqueta para mostrar el valor formateado
        self.retries_label = ctk.CTkLabel(
            set_frame,
            text=f"Retries: {config_data['retries']}"
        )    
        self.retries_label.grid(row=10, column=0, padx=10, pady=5, sticky="w")  

        # 9. "limit_rate" - Entrada de texto (limitar la velocidad)

        self.limit_rate_var = ctk.DoubleVar(value=int(float(config_data['limit_rate'][:-1]) * 1000))

        # Crear el slider (1M a 1000G -> 1 a 1000000)
        self.limitrate_slider = ctk.CTkSlider(
            set_frame,
            from_=0,
            to=100,  # Aprox 1000G
            command=self.update_limitrate_label
            , width=140
        )
        self.limitrate_slider.set(self.inv_log_scale_lr(self.limit_rate_var.get()))
     
        self.limitrate_slider.grid(row=11, column=1, padx=10, pady=5, sticky="w")

        # Etiqueta para mostrar el valor formateado
        self.limitrate_label = ctk.CTkLabel(
            set_frame,
            text = f"Limit Rate: {int(float(config_data['limit_rate'][:-1]) * 1000)}"
        )    
        self.limitrate_label.grid(row=11, column=0, padx=10, pady=5, sticky="w")  

        # 10. "default_folder" - Entrada de texto (carpeta de descarga predeterminada)
        self.default_folder_var = ctk.StringVar(value=config_data["custom_folder"])  # Aquí se puede poner una ruta por defecto si lo deseas
        self.default_folder_entry = ctk.CTkEntry(set_frame, textvariable=self.default_folder_var,width=107)
        self.default_folder_label = ctk.CTkLabel(set_frame, text="Download Folder")
        self.default_folder_label.grid(row=12, column=0, padx=10, pady=5, sticky="w")
        self.default_folder_entry.grid(row=12, column=1, padx=(10,1), pady=5, sticky="w")

        # Botón para seleccionar carpeta
        self.folder_button = ctk.CTkButton(set_frame, text="📁", command=self.select_folder,width=27)
        self.folder_button.grid(row=12, column=1, padx=(123,10), pady=5, sticky="w")

        # 10.5. "auto_quookie" - Casilla de verificación
        self.auto_cookies_var = ctk.BooleanVar(value=config_data["auto_cookies"])  # Predeterminado: True

        # Etiqueta para "Geo Bypass"
        self.auto_cookies_label = ctk.CTkLabel(set_frame, text="Auto Cookies")
        self.auto_cookies_label.grid(row=13, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación para "Geo Bypass"
        self.auto_cookies_checkbox = ctk.CTkCheckBox(set_frame, variable=self.auto_cookies_var, text="", command=self.toggle_cookie_entry)
        self.auto_cookies_checkbox.grid(row=13, column=1, pady=5, sticky="e")

        # 11. "cookie_path" - Entrada de texto (ruta de las cookies)
        self.cookie_path_var = ctk.StringVar(value=config_data["cookie_path"])  # Aquí se puede poner una ruta por defecto si lo deseas
        self.cookie_path_entry = ctk.CTkEntry(set_frame, textvariable=self.cookie_path_var, width=107)
        self.set_cookie_label = ctk.CTkLabel(set_frame, text="Cookie Path")
        self.set_cookie_label.grid(row=14, column=0, padx=10, pady=5, sticky="w")
        self.cookie_path_entry.grid(row=14, column=1, padx=(10,1), pady=5, sticky="w")

        # Botón para seleccionar carpeta
        self.cookie_folder_button = ctk.CTkButton(set_frame, text="📁", command=self.select_cookie_folder, width=27)
        self.cookie_folder_button.grid(row=14, column=1, padx=(123,10), pady=5, sticky="w")

        # 12. "set_appearance_mode" - Opción de selección (modo de apariencia)
        self.appearance_mode_var = ctk.StringVar(value=config_data["set_appearance_mode"])
        self.appearance_mode_menu = ctk.CTkOptionMenu(set_frame, variable=self.appearance_mode_var, values=["light", "dark"])
        self.appearance_mode_menu_label =ctk.CTkLabel(set_frame, text="Appearance Mode")
        self.appearance_mode_menu_label.grid(row=15, column=0, padx=10, pady=5, sticky="w")
        self.appearance_mode_menu.grid(row=15, column=1, padx=10, pady=5, sticky="w")

        # 13. "set_default_color_theme" - Entrada de texto (tema de color predeterminado)
        self.color_theme_var = ctk.StringVar(value=os.path.splitext(os.path.basename(config_data["set_default_color_theme"]))[0])
        self.selected_theme = ctk.CTkOptionMenu(set_frame, variable=self.color_theme_var, values=theme_names)
        self.selected_theme_label = ctk.CTkLabel(set_frame, text="Default Color Theme")
        self.selected_theme_label.grid(row=16, column=0, padx=10, pady=5, sticky="w")
        self.selected_theme.grid(row=16, column=1, padx=10, pady=5, sticky="w")

        # 7. "geo_bypass" - Casilla de verificación
        self.terminal_var = ctk.BooleanVar(value=False)  # Predeterminado: True

        # Etiqueta para "Geo Bypass"
        self.terminal_label = ctk.CTkLabel(set_frame, text="Show Terminal")
        self.terminal_label.grid(row=17, column=0, padx=10, pady=5, sticky="w")

        # Casilla de verificación para "Geo Bypass"
        self.terminal_checkbox = ctk.CTkCheckBox(set_frame, variable=self.terminal_var, text="")
        self.terminal_checkbox.grid(row=17, column=1, pady=5, sticky="e")

        self.start_button = ctk.CTkButton(top_frame, text="Start", command=lambda: self.process_start(config_data, theme_names), corner_radius=corner_basic_r)
        self.start_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        # Configurar el comportamiento de las filas y columnas del grid
        main_frame.grid_rowconfigure(0, weight=0, minsize=100)  # La fila con la imagen debe expandirse
        main_frame.grid_rowconfigure(1, weight=0)  # La fila del formulario no debe expandirse
        main_frame.grid_rowconfigure(2, weight=0)  # La fila del progreso debe expandirse
        main_frame.grid_rowconfigure(3, weight=3)  # La fila de las listas debe expandirse más
        main_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda debe expandirse
        main_frame.grid_columnconfigure(1, weight=0)  # Columna derecha no debe expandirse


       # Para cada widget que cambia un valor, agregar un comando para actualizar y guardar la configuración.
        self.url_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.type_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.v_quality_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.no_overwrite_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.quiet_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.max_filesize_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.simulate_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.set_proxy_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.proxy_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.geo_bypass_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.retries_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.limit_rate_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.default_folder_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.auto_cookies_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.cookie_path_var.trace_add("write", lambda *args: self.update_config(theme_names,0))
        self.appearance_mode_var.trace_add("write", lambda *args: self.update_config(theme_names,1))
        self.color_theme_var.trace_add("write", lambda *args: self.update_config(theme_names,1))

    def process_start(self, config_data, theme_names):

        self.toggle_widget = 1
     
        down_data = {
                "titles": [],
                "title": "",
                "tot": 0,
                "progress": 0,
                "suc": 0,
                "fail":0
            }
            
        with open("Down_Current_Stats.json", "w", encoding="utf-8") as file:
            json.dump(down_data, file, indent=4) 

            log_data ={
            "downloaded": [],
            "failed": [],
            "skipped": []
        }
        with open("download_log.json", "w", encoding="utf-8") as file:
            json.dump(log_data, file, indent=4, ensure_ascii=False) 
        
        self.success_list.configure(state="normal")
        self.success_list.delete("1.0", "end")  # Limpiar antes de agregar
        self.success_list.configure(state="disabled")
        
        self.failed_list.configure(state="normal")
        self.failed_list.delete("1.0", "end")  # Limpiar antes de agregar
        self.failed_list.configure(state="disabled")

        self.toggle_widgets(self.toggle_widget)
        self.process = subprocess.Popen(['python', 'downloader.py'])
        thread = threading.Thread(
            target=self.monitor_signals,  # Método a ejecutar
            args=(self.process, config_data, theme_names, self.stop_event),  # Argumentos del método
            daemon=True  # Para que el hilo sea demonio y no bloquee la salida del programa
        )
        thread.start()
        
        



    def log_scale_fs(self, value):
        # Escala logarítmica de 1M (10^0) a 1000G (10^6)
        return 10 ** (value / 100)  # Escala más agresiva

    def inv_log_scale_fs(self, value):
        # Inversa de la escala logarítmica
        return math.log10(value) * 100  # Escala inversa ajustada

    def update_filesize_label(self, value):
        scaled_value = self.log_scale_fs(value)
        if scaled_value < 1000:
            formatted_value = f"{int(scaled_value)}Mb"
        elif scaled_value >= 1000 and scaled_value < 1000000:
            formatted_value = f"{int(scaled_value / 1000)}Gb"
        else:
            formatted_value = f"{int(scaled_value / 1000000)}Tb"
        
        self.filesize_label.configure(text=f"Max Filesize: {formatted_value}")
        self.max_filesize_var.set(int(scaled_value)*1000000)   

    def first_filesize_label(self, value):
        if value < 1000000000:
            formatted_value = f"{int(value/1000000)}Mb"
        elif value >= 1000000000 and value < 1000000000000:
            formatted_value = f"{int(value / 1000000000)}Gb"
        else:
            formatted_value = f"{int(value / 1000000000000)}Tb"
        
        self.filesize_label.configure(text=f"Max Filesize: {formatted_value}")  
    
    def log_scale_lr(self, value):
        # Escala logarítmica de 100KB (10^2) a 20GB (10^7)
        return 10 ** (value * 5 / 100) * 100  # Escala ajustada para 100KB a 20GB

    def inv_log_scale_lr(self, value):
        # Inversa de la escala logarítmica
        return (math.log10(value / 100) * 100) / 5  # Escala inversa ajustada para 100KB a 20GB

    def update_limitrate_label(self, value):
        # Aplicar la escala logarítmica para obtener el valor real
        scaled_value = self.log_scale_lr(value)
        
        # Formatear el valor de acuerdo con el rango
        if scaled_value < 1000:
            formatted_value = f"{int(scaled_value)}KB"
        elif scaled_value >= 1000 and scaled_value < 1000000:
            formatted_value = f"{int(scaled_value / 1000)}MB"
        elif scaled_value >= 1000000 and scaled_value < 1000000000:
            formatted_value = f"{int(scaled_value / 1000000)}GB"
        else:
            formatted_value = f"{int(scaled_value / 1000000000)}TB"
        
        # Actualizar la etiqueta con el valor formateado
        self.limitrate_label.configure(text=f"LimitRate: {formatted_value}")

        # Actualizar el valor de max_filesize_var (para mantener sincronización con el slider)
        self.limit_rate_var.set(scaled_value)

    def first_limitrate_label(self, value):
        
        if value < 1:
            formatted_value = f"{int(value)*1000}KB"
        elif value >= 1 and value < 1000:
            formatted_value = f"{int(value)}MB"
        elif value >= 1000 and value < 1000000:
            formatted_value = f"{int(value / 1000)}GB"
        else:
            formatted_value = f"{int(value / 1000000)}TB"
        
        # Actualizar la etiqueta con el valor formateado
        self.limitrate_label.configure(text=f"LimitRate: {formatted_value}")
    
    def update_retries_label(self, value):
       
        retries = f"{int(value)}"
        
        self.retries_label.configure(text=f"Retries: {retries}")
        self.retries_var.set(int(value))     
    

    def toggle_proxy_entry(self):
        if self.set_proxy_var.get():
            # Habilitar la entrada de texto
            self.proxy_entry.configure(state="normal")
            if self.appearance_mode_var.get() == "dark":
                self.set_proxy_label2.configure(text_color="white")  # Etiqueta de proxy color normal
                self.proxy_entry.configure(text_color="white")
            else:
                self.set_proxy_label2.configure(text_color="black")  # Etiqueta de proxy color normal
                self.proxy_entry.configure(text_color="black")
        else:
            # Deshabilitar la entrada de texto
            self.proxy_entry.configure(state="disabled")
            self.proxy_entry.configure(text_color="gray")  # Atenuar texto de la entrada
            self.set_proxy_label2.configure(text_color="gray") 

    def toggle_type_entry(self, value_for_fill_entry):
        if self.type_var.get() == "video":
            # Habilitar la entrada de texto
            self.v_quality_menu.configure(state="normal")
            if self.appearance_mode_var.get() == "dark":
                self.v_q_label.configure(text_color="white")  # Etiqueta de proxy color normal
                self.v_quality_menu.configure(text_color="white")
            else:
                self.v_q_label.configure(text_color="black")  # Etiqueta de proxy color normal
                self.v_quality_menu.configure(text_color="black")
        else:
            # Deshabilitar la entrada de texto
            self.v_quality_menu.configure(state="disabled")
            self.v_quality_menu.configure(text_color="gray")  # Atenuar texto de la entrada
            self.v_q_label.configure(text_color="gray")

    def toggle_cookie_entry(self):
        if self.auto_cookies_var.get() == 0:
            # Habilitar la entrada de texto
            self.cookie_path_entry.configure(state="normal")
            self.cookie_folder_button.configure(state="normal")
            if self.appearance_mode_var.get() == "dark":
                self.set_cookie_label.configure(text_color="white")  # Etiqueta de proxy color normal
                self.cookie_path_entry.configure(text_color="white")
            else:
                self.set_cookie_label.configure(text_color="black")  # Etiqueta de proxy color normal
                self.cookie_path_entry.configure(text_color="black")
        else:
            # Deshabilitar la entrada de texto
            self.cookie_path_entry.configure(state="disabled")
            self.cookie_folder_button.configure(state="disabled")
            self.cookie_path_entry.configure(text_color="gray")  # Atenuar texto de la entrada
            self.set_cookie_label.configure(text_color="gray")    

    
    def update_config(self, theme_names, flag_reset_widgets):
        config_data = {
            "url": self.url_var.get(),
            "type": self.type_var.get(),
            "v_quality": self.v_quality_var.get(),
            "no_overwrites": self.no_overwrite_var.get(),
            "quiet": self.quiet_var.get(),
            "max_filesize": self.max_filesize_var.get(),
            "simulate": self.simulate_var.get(),
            "set_proxy": self.set_proxy_var.get(),
            "proxy": self.proxy_var.get(),
            "geo_bypass": self.geo_bypass_var.get(),
            "retries": int(self.retries_var.get()),
            "limit_rate": f"{round(self.limit_rate_var.get()/1000, 2)}M",
            "custom_folder": self.default_folder_var.get(),
            "default_folder": str(self.download_folder),
            "auto_cookies": self.auto_cookies_var.get(),
            "cookie_path": self.cookie_path_var.get(),
            "set_appearance_mode": self.appearance_mode_var.get(),
            "set_default_color_theme": f"{self.theme_folder}\\themes\\{self.color_theme_var.get()}.json"
        }
        self.save_config(config_data)
        ctk.set_appearance_mode(config_data.get('set_appearance_mode', 'dark'))
        ctk.set_default_color_theme(config_data.get('set_default_color_theme', f'{self.theme_folder}\\themes\\lavender.json'))

        if flag_reset_widgets == 1:
            self.create_widgets(config_data, theme_names)
            self.first_filesize_label(config_data["max_filesize"])
            self.update_retries_label(config_data["retries"])
        self.toggle_cookie_entry()
        self.toggle_proxy_entry()
        value_for_fill_entry = None
        self.toggle_type_entry(value_for_fill_entry)

    def toggle_widgets(self, on_start):
        # 1. Tipo de descarga (type_menu)

        self.toggle_entry(self.start_button, on_start, self.type_label)

        self.toggle_entry(self.type_menu, on_start, self.type_label)
        
        # 2. Calidad de video (v_quality_menu)
        self.toggle_entry(self.v_quality_menu, on_start, label = self.v_q_label)

        self.toggle_entry(self.no_overwrite_checkbox, on_start, label = self.no_overwrite_label)

        self.toggle_entry(self.quiet_checkbox, on_start, label = self.quiet_label)

        self.toggle_entry(self.max_filesize_slider,  on_start, label = self.filesize_label)

        self.toggle_entry(self.simulate_checkbox,  on_start, label = self.simulate_label)
        # 4. Proxy
        self.toggle_entry(self.proxy_entry, on_start, label=self.set_proxy_label2)

        self.toggle_entry(self.set_proxy_checkbox, on_start, label=self.set_proxy_label)

        self.toggle_entry(self.geo_bypass_checkbox, on_start, label=self.geo_bypass_label)

        # 6. Retries
        self.toggle_entry(self.retries_slider, on_start, label = self.retries_label)

        # 7. Limitar velocidad
        self.toggle_entry(self.limitrate_slider,  on_start, label = self.limitrate_label)

        # 8. Carpeta predeterminada
        self.toggle_entry(self.default_folder_entry,  on_start, label = self.default_folder_label)

        self.toggle_entry(self.folder_button,  on_start)

        # 9. Ruta de cookies

        self.toggle_entry(self.auto_cookies_checkbox,  on_start, label = self.auto_cookies_label)

        self.toggle_entry(self.cookie_path_entry,  on_start, label = self.set_cookie_label)

        self.toggle_entry(self.cookie_folder_button,  on_start)

        # 10. Modo de apariencia
        self.toggle_entry(self.appearance_mode_menu, on_start, label = self.appearance_mode_menu_label)

        # 11. Tema de color
        self.toggle_entry(self.selected_theme,  on_start, label = self.selected_theme_label)

        self.toggle_entry(self.terminal_checkbox,  on_start, label = self.terminal_label)

        if not on_start:
            self.toggle_cookie_entry()
            self.toggle_proxy_entry()
            value_for_fill_entry = None
            self.toggle_type_entry(value_for_fill_entry)
      

    # Funcion general para habilitar/deshabilitar entradas y etiquetas
    def toggle_entry(self, widget, on_start, label = None):
        if not on_start:
            widget.configure(state="normal")
            color = "white" if self.appearance_mode_var.get() == "dark" else "black"
            if widget == self.proxy_entry or widget == self.default_folder_entry or widget == self.cookie_path_entry:
                widget.configure(text_color=color)
            if label:
                label.configure(text_color=color)
        else:
            widget.configure(state="disabled")
            if widget == self.proxy_entry or widget == self.default_folder_entry or widget == self.cookie_path_entry:
                widget.configure(text_color="gray")
            if label:
                label.configure(text_color="gray")
    
    def stop_subprocess(self):
        """Método para detener el subprocess y el hilo"""
        if self.process:
            self.process.terminate()  # Terminar el proceso
            self.process.wait()  # Esperar que termine correctamente

        # Señalar al hilo que termine
        self.stop_event.set()

    def on_close(self):
        """Método llamado cuando se cierra la ventana"""
        self.stop_subprocess()  # Llamamos a la función para parar el subprocess y el hilo
        self.root.quit()  # Cerrar la ventana de la aplicación

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()


if __name__ == "__main__":
    app = ModernApp()
    app.run()