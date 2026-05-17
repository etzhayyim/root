from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material_type: str
    weld_strength_psi: float
    inspection_passed: bool

def validate_specs(state: AssemblyState):
    state['inspection_passed'] = state['weld_strength_psi'] > 500
    return state

def check_compliance(state: AssemblyState):
    print(f'Compliance check for assembly: {state['inspection_passed']}')
    return {'inspection_passed': state['inspection_passed']}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()