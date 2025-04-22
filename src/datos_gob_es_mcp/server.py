from typing import Any, Dict
import httpx
import json
import logging
from mcp.server.fastmcp import FastMCP

# Init logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DatosGobEsMCPServer")

# Init FastMCP server
mcp = FastMCP(
    "datosgob-mcp",
    description="MCP server for querying the Spanish Government Open Data Portal (datos.gob.es) via SPARQL"
)

# Constants
SPARQL_ENDPOINT = "https://datos.gob.es/virtuoso/sparql"

# Prefixes for SPARQL queries
PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

async def make_sparql_request(query: str, format: str = "json") -> dict[str, Any] | None:
    """Make a request to the SPARQL endpoint with proper error handling."""
    logger.info(f"Attempting SPARQL query with format {format}") # More descriptive log

    params = {
        "query": query,
        "format": format
    }
    # Dynamic accept header based on format, default to json if not specified
    accept_header = f"application/sparql-results+{format}" if format else "application/sparql-results+json"
    headers = {
        "Accept": accept_header,
        "User-Agent": "DatosGobEsMCPServer/1.1" # Updated User-Agent
    }

    # Set timeout on client initialization
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Use params argument for automatic URL encoding
            response = await client.get(SPARQL_ENDPOINT, params=params, headers=headers)
            response.raise_for_status() # Check for HTTP errors (4xx or 5xx)

            # Parse response based on format
            if format == "json":
                # Handle potential JSON decoding errors
                try:
                    return response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to decode JSON response: {json_err}")
                    logger.debug(f"Response text: {response.text}")
                    return None
            else:
                # For non-JSON, return raw text content
                return {"content": response.text, "format": format}

        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}")
            return None
        except httpx.RequestError as req_err:
            # Handles connection errors, timeouts, etc.
            logger.error(f"Request error connecting to SPARQL endpoint: {req_err}")
            return None
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred during SPARQL request: {e}", exc_info=True)
            return None

def format_dataset_results(data: Dict) -> str:
    """Format dataset results into a readable string."""
    if not data or "results" not in data or "bindings" not in data["results"]:
        return "No results found."
    
    results = []
    for binding in data["results"]["bindings"]:
        dataset_info = {}
        
        # Extract common fields
        if "dataset" in binding:
            dataset_info["URI"] = binding["dataset"]["value"]
        
        if "title" in binding:
            dataset_info["Title"] = binding["title"]["value"]
        
        if "description" in binding:
            dataset_info["Description"] = binding["description"]["value"]
            
        if "publisher" in binding:
            dataset_info["Publisher"] = binding["publisher"]["value"]
            
        if "date" in binding:
            dataset_info["Date"] = binding["date"]["value"]
            
        if "theme" in binding:
            dataset_info["Theme"] = binding["theme"]["value"]
        
        # Format this dataset entry
        entry = []
        for key, value in dataset_info.items():
            # Truncate overly long descriptions
            if key == "Description" and len(value) > 200:
                value = value[:197] + "..."
            entry.append(f"{key}: {value}")
        
        results.append("\n".join(entry))
    
    return "\n\n".join(results)

def format_publisher_results(data: Dict) -> str:
    """Format publisher results into a readable string."""
    if not data or "results" not in data or "bindings" not in data["results"]:
        return "No results found."
    
    results = []
    for binding in data["results"]["bindings"]:
        publisher_info = {}
        
        if "publisher" in binding:
            publisher_info["URI"] = binding["publisher"]["value"]
        
        if "name" in binding:
            publisher_info["Name"] = binding["name"]["value"]
            
        if "type" in binding:
            publisher_info["Type"] = binding["type"]["value"].split("#")[-1]
        
        # Format this publisher entry
        entry = []
        for key, value in publisher_info.items():
            entry.append(f"{key}: {value}")
        
        results.append("\n".join(entry))
    
    return "\n\n".join(results)

def format_theme_results(data: Dict) -> str:
    """Format theme results into a readable string."""
    if not data or "results" not in data or "bindings" not in data["results"]:
        return "No results found."
    
    results = []
    for binding in data["results"]["bindings"]:
        if "theme" in binding and "label" in binding:
            theme_uri = binding["theme"]["value"]
            theme_label = binding["label"]["value"]
            results.append(f"{theme_label} ({theme_uri})")
    
    return "\n".join(results)

@mcp.tool()
async def list_datasets(limit: int = 10) -> str:
    """List datasets available in the Spanish Government Open Data Portal.
    
    Args:
        limit: Maximum number of datasets to return (default: 10)
    """
    query = f"""
    {PREFIXES}
    
    SELECT DISTINCT ?dataset ?title ?description
    WHERE {{
      ?dataset a dcat:Dataset .
      ?dataset dct:title ?title .
      OPTIONAL {{ ?dataset dct:description ?description }}
      FILTER(LANG(?title) = "es")
    }}
    LIMIT {limit}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return "No dataset data could be obtained."
    
    result = f"Listing {limit} datasets from datos.gob.es:\n\n"
    result += format_dataset_results(data)
    
    return result

@mcp.tool()
async def search_datasets(keyword: str, limit: int = 10) -> str:
    """Search datasets by keyword in title, description, and keywords/tags.

    Args:
        keyword: Keyword to search for (case-insensitive).
        limit: Maximum number of datasets to return (default: 10).
    """
    if not keyword:
        return "Please provide a keyword to search for."

    # Escape potential regex special characters in the keyword for safety
    # Simple escaping for common cases, might need more robust solution if complex regex is expected in keywords
    safe_keyword = keyword.replace('\\', '\\\\').replace('"', '\\"').replace('.', '\\.').replace('*', '\\*').replace('+', '\\+').replace('?', '\\?').replace('(', '\\(').replace(')', '\\)').replace('[', '\\[').replace(']', '\\]').replace('{', '\\{').replace('}', '\\}')

    query = f"""
    {PREFIXES}

    SELECT DISTINCT ?dataset ?title ?description
    WHERE {{
      ?dataset a dcat:Dataset .
      ?dataset dct:title ?title .
      OPTIONAL {{ ?dataset dct:description ?description . }}
      OPTIONAL {{ ?dataset dcat:keyword ?keyword_val . }} # Include keywords/tags

      # Combine text fields safely using COALESCE for optional fields
      BIND(COALESCE(STR(?title), "") AS ?title_str)
      BIND(COALESCE(STR(?description), "") AS ?desc_str)
      BIND(COALESCE(STR(?keyword_val), "") AS ?key_str)
      # Combine and convert to lowercase for case-insensitive search
      BIND(LCASE(CONCAT(?title_str, " ", ?desc_str, " ", ?key_str)) AS ?search_text)

      # Apply the regex filter to the combined text
      FILTER(REGEX(?search_text, "{safe_keyword}", "i"))

      # Ensure title is in Spanish
      FILTER(LANG(?title) = "es")
    }}
    LIMIT {limit}
    """

    logger.info(f"Searching datasets with keyword: '{keyword}' (safe: '{safe_keyword}')")
    data = await make_sparql_request(query)

    # Check specifically if bindings array is present and non-empty
    if not data or "results" not in data or "bindings" not in data["results"] or not data["results"]["bindings"]:
        return f"No datasets found matching keyword: '{keyword}'."

    count = len(data["results"]["bindings"])
    result = f"Found {count} datasets matching '{keyword}':\n\n"
    result += format_dataset_results(data)

    return result

@mcp.tool()
async def get_dataset_details(dataset_uri: str) -> str:
    """Get detailed information about a specific dataset.
    
    Args:
        dataset_uri: URI of the dataset to get details for
    """
    query = f"""
    {PREFIXES}
    
    SELECT ?property ?value
    WHERE {{
      <{dataset_uri}> ?property ?value .
    }}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return f"No details found for dataset {dataset_uri}."
    
    result = f"Details for dataset: {dataset_uri}\n\n"
    
    if "results" in data and "bindings" in data["results"]:
        properties = {}
        for binding in data["results"]["bindings"]:
            if "property" in binding and "value" in binding:
                prop = binding["property"]["value"]
                val = binding["value"]["value"]
                
                # Extract the property name from the URI
                prop_name = prop.split("/")[-1]
                if "#" in prop_name:
                    prop_name = prop_name.split("#")[-1]
                
                properties[prop_name] = val
        
        # Format prioritized properties first
        priority_props = ["title", "description", "issued", "modified", "publisher", "theme"]
        for prop in priority_props:
            if prop in properties:
                result += f"{prop.capitalize()}: {properties[prop]}\n"
                del properties[prop]
        
        # Then add remaining properties
        for prop, val in properties.items():
            result += f"{prop}: {val}\n"
    
    return result

@mcp.tool()
async def list_publishers(limit: int = 10) -> str:
    """List publishers (organizations) that publish datasets.
    
    Args:
        limit: Maximum number of publishers to return (default: 10)
    """
    query = f"""
    {PREFIXES}
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?publisher ?name
    WHERE {{
      ?dataset a dcat:Dataset .
      ?dataset dct:publisher ?publisher .
      # Usar skos:prefLabel para el nombre del publicador
      ?publisher skos:prefLabel ?name .
      # Se elimina el filtro específico para listar todos
    }}
    LIMIT {limit}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return "No publisher data could be obtained."
    
    result = f"Listing {limit} publishers:\n\n"
    result += format_publisher_results(data)
    
    return result

@mcp.tool()
async def get_publisher_datasets(publisher_uri: str, limit: int = 10) -> str:
    """Get datasets published by a specific organization.
    
    Args:
        publisher_uri: URI of the publisher
        limit: Maximum number of datasets to return (default: 10)
    """
    query = f"""
    {PREFIXES}
    
    SELECT DISTINCT ?dataset ?title ?description
    WHERE {{
      ?dataset a dcat:Dataset .
      ?dataset dct:publisher <{publisher_uri}> .
      ?dataset dct:title ?title .
      OPTIONAL {{ ?dataset dct:description ?description }}
      FILTER(LANG(?title) = "es")
    }}
    LIMIT {limit}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return f"No datasets found for publisher {publisher_uri}."
    
    result = f"Datasets published by {publisher_uri}:\n\n"
    result += format_dataset_results(data)
    
    return result

@mcp.tool()
async def list_themes() -> str:
    """List all themes/categories available in the data portal."""
    query = f"""
    {PREFIXES}
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?theme ?label
    WHERE {{
      # Buscar directamente conceptos de tema (skos:Concept)
      ?theme a skos:Concept .
      # Usar skos:prefLabel para la etiqueta del tema
      ?theme skos:prefLabel ?label .
      # Opcional: Filtrar por temas realmente usados en datasets
      # FILTER EXISTS {{ ?dataset dcat:theme ?theme . }}
      FILTER(LANG(?label) = "es")
    }}
    ORDER BY ?label
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return "No theme data could be obtained."
    
    result = "Available themes/categories:\n\n"
    result += format_theme_results(data)
    
    return result

@mcp.tool()
async def get_datasets_by_theme(theme_uri: str, limit: int = 10) -> str:
    """Get datasets belonging to a specific theme/category.
    
    Args:
        theme_uri: URI of the theme
        limit: Maximum number of datasets to return (default: 10)
    """
    query = f"""
    {PREFIXES}
    
    SELECT DISTINCT ?dataset ?title ?description
    WHERE {{
      ?dataset a dcat:Dataset .
      ?dataset dcat:theme <{theme_uri}> .
      ?dataset dct:title ?title .
      OPTIONAL {{ ?dataset dct:description ?description }}
      FILTER(LANG(?title) = "es")
    }}
    LIMIT {limit}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return f"No datasets found for theme {theme_uri}."
    
    result = f"Datasets in theme {theme_uri}:\n\n"
    result += format_dataset_results(data)
    
    return result

@mcp.tool()
async def get_latest_datasets(limit: int = 10) -> str:
    """Get the most recently published datasets.
    
    Args:
        limit: Maximum number of datasets to return (default: 10)
    """
    query = f"""
    {PREFIXES}
    
    SELECT DISTINCT ?dataset ?title ?description ?date
    WHERE {{
      ?dataset a dcat:Dataset .
      ?dataset dct:title ?title .
      ?dataset dct:issued ?date .
      OPTIONAL {{ ?dataset dct:description ?description }}
      FILTER(LANG(?title) = "es")
    }}
    ORDER BY DESC(?date)
    LIMIT {limit}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return "No dataset data could be obtained."
    
    result = f"Latest {limit} datasets:\n\n"
    result += format_dataset_results(data)
    
    return result

@mcp.tool()
async def run_custom_sparql(sparql_query: str) -> str:
    """Run a custom SPARQL query against the datos.gob.es endpoint.
    
    Args:
        sparql_query: SPARQL query string (must be valid SPARQL)
    """
    # Add common prefixes if they're not in the query
    if not any(prefix in sparql_query for prefix in ["PREFIX ", "prefix "]):
        sparql_query = PREFIXES + sparql_query
    
    data = await make_sparql_request(sparql_query)
    
    if not data:
        return "Failed to execute SPARQL query."
    
    # Format the raw results as a readable string
    result = "Custom SPARQL query results:\n\n"
    
    if "results" in data and "bindings" in data["results"]:
        if len(data["results"]["bindings"]) == 0:
            return "Query executed successfully, but no results were returned."
        
        # Get all the variables used in the results
        variables = data["head"]["vars"]
        
        # Format each row of results
        rows = []
        for binding in data["results"]["bindings"]:
            row_parts = []
            for var in variables:
                if var in binding:
                    value = binding[var]["value"]
                    row_parts.append(f"{var}: {value}")
            rows.append("\n".join(row_parts))
        
        result += "\n\n".join(rows)
    else:
        # Handle non-standard responses
        result += json.dumps(data, indent=2)
    
    return result

@mcp.tool()
async def get_dataset_distributions(dataset_uri: str) -> str:
    """Get available distributions (file formats) for a specific dataset.
    
    Args:
        dataset_uri: URI of the dataset
    """
    query = f"""
    {PREFIXES}
    
    SELECT ?distribution ?title ?format ?accessURL ?downloadURL
    WHERE {{
      <{dataset_uri}> dcat:distribution ?distribution .
      OPTIONAL {{ ?distribution dct:title ?title }}
      OPTIONAL {{ ?distribution dct:format ?format }}
      OPTIONAL {{ ?distribution dcat:accessURL ?accessURL }}
      OPTIONAL {{ ?distribution dcat:downloadURL ?downloadURL }}
    }}
    """
    
    data = await make_sparql_request(query)
    
    if not data:
        return f"No distribution data found for dataset {dataset_uri}."
    
    result = f"Available distributions for dataset: {dataset_uri}\n\n"
    
    if "results" in data and "bindings" in data["results"]:
        if len(data["results"]["bindings"]) == 0:
            return "No distributions found for this dataset."
        
        for i, binding in enumerate(data["results"]["bindings"], 1):
            result += f"Distribution {i}:\n"
            
            if "distribution" in binding:
                result += f"URI: {binding['distribution']['value']}\n"
                
            if "title" in binding:
                result += f"Title: {binding['title']['value']}\n"
                
            if "format" in binding:
                result += f"Format: {binding['format']['value']}\n"
                
            if "accessURL" in binding:
                result += f"Access URL: {binding['accessURL']['value']}\n"
                
            if "downloadURL" in binding:
                result += f"Download URL: {binding['downloadURL']['value']}\n"
                
            result += "\n"
    
    return result.strip()


def main():
    """Start the MCP server"""
    mcp.run()

if __name__ == "__main__":
    mcp.run(transport='stdio')