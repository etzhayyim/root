from typing import TypedDict
from langgraph.graph import StateGraph, END

class SilicaBrickState(TypedDict):
    spec_data: dict
    approved: bool
    validation_log: list

def validate_thermal_specs(state: SilicaBrickState):
    sio2 = state['spec_data'].get('sio2_content', 0)
    if sio2 >= 95.0:
        return {'approved': True, 'validation_log': ['SiO2 content within range']}
    return {'approved': False, 'validation_log': ['SiO2 content too low']}

def final_approval(state: SilicaBrickState):
    return {'validation_log': state['validation_log'] + ['Material approved for procurement']}

graph = StateGraph(SilicaBrickState)
graph.add_node('validate', validate_thermal_specs)
graph.add_node('approval', final_approval)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()