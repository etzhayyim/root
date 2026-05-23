from typing import TypedDict
from langgraph.graph import StateGraph, END

class PistonRingState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: PistonRingState):
    required = ['material', 'diameter', 'gap_clearance']
    all_present = all(k in state['specs'] for k in required)
    return {'validated': all_present}

def approval_step(state: PistonRingState):
    return {'validated': state['validated']}

graph = StateGraph(PistonRingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
