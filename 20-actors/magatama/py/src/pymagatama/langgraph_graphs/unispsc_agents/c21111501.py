from typing import TypedDict
from langgraph.graph import StateGraph, END

class SeederState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: SeederState):
    # Business logic for agricultural equipment validation
    is_valid = all(key in state['specs'] for key in ['seeding_rate', 'capacity'])
    print(f'Validation result: {is_valid}')
    return {'approved': is_valid}

def route_by_validation(state: SeederState):
    return 'process' if state['approved'] else END

graph = StateGraph(SeederState)
graph.add_node('process', validate_specs)
graph.set_entry_point('process')
graph.add_edge('process', END)
graph = graph.compile()