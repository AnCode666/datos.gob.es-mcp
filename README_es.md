[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

# Datos.gob.es-MCP. Integración vía MCP con el portal de datos abiertos del Gobierno de España

**Datos.gob.es-mcp** permite consultar y analizar los más de 90,000 conjuntos de datos públicos disponibles en el portal [datos.gob.es](https://datos.gob.es/es/) directamente desde Claude AI y otros clientes MCP compatibles, utilizando el protocolo **Model Context Protocol (MCP)**.

Este servidor MCP expone herramientas para que los LLM puedan buscar, filtrar y acceder a datos abiertos de múltiples sectores.

## Características principales

- Búsqueda de conjuntos de datos por **palabras clave** en título, descripción y etiquetas.
- Listado de **datasets por categorías temáticas** (medio ambiente, transporte, educación, etc.)
- Acceso a **metadatos detallados** de cada conjunto de datos.
- Consulta de **distribuciones disponibles** (formatos y URLs de acceso)
- Ejecución de **consultas SPARQL personalizadas** contra el endpoint oficial de SPARQL.

## Instalación

### Instalar desde uv

### Prerrequisitos

- Python 3.10 o superior.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

### Instalación de uv

Lo primero que hay que hacer es instalar `uv`, que es un gestor de paquetes para Python.
**Se instala desde la consola**.

En MAC y Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

En Windows:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

También se puede instalar con pip:

```bash
pip install uv
```

Para más información sobre la instalación de **uv**, consulta la [documentación oficial](https://docs.astral.sh/uv/getting-started/installation/).

## Integración con clientes como Claude para Escritorio

Una vez que tenemos **uv** instalado, ya podemos usar el servidor MCP desde cualquier cliente compatible, como Claude para Escritorio, en cuyo caso los pasos a seguir son los siguientes:

1. Ve a **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**.
2. Agrega el siguiente bloque de código dentro de `"mcpServers"`:

```json
"datos_gob_es_mcp": {
    "command": "uvx",
    "args": [
        "datos_gob_es_mcp"
    ]
}
```

3. Si ya tienes otro servidor MCP configurado en tu cliente, separa cada servidor con una coma `,`.

En general, para integrarlo en cualquier otro cliente compatible con MCP, como pueden ser Cursor, CODEGPT o Roo Code, solamente hay que ir a la correspondiente configuración de los servidores MCP del cliente y añadir el mismo bloque de código.

## Ejemplos de uso

Una vez configurado correctamente, podrás pedirle cosas como:

```text
- "Busca conjuntos de datos sobre transporte público en Madrid"
- "Lista los datasets más recientes publicados por el Ayuntamiento de Barcelona"
- "Muestra los detalles del dataset con URI https://datos.gob.es/es/catalogo/l01330241-padron-de-vehiculos-ano-2023-autobuses"
---
