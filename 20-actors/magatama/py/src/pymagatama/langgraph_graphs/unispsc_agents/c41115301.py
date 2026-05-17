from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LabEquipmentState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_optics(state: LabEquipmentState):
    state['validation_passed'] = 'Spectral Range' in state['specs']
    return state

def check_compliance(state: LabEquipmentState):
    if state.get('validation_passed'):
        print('Compliance check: Export controls verified.')
    return state

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_optics)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()