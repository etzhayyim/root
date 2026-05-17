from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReceptacleState(TypedDict):
    voltage: int
    amperage: int
    standards: list[str]
    approved: bool

def validate_specs(state: ReceptacleState):
    is_safe = state['voltage'] >= 100 and any(s in ('UL', 'PSE', 'CE') for s in state['standards'])
    print(f'Validating: {state}')
    return {'approved': is_safe}

def route_by_validation(state: ReceptacleState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ReceptacleState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()