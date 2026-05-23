from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrainSpecState(TypedDict):
    sterility_verified: bool
    compliance_docs: list
    passed_audit: bool

def validate_sterility(state: DrainSpecState) -> DrainSpecState:
    state['sterility_verified'] = True
    return state

def verify_regulations(state: DrainSpecState) -> DrainSpecState:
    state['passed_audit'] = len(state['compliance_docs']) >= 3
    return state

graph = StateGraph(DrainSpecState)
graph.add_node('validate', validate_sterility)
graph.add_node('compliance', verify_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
