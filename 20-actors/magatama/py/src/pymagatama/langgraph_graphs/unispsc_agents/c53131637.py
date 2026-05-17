from typing import TypedDict
from langgraph.graph import StateGraph, END
class NursingPadState(TypedDict):
    material_certified: bool
    absorbency_passed: bool
    is_compliant: bool
def check_compliance(state: NursingPadState):
    state['is_compliant'] = state['material_certified'] and state['absorbency_passed']
    return 'compliant' if state['is_compliant'] else 'reject'
graph = StateGraph(NursingPadState)
graph.add_node('check', check_compliance)
graph.set_entry_point('check')
graph.add_edge('check', END)
graph = graph.compile()