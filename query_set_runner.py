# Interactive SparqlQuerySet Runner
# Author: Wolfgang Fahl / bitplan.com
# Runs queries from YAML configuration files using SPARQL
# WF 2025-11-16
import requests
import yaml
from lodstorage.sparql import SPARQL
from lodstorage.query import Query, QueryManager
from typing import Optional, Dict, List
import sys


class QuerySetRunner:
    """
    Runs queries from a YAML configuration file using specified language e.g. SPARQL
    """

    def __init__(self, yaml_url: str, endpoints: Dict[str, Dict] = None):
        """
        Initialize with YAML configuration URL.

        Args:
            yaml_url: URL to the YAML file containing query definitions
            endpoints: Dictionary of endpoint configurations
        """
        self.yaml_url = yaml_url
        self.config = None
        self.query_manager = None
        self.endpoints = endpoints or {}

    def download_config(self) -> dict:
        """
        Download and parse the YAML configuration.

        Returns:
            Parsed YAML configuration as dictionary
        """
        response = requests.get(self.yaml_url)
        response.raise_for_status()
        config = yaml.safe_load(response.text)
        self.config = config
        return config

    def get_query_names(self) -> List[str]:
        """
        Get list of available query names.

        Returns:
            List of query names
        """
        if self.config is None:
            self.download_config()
        return list(self.config.keys())

    def get_endpoint_names(self) -> List[str]:
        """
        Get list of available endpoint names.

        Returns:
            List of endpoint names
        """
        return list(self.endpoints.keys())

    def run_query(self, query_name: str, endpoint_name: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Run a specific query by name.

        Args:
            query_name: Name of the query to run
            endpoint_name: Name of the endpoint to use
            params: Optional parameters for the query

        Returns:
            Query results as list of dictionaries
        """
        query_obj = self.config.get(query_name)
        if query_obj is None:
            raise ValueError(f"Query '{query_name}' not found")

        query_text = query_obj.get('query') or query_obj.get('sparql')

        if query_text is None:
            raise ValueError(f"No query text found for '{query_name}'")

        endpoint_config = self.endpoints.get(endpoint_name)
        if endpoint_config is None:
            raise ValueError(f"Endpoint '{endpoint_name}' not found")

        endpoint_url = endpoint_config.get('endpoint')
        calls_per_minute = endpoint_config.get('calls_per_minute')

        sparql = SPARQL(endpoint_url, calls_per_minute=calls_per_minute)
        results = sparql.queryAsListOfDicts(query_text, param_dict=params)

        return results


class QuerySetRunnerUI:
    """
    Jupyter notebook UI for QuerySetRunner
    """

    def __init__(self, runner: QuerySetRunner):
        """
        Initialize UI with a QuerySetRunner instance.

        Args:
            runner: QuerySetRunner instance to use
        """
        self.runner = runner
        self.widgets = None

    def create_widgets(self):
        """Create and return Jupyter widgets for interactive query running."""
        import ipywidgets as widgets
        from IPython.display import display
        import pandas as pd

        endpoint_selector = widgets.Dropdown(
            options=self.runner.get_endpoint_names(),
            description='Endpoint:',
            style={'description_width': 'initial'}
        )

        query_selector = widgets.Dropdown(
            options=self.runner.get_query_names(),
            description='Query:',
            style={'description_width': 'initial'}
        )

        limit_input = widgets.IntText(
            value=10,
            description='Limit:',
            disabled=False
        )

        run_button = widgets.Button(
            description='Run Query',
            button_style='success'
        )

        output = widgets.Output()

        def on_button_click(b):
            """Handle button click event."""
            with output:
                output.clear_output()
                endpoint_name = endpoint_selector.value
                query_name = query_selector.value
                limit_value = limit_input.value

                print(f"Running query: {query_name} on {endpoint_name}")
                results = self.runner.run_query(query_name, endpoint_name, params={"limit": limit_value})

                df = pd.DataFrame(results)
                display(df)

        run_button.on_click(on_button_click)

        self.widgets = {
            'endpoint_selector': endpoint_selector,
            'query_selector': query_selector,
            'limit_input': limit_input,
            'run_button': run_button,
            'output': output
        }

        return self.widgets

    def display(self):
        """Display all widgets in the notebook."""
        from IPython.display import display

        if self.widgets is None:
            self.create_widgets()

        for widget in self.widgets.values():
            display(widget)


def get_default_config() -> tuple:
    """
    Get default configuration for endpoints and YAML URL.

    Returns:
        Tuple of (yaml_url, endpoints)
    """
    endpoints = {
        'wikidata': {
            'endpoint': 'https://query.wikidata.org/sparql',
            'website': 'https://query.wikidata.org'
        }
    }
    yaml_url = "https://raw.githubusercontent.com/SEEKCommons/resource-hub/refs/heads/main/documentation/query_objects.yaml"
    return yaml_url, endpoints


if __name__ == "__main__":
    # Check if running in Jupyter
    try:
        get_ipython()
        in_notebook = True
    except NameError:
        in_notebook = False

    if in_notebook:
        # Running in Jupyter - create UI
        yaml_url, endpoints = get_default_config()
        runner = QuerySetRunner(yaml_url, endpoints=endpoints)
        runner.download_config()

        ui = QuerySetRunnerUI(runner)
        ui.display()
    else:
        # Running from command line - show usage
        print("QuerySetRunner - SPARQL Query Runner")
        print("\nUsage in Jupyter Notebook:")
        print("  %run query_set_runner.py")
        print("\nUsage in Python script:")
        print("  from query_set_runner import QuerySetRunner, get_default_config")
        print("  yaml_url, endpoints = get_default_config()")
        print("  runner = QuerySetRunner(yaml_url, endpoints=endpoints)")
        print("  runner.download_config()")
        print("  results = runner.run_query('query_name', 'wikidata', params={'limit': 10})")
