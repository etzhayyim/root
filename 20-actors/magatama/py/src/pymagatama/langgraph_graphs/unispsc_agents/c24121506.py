from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    surface_resistivity: float
    is_compliant: bool

def validate_esd_specs(state: PackagingState):
    # Threshold for antistatic packaging (typically < 1e5 ohms for conductive)
    state['is_compliant'] = state['surface_resistivity'] < 1e5
    return state

def route_verification(state: PackagingState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_esd_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()