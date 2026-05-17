from typing import TypedDict
from langgraph.graph import StateGraph, END

class GearState(TypedDict):
    part_number: str
    compliance_docs: list
    is_airworthy: bool

def validate_compliance(state: GearState):
    state['is_airworthy'] = len(state['compliance_docs']) >= 3
    return {'is_airworthy': state['is_airworthy']}

def structural_check(state: GearState):
    return {'status': 'Safety checks completed' if state['is_airworthy'] else 'Flagged for Inspection'}

graph = StateGraph(GearState)
graph.add_node('validate', validate_compliance)
graph.add_node('safety', structural_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()