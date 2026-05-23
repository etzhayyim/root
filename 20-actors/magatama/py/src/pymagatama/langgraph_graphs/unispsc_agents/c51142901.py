from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_msds: bool
    is_compliant: bool
    hazard_check: str

def validate_purity(state: ChemicalState):
    state['is_compliant'] = state['purity'] >= 0.99 and state['has_msds']
    return {'is_compliant': state['is_compliant']}

def safety_gate(state: ChemicalState):
    state['hazard_check'] = 'PASSED' if state['is_compliant'] else 'FAILED'
    return {'hazard_check': state['hazard_check']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_gate)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
