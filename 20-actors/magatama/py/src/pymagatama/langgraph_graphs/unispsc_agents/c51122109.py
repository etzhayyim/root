from typing import TypedDict
from langgraph.graph import StateGraph, END

class PapaverineState(TypedDict):
    purity: float
    has_coa: bool
    compliance_ok: bool

def validate_compliance(state: PapaverineState):
    if state['purity'] >= 99.0 and state['has_coa']:
        return {'compliance_ok': True}
    return {'compliance_ok': False}

graph = StateGraph(PapaverineState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()