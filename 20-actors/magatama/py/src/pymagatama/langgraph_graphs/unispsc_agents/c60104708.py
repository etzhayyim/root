from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasDiffusionState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: GasDiffusionState):
    required = ['Material-Compatibility', 'Pressure-Rating']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_export(state: GasDiffusionState):
    # Dual-use oversight logic
    print('Checking dual-use export regulations...')
    return state

graph = StateGraph(GasDiffusionState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()