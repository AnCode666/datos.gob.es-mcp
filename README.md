[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/ancode666-datos-gob-es-mcp-badge.png)](https://mseep.ai/app/ancode666-datos-gob-es-mcp)

[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/726f4340-a758-4d9f-8f56-b2130dcf83c4)

# Datos.gob.es-MCP. MCP integration with the Spanish Government Open Data Portal

**Datos.gob.es-mcp** enables querying and analyzing over 90,000 public datasets available on the [datos.gob.es](https://datos.gob.es/es/) portal directly from Claude AI and other compatible MCP clients using the **Model Context Protocol (MCP)**.

This MCP server exposes tools for LLMs to search, filter, and access open data across multiple sectors.

## Main features

- **Keyword search** across dataset titles, descriptions and tags.
- **Thematic category filtering** (environment, transportation, education, etc.)
- **Detailed metadata access** for each dataset.
- **Available distributions** listing (formats and access URLs)
- **Custom SPARQL queries** execution against the official SPARQL endpoint.

## Installation

### Install via uv

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### uv Installation

First install `uv`, a modern Python package manager.
**Install from command line**:

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

For more information about installing **uv**, visit the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

## Integration with clients like Claude for Desktop

Once **uv** is installed, you can use the MCP server with any compatible client like Claude Desktop. Configuration steps:

1. Go to **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**
2. Add this configuration block under `"mcpServers"`:

```json
"datos_gob_es_mcp": {
    "command": "uvx",
    "args": [
        "datos_gob_es_mcp"
    ]
}
```

3. If you have other MCP servers configured, separate them with commas `,`

For other MCP-compatible clients like Cursor, CODEGPT or Roo Code, add the same configuration block to their respective MCP server settings.

## Usage Examples

Once properly configured, you can request operations like:

```text
- "Search for public transportation datasets in Madrid"
- "List latest datasets published by Barcelona City Council"
- "Show details for dataset with URI https://datos.gob.es/es/catalogo/l01330241-padron-de-vehiculos-ano-2023-autobuses"
---
