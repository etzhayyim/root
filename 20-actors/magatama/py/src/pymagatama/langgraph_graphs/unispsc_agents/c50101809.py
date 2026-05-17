from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrangeProcurementState(TypedDict):
    brics_level: float
    pesticide_test_passed: bool
    temperature_compliant: bool
    status: str

def validate_quality(state: OrangeProcurementState):
    if state['brics_level'] >= 10.0 and state['pesticide_test_passed']:
        return {'status': 'QUALITY_APPROVED'}
    return {'status': 'REJECTED'}

def check_logistics(state: OrangeProcurementState):
    if state['temperature_compliant']:
        return {'status': 'READY_FOR_SHIPMENT'}
    return {'status': 'LOGISTICS_HALTED'}

graph = StateGraph(OrangeProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('logistics', check_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()