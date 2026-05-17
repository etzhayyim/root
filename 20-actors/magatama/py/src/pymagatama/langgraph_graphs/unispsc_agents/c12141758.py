from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SolventState(TypedDict):
    purity_level: float
    contaminants: List[str]
    validation_status: str

def check_purity(state: SolventState):
    if state['purity_level'] >= 99.999:
        return {'validation_status': 'PASS'}
    return {'validation_status': 'FAIL'}

def audit_contaminants(state: SolventState):
    if not state['contaminants']:
        return {'validation_status': 'AUDIT_CLEAN'}
    return {'validation_status': 'AUDIT_FAILED'}

graph = StateGraph(SolventState)
graph.add_node('check_purity', check_purity)
graph.add_node('audit_contaminants', audit_contaminants)
graph.set_entry_point('check_purity')
graph.add_edge('check_purity', 'audit_contaminants')
graph.add_edge('audit_contaminants', END)
graph = graph.compile()