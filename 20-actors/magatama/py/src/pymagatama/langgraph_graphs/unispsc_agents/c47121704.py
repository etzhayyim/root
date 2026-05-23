from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    lid_specs: dict
    is_compliant: bool

def validate_lid_specs(state: ContainerState):
    specs = state['lid_specs']
    valid = all(k in specs for k in ['material', 'dimensions', 'impact_resistance'])
    print(f'Validating lid specs: {valid}')
    return {'is_compliant': valid}

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_lid_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
