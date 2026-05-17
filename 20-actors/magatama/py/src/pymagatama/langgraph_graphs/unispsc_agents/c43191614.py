from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ImageSoftwareState(TypedDict):
    software_name: str
    license_key: str
    validation_status: bool
    tasks: Annotated[Sequence[str], operator.add]

def validate_license(state: ImageSoftwareState):
    # Simulate license key verification logic
    is_valid = len(state['license_key']) > 10
    return {'validation_status': is_valid}

def perform_install(state: ImageSoftwareState):
    if state['validation_status']:
        return {'tasks': ['License validated', 'Installer initialized', 'Deployment complete']}
    return {'tasks': ['Deployment failed: Invalid License']}

def build_graph():
    graph = StateGraph(ImageSoftwareState)
    graph.add_node('validate', validate_license)
    graph.add_node('install', perform_install)
    graph.add_edge('validate', 'install')
    graph.add_edge('install', END)
    graph.set_entry_point('validate')
    return graph.compile()

graph = build_graph()