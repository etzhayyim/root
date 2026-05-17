from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoosterState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: BoosterState):
    required = ['Voltage', 'Pressure', 'Certification']
    state['is_compliant'] = all(key in state['specs'] for key in required)
    return state

def check_export_controls(state: BoosterState):
    if state.get('is_compliant', False):
        print('Checking dual-use export compliance...')
    return state

graph = StateGraph(BoosterState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()