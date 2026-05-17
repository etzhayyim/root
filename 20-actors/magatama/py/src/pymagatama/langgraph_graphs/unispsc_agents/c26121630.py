from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: CableState):
    required = ['IP_Rating', 'Voltage_Rating']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

graph = StateGraph(CableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()