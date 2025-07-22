# News Scraper

Este proyecto permite **extraer titulares de noticias** de medios marplatenses y guardar los resultados en un archivo CSV.

---

## Requisitos previos

Antes de comenzar, asegurate de tener instalados:

- [Python 3.10 o superior](https://www.python.org/downloads/windows/)
- [Git para Windows](https://git-scm.com/download/win)

---

### Instalar Python

1. Ir a [python.org/downloads](https://www.python.org/downloads/)
2. Descargar el instalador de Windows (elegir 32 o 64 bits según tu computadora).
3. Ejecutar el instalador y **marcar la opción “Add Python to PATH”** antes de hacer clic en “Install Now”.
4. Al finalizar, abrir una consola (CMD o PowerShell) y escribir:

```sh
python --version
```

Deberías ver algo como: Python 3.11.6

### Instalar Git

1. Ir a [git-scm.com/download/win](git-scm.com/download/win)

2. La descarga empezará automáticamente. Instalar con la configuración por defecto.

3. Abrir una consola (CMD o PowerShell) y escribir:

```sh
git --version
```

## Instalación

### Clonar el repositorio

Abrí la consola y ejecutá:

```sh
git clone https://github.com/dPenedo/news_scraper.git
cd news_scraper
```

### Crear entorno virtual

Desde dentro de la carpeta del proyecto:

```sh
python -m venv venv
```

**Activar** el entorno virtual (esto cambia según la consola):

En CMD:

```sh
venv\Scripts\activate.bat
```

En PowerShell:

```sh
venv\Scripts\Activate.ps1
```

Deberías ver algo como (venv) al principio de la línea.

## Instalar dependencias

Con el entorno virtual activo:

```sh
pip install -r requirements.txt
```

### Uso

Con el entorno virtual activado, ejecutar:

```sh
python -m news_scraper
```

Los resultados se guardarán como archivo `.csv` en la carpeta del proyecto.

## Formato del archivo CSV

Cada fila representa una noticia. Las columnas son:

- Fecha

- Medio (1 = lacapitalmdp, 2 = 0223.com.ar, 3 = quedigital)

- Titular

- Zona_portada: depende del nombre que tome en cada medio

- Seccion: depende de cómo el medio clasifique sus secciones.
  - QueDigital: lo hace por secciones clásicas (sociedad, cultrua, deportes, ...)
  - 0223: utiliza etiquetas/tags menos precisas (Robo, Violencia, Intento de Femicidio,Clima)

- URL

## Info de la matriz

> Categoría general, subcategoría, actores, lugar geográfico y alineamiento político deben completarse manualmente o en una segunda etapa.

La matriz completa es la siguiente:

- **Fecha**
- **Medio**:
  - 1 = lacapitalmdp
  - 2 = 0223.com.ar
  - 3 = quedigital
- **titulo**
- Categoría general
- Subcategoría
- Actores mencionados
- Lugar geográfico referido
- alineamiento político o la tendencia pro/anti gubernamental
- Dudas: deben ser indicadas las dudas de codificación por medio de comentarios.
