# Mantener el manual ilustrado

El manual se publica en `docs/manual_usuario.md` y `docs/manual_usuario.pdf`. Sus capturas PNG originales están en `docs/manual/capturas/`; las figuras SVG añaden números y flechas vectoriales sobre esas capturas sin sustituir la interfaz por un dibujo.

## Obtener capturas nuevas

Desde la raíz del proyecto, en Windows con Chrome instalado y las dependencias del frontend disponibles:

```powershell
.\frontend\.venv\Scripts\python.exe docs/tools/capture_manual.py
```

Para actualizar sólo algunas escenas:

```powershell
.\frontend\.venv\Scripts\python.exe docs/tools/capture_manual.py tickets ticket cobrar
```

El capturador inicia Flet en `127.0.0.1:8767` y un Chrome sin ventana con depuración en `127.0.0.1:9227`. Cierra los procesos que inicia al terminar. Ambos puertos deben estar libres. El perfil aislado y los archivos temporales se guardan dentro de `.venv-codex/`, excluido de Git.

`manual_preview.py` prepara todas las escenas con datos ficticios en memoria. No carga los `.env`, no llama al backend, no crea ventas reales y no envía trabajos de impresión. En las escenas de acceso y sesión activa se muestran los controles del modo conectado con datos ficticios. La selección de Excel se prepara con un archivo de ejemplo; el selector nativo de archivos no forma parte de la captura.

Las capturas tienen un área de 1440 × 1080 píxeles. Si cambia la disposición de un formulario, actualiza sus coordenadas y leyendas en `manual_figures.py` después de revisar la captura correspondiente. Revisa también los acercamientos y las referencias que podrían quedar fuera del área visible.

## Generar las figuras y el PDF

Con ReportLab instalado y las fuentes Arial de Windows disponibles:

```powershell
.\frontend\.venv\Scripts\python.exe docs/tools/build_manual.py
```

El generador comprueba dimensiones y coordenadas, crea los SVG con su captura incrustada, actualiza los bloques identificados con `manual-figure` en Markdown y exporta el PDF. Las secciones y figuras aparecen también como marcadores de navegación del PDF. El texto situado fuera de los bloques generados se conserva.

Las figuras se definen con una escena, un título, el encabezado ante el que se insertan, un recorte y una lista de referencias. Cada referencia contiene su explicación, el punto del control y la posición de su número. La misma definición alimenta el SVG, la leyenda de Markdown y las anotaciones vectoriales del PDF.

No incluyas capturas de las credenciales locales ni datos de clientes, ventas o empleados reales al regenerar la documentación.
