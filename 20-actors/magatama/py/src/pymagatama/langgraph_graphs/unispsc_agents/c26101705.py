from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_specs(state: AircraftComponentState):
    # Simulate aerospace certification check
    required = ['AS9100', 'Material_Cert']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': all_present}

def route_verification(state: AircraftComponentState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(AircraftComponentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()