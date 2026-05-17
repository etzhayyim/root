from typing import TypedDict
from langgraph.graph import StateGraph, END

class IndustrialTruckState(TypedDict):
    truck_id: str
    capacity: float
    safety_verified: bool
    maintenance_plan: str

def validate_specs(state: IndustrialTruckState):
    state['safety_verified'] = state['capacity'] > 0
    return state

def check_compliance(state: IndustrialTruckState):
    if state['safety_verified']:
        state['maintenance_plan'] = 'standard_annual'
    return state

graph = StateGraph(IndustrialTruckState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()