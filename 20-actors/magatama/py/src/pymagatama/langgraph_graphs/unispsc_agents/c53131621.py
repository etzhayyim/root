from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NailClipperState(TypedDict):
    material: str
    blade_sharpness_test: bool
    sterilization_grade: bool
    qc_passed: bool

def validate_materials(state: NailClipperState):
    state['qc_passed'] = state['material'] == 'Stainless Steel' and state['blade_sharpness_test']
    return state

def check_compliance(state: NailClipperState):
    return {'qc_passed': state['qc_passed'] and state['sterilization_grade']}

graph = StateGraph(NailClipperState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
