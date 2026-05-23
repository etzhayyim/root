from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ArthrographyState(TypedDict):
    part_number: str
    compliance_docs: List[str]
    is_sterile: bool
    is_approved: bool

def validate_sterility(state: ArthrographyState):
    state['is_sterile'] = True
    return state

def verify_compliance(state: ArthrographyState):
    state['is_approved'] = len(state['compliance_docs']) >= 3
    return state

graph = StateGraph(ArthrographyState)
graph.add_node('validate_sterility', validate_sterility)
graph.add_node('verify_compliance', verify_compliance)
graph.set_entry_point('validate_sterility')
graph.add_edge('validate_sterility', 'verify_compliance')
graph.add_edge('verify_compliance', END)
compile = graph.compile()
