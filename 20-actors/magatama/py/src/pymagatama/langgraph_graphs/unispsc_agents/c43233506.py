from typing import TypedDict
from langgraph.graph import StateGraph, END

class MapSoftwareState(TypedDict):
    license_type: str
    geospatial_validation_passed: bool
    export_control_check: str

def validate_geodata_compliance(state: MapSoftwareState):
    state['geospatial_validation_passed'] = True
    return 'Validated'

def check_export_regulations(state: MapSoftwareState):
    state['export_control_check'] = 'Cleared'
    return 'Cleared'

graph = StateGraph(MapSoftwareState)
graph.add_node('validate', validate_geodata_compliance)
graph.add_node('export', check_export_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()