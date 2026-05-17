from langgraph.graph import StateGraph, END
from typing import TypedDict
class ProcurementState(TypedDict):
    spec: dict
    validated: bool
    error: str
def validate_specs(state: ProcurementState):
    required = ['measurement_range', 'accuracy_tolerance']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing critical technical parameters'}
def check_calibration(state: ProcurementState):
    if state['spec'].get('calibration_certificate'):
        return {'validated': True}
    return {'validated': False, 'error': 'Calibration certificate required for compliance'}
graph = StateGraph(ProcurementState)
graph.add_node('val', validate_specs)
graph.add_node('cal', check_calibration)
graph.set_entry_point('val')
graph.add_edge('val', 'cal')
graph.add_edge('cal', END)
graph = graph.compile()