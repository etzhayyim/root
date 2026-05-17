from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity: float
    safety_check_passed: bool
    compliance_docs: List[str]

def validate_chemistry(state: ProcurementState):
    state['safety_check_passed'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    state['compliance_docs'] = ['COA', 'MSDS'] if state['safety_check_passed'] else []
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemistry)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()