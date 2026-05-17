from typing import TypedDict
from langgraph.graph import StateGraph, END

class OxfendazoleState(TypedDict):
    purity_level: float
    compliance_docs: list
    status: str

def validate_purity(state: OxfendazoleState):
    state['status'] = 'Validated' if state['purity_level'] >= 99.0 else 'Rejected'
    return state

def check_compliance(state: OxfendazoleState):
    if len(state['compliance_docs']) < 3:
        state['status'] = 'Missing Documentation'
    return state

graph = StateGraph(OxfendazoleState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()