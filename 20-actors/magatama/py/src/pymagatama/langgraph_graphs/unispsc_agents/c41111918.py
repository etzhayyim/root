from typing import TypedDict
from langgraph.graph import StateGraph, END

class GyroState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_tech_specs(state: GyroState):
    drift = state['spec_data'].get('drift_rate', 1.0)
    state['validation_result'] = drift < 0.5
    return state

def check_export_control(state: GyroState):
    if state['spec_data'].get('dual_use_rating', True):
        print('Triggering Export Control Review')
    return {'validation_result': True}

graph = StateGraph(GyroState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('export_check', check_export_control)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
