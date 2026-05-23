from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    bag_id: str
    tamper_evident: bool
    compliance_checked: bool

def validate_security_features(state: ProcurementState):
    state['compliance_checked'] = state['tamper_evident'] is True
    return {'compliance_checked': state['compliance_checked']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_security_features)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
