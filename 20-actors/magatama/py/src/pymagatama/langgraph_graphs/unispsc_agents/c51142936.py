from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity_level: float
    reg_compliant: bool
    lab_result: str

def validate_purity(state: PharmState):
    if state['purity_level'] >= 99.5:
        return {'lab_result': 'PASSED'}
    return {'lab_result': 'FAILED'}

def check_compliance(state: PharmState):
    state['reg_compliant'] = True
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()