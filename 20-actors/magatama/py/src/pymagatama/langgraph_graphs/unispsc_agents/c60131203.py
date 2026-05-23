from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FluteProcurementState(TypedDict):
    material: str
    tuning_standard: str
    inspection_passed: bool

def validate_materials(state: FluteProcurementState):
    state['inspection_passed'] = state['material'] in ['Silver', 'Nickel-Plated', 'Grenadilla']
    return state

def check_tuning(state: FluteProcurementState):
    if state['inspection_passed']:
        state['inspection_passed'] = state['tuning_standard'] == 'A=440Hz'
    return state

graph = StateGraph(FluteProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('tune_check', check_tuning)
graph.set_entry_point('validate')
graph.add_edge('validate', 'tune_check')
graph.add_edge('tune_check', END)
graph = graph.compile()
