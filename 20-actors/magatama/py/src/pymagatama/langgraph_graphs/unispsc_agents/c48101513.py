from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatLampState(TypedDict):
    wattage: float
    safety_compliant: bool
    approved: bool

def validate_specs(state: HeatLampState):
    is_safe = state['wattage'] <= 3000
    return {'safety_compliant': is_safe}

def approval_step(state: HeatLampState):
    return {'approved': state['safety_compliant']}

graph = StateGraph(HeatLampState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
