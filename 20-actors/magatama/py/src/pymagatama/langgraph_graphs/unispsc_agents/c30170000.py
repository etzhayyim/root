from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_materials(state: ProcurementState):
    specs = state['spec_data']
    logs = []
    if 'fire_rating' not in specs: logs.append('Missing fire rating')
    if 'thermal_u_value' not in specs: logs.append('Missing u-value')
    return {'validation_log': logs, 'is_compliant': len(logs) == 0}

graph = StateGraph(ProcurementState)
graph.add_node('validation', validate_materials)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()