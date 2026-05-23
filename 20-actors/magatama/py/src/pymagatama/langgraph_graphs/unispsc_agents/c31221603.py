from typing import TypedDict
from langgraph.graph import StateGraph, END

class TanninState(TypedDict):
    purity: float
    origin: str
    compliance_docs: bool

def validate_tannin(state: TanninState):
    if state['purity'] < 0.8: return 'invalid'
    return 'valid'

def check_compliance(state: TanninState):
    return {'compliance_docs': state.get('compliance_docs', False)}

graph = StateGraph(TanninState)
graph.add_node('validate', validate_tannin)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
