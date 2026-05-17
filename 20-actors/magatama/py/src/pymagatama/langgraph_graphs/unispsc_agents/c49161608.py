from typing import TypedDict
from langgraph.graph import StateGraph, END

class VolleyballState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: VolleyballState):
    s = state['spec_data']
    compliant = (260 <= s.get('weight', 0) <= 280) and (65 <= s.get('circumference', 0) <= 67)
    return {'is_compliant': compliant}

graph = StateGraph(VolleyballState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()