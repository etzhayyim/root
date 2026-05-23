from typing import TypedDict
from langgraph.graph import StateGraph, END

class VendingMachineState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: VendingMachineState):
    state['approved'] = 'Food Safety Certification' in state['specs'] and state['specs']['Power'] > 0
    return state

def route(state: VendingMachineState):
    return 'process' if state['approved'] else END

graph = StateGraph(VendingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route)
graph.add_edge('process', END)
graph = graph.compile()
