from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectricalState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: ElectricalState):
    specs = state['spec_data']
    required_keys = ['voltage', 'current', 'certification']
    compliance = all(k in specs for k in required_keys)
    return {'is_compliant': compliance}

graph = StateGraph(ElectricalState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()