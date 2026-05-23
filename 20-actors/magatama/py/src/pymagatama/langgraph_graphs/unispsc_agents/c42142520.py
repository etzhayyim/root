from typing import TypedDict
from langgraph.graph import StateGraph, END

class DispensingState(TypedDict):
    gauge: str
    material: str
    inspection_passed: bool

def validate_specs(state: DispensingState):
    # Simulate CAD/Spec validation for dispensing needle geometry
    state['inspection_passed'] = state['gauge'] in ['14G', '16G', '18G']
    return state

def determine_workflow(state: DispensingState):
    return 'process' if state['inspection_passed'] else END

def execute_processing(state: DispensingState):
    return state

graph = StateGraph(DispensingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', execute_processing)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', determine_workflow)
graph.add_edge('process', END)
graph = graph.compile()
