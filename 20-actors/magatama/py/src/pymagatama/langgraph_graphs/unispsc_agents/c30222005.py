from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    facility_type: str
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: ProcurementState):
    state['approved'] = len(state['compliance_docs']) >= 3
    return state

def construction_planning(state: ProcurementState):
    print(f'Planning for {state['facility_type']}...')
    return {'approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('plan', construction_planning)
graph.set_entry_point('validate')
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph = graph.compile()