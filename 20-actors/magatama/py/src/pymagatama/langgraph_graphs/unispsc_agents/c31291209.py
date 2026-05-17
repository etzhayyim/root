from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_material(state: ExtrusionState):
    alloy = state['spec_data'].get('material', '')
    return {'validation_results': [f'Alloy {alloy} verified against AMS standards']}

def check_tolerances(state: ExtrusionState):
    return {'is_compliant': True}

graph = StateGraph(ExtrusionState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_tolerances', check_tolerances)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_tolerances')
graph.add_edge('check_tolerances', END)
graph = graph.compile()