from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_number: str
    pressure_rating: float
    has_as9100_cert: bool
    approved_supplier: bool

def validate_specs(state: AircraftComponentState):
    if state['pressure_rating'] < 3000:
        return {'status': 'rejected', 'reason': 'insufficient_pressure'}
    return {'status': 'validated'}

def check_compliance(state: AircraftComponentState):
    if not state['has_as9100_cert'] or not state['approved_supplier']:
        return {'status': 'compliance_failure'}
    return {'status': 'ready_for_procurement'}

graph = StateGraph(AircraftComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
