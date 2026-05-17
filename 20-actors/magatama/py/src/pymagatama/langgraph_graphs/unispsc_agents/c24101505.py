from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PalletTruckState(TypedDict):
    capacity: int
    certified: bool
    approved: bool

def validate_specs(state: PalletTruckState):
    state['approved'] = state['capacity'] > 0 and state['certified']
    return state

def route_logic(state):
    return 'process' if state['approved'] else END

graph = StateGraph(PalletTruckState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
app = graph.compile()