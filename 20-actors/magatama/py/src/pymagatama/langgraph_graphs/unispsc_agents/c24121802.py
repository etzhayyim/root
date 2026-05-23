from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_container_specs(state: ContainerState):
    required = ['capacity', 'material', 'un_code']
    compliance = all(k in state['spec_data'] for k in required)
    return {'is_compliant': compliance}

graph = StateGraph(ContainerState)
graph.add_node('validation', validate_container_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
