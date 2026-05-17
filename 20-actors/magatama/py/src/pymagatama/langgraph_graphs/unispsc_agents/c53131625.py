from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NetState(TypedDict):
    material: str
    compliance_docs: List[str]
    validation_score: float

def validate_material(state: NetState):
    state['validation_score'] = 1.0 if 'non-woven' in state['material'].lower() else 0.5
    return state

def check_compliance(state: NetState):
    state['validation_score'] *= 1.0 if len(state['compliance_docs']) > 0 else 0.0
    return state

graph = StateGraph(NetState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()