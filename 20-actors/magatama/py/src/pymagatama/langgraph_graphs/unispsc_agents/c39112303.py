from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterState(TypedDict):
    spec_data: dict
    is_validated: bool

def validate_specs(state: FilterState):
    required = ['material', 'dimension']
    validated = all(k in state['spec_data'] for k in required)
    return {'is_validated': validated}

def approval_node(state: FilterState):
    print('Proceeding with procurement workflow')
    return {'is_validated': True}

graph = StateGraph(FilterState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
