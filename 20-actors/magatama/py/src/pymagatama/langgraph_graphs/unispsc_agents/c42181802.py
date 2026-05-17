from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OximeterState(TypedDict):
    cable_model: str
    compliance_docs: List[str]
    is_validated: bool

def validate_compliance(state: OximeterState):
    # Business logic for verifying medical compliance
    is_valid = 'ISO_80601' in state['compliance_docs']
    return {'is_validated': is_valid}

def routing_logic(state: OximeterState):
    return 'validate' if state['compliance_docs'] else END

graph = StateGraph(OximeterState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()