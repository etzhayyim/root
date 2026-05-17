from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GraphicsState(TypedDict):
    requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_format(state: GraphicsState):
    fmt = state['requirements'].get('format', 'unknown')
    log = f'Validating format: {fmt}'
    return {'validation_logs': [log], 'is_compliant': True}

def check_license(state: GraphicsState):
    lic = state['requirements'].get('license', 'none')
    log = f'Checking license: {lic}'
    return {'validation_logs': [log], 'is_compliant': True}

graph = StateGraph(GraphicsState)
graph.add_node('format_check', validate_format)
graph.add_node('license_check', check_license)
graph.set_entry_point('format_check')
graph.add_edge('format_check', 'license_check')
graph.add_edge('license_check', END)
graph = graph.compile()