from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    surface_resistivity: float
    thickness: float
    is_compliant: bool

def validate_specs(state: PackagingState):
    # Validate resistivity range (e.g., 10^5 to 10^11 ohms)
    compliant = 100000 <= state['surface_resistivity'] <= 100000000000 and state['thickness'] > 0
    return {'is_compliant': compliant}

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
