# NEF to JPG Converter

Aplicación de escritorio Windows para convertir archivos RAW de Nikon (.NEF) y otros formatos RAW a JPEG de alta calidad.

---

## ✅ Requisitos

- **Windows 10/11**
- **Python 3.10 o superior** → [python.org](https://python.org)
- Pip actualizado

---

## 🚀 Instalación y ejecución (modo desarrollo)

```bash
# 1. Clonar / abrir el proyecto en VSCode
# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
python main.py
```

---

## 📦 Generar el ejecutable .exe

Simplemente ejecutá:

```
build.bat
```

Esto hace automáticamente:
1. Instala todas las dependencias
2. Genera el ícono `assets/icon.ico`
3. Compila con PyInstaller
4. Genera `dist/NEFtoJPG.exe` (portable, sin instalación)

---

## 🖼️ Funcionalidades

| Feature | Detalle |
|---|---|
| Formatos soportados | .NEF, .CR2, .CR3, .ARW, .DNG, .RAF, .RW2 |
| Drag & Drop | Arrastrar archivos directamente sobre la ventana |
| Calidad JPEG | Slider ajustable 50–100 |
| Redimensión | Original / 1920px / 3840px / Tamaño personalizado |
| Sobrescribir | Toggle activable/desactivable |
| Multithreading | Hasta 4 archivos en paralelo |
| Barra de progreso | Tiempo real con contadores |
| Log de errores | Panel expandible con detalle de cada error |

---

## 📁 Estructura del proyecto

```
Conversor .nef a .jpg/
├── main.py                   # Punto de entrada
├── ui/
│   ├── app.py                # Ventana principal
│   ├── file_list.py          # Lista de archivos con estados
│   ├── settings_panel.py     # Panel de configuración
│   └── progress_panel.py     # Barra de progreso y contadores
├── converters/
│   └── nef_converter.py      # Lógica de conversión RAW → JPG
├── assets/
│   └── icon.ico              # Ícono (generado por create_icon.py)
├── create_icon.py            # Generador de ícono
├── requirements.txt          # Dependencias Python
├── build.bat                 # Script de compilación
└── README.md                 # Este archivo
```

---

## 🔧 Dependencias

| Librería | Uso |
|---|---|
| `customtkinter` | Interfaz gráfica moderna |
| `rawpy` | Decodificación de archivos RAW (LibRaw) |
| `Pillow` | Procesamiento y guardado de imágenes |
| `imageio` | Soporte adicional de formatos |
| `tkinterdnd2` | Drag & Drop de archivos |
| `numpy` | Procesamiento de arrays de píxeles |
| `pyinstaller` | Compilación a .exe |

---

## ⚠️ Solución de problemas

**`rawpy` no instala en Windows**  
→ Asegurate de tener Visual C++ Redistributable instalado.

**La app abre y cierra inmediatamente**  
→ Ejecutá desde CMD con `python main.py` para ver el error.

**El .exe no encuentra librerías**  
→ Ejecutar `build.bat` de nuevo; el script incluye todos los módulos necesarios.

---

## 📌 Notas de versión

- **v1.0.0** — Primera versión estable. Conversión NEF→JPG con interfaz moderna.

---

*Hecho con ❤️ y Python*
