from typing import TypedDict
from langgraph.graph import StateGraph, END

class VehicleState(TypedDict):
    vin: str
    compliance_check: bool
    approved: bool

def validate_vehicle(state: VehicleState):
    if len(state['vin']) == 17:
        return {'compliance_check': True}
    return {'compliance_check': False}

def approval_step(state: VehicleState):
    return {'approved': state['compliance_check']}

graph = StateGraph(VehicleState)
graph.add_node('validate', validate_vehicle)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
