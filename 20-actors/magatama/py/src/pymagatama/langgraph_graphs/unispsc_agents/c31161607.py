from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExpansionBoltState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_load_capacity(state: ExpansionBoltState):
    capacity = state['spec_data'].get('load_capacity', 0)
    return {'is_compliant': capacity > 0}

graph = StateGraph(ExpansionBoltState)
graph.add_node('validate', validate_load_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
