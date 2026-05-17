from typing import TypedDict
from langgraph.graph import StateGraph, END

class MonitorArmState(TypedDict):
    vesa_compatible: bool
    max_weight: float
    weight_requirement: float

def validate_specs(state: MonitorArmState):
    if state['max_weight'] < state['weight_requirement']:
        return {'status': 'rejected'}
    return {'status': 'approved'}

graph = StateGraph(MonitorArmState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()