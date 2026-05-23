from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class WireState(TypedDict):
    spec_data: dict
    validation_log: List[str]
    approved: bool

def validate_tensile(state: WireState):
    strength = state['spec_data'].get('tensile_strength', 0)
    valid = 1500 <= strength <= 3000
    return {'validation_log': [f'Tensile strength check: {valid}'], 'approved': valid}

graph = StateGraph(WireState)
graph.add_node('validate', validate_tensile)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
