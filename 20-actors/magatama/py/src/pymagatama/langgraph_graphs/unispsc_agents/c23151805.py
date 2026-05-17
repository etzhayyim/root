from typing import TypedDict
from langgraph.graph import StateGraph, END

class MachineState(TypedDict):
    tonnage: float
    safety_certs: list[str]
    approved: bool

def validate_specs(state: MachineState):
    state['approved'] = state['tonnage'] > 0 and 'ISO-23125' in state['safety_certs']
    return state

def route_verification(state: MachineState):
    return 'approved' if state['approved'] else END

graph = StateGraph(MachineState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()