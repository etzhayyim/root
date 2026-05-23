from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TiltProcurementState(TypedDict):
    load_capacity: float
    tilt_angle: int
    safety_compliant: bool
    approved: bool

def validate_specs(state: TiltProcurementState):
    if state['load_capacity'] > 0 and 0 <= state['tilt_angle'] <= 180:
        return {'safety_compliant': True}
    return {'safety_compliant': False}

def approval_check(state: TiltProcurementState):
    return {'approved': state['safety_compliant']}

graph = StateGraph(TiltProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
