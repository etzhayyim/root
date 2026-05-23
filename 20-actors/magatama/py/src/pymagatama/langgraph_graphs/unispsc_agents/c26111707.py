from typing import TypedDict
from langgraph.graph import StateGraph, END

class BatteryProcurementState(TypedDict):
    voltage: float
    capacity: float
    hazmat_clearance: bool
    is_approved: bool

def validate_specs(state: BatteryProcurementState) -> BatteryProcurementState:
    state['is_approved'] = state['voltage'] > 0 and state['capacity'] > 0
    return state

def check_compliance(state: BatteryProcurementState) -> BatteryProcurementState:
    if not state.get('hazmat_clearance', False):
        state['is_approved'] = False
    return state

graph = StateGraph(BatteryProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
