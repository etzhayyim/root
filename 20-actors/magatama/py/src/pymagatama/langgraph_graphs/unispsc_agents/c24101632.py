from typing import TypedDict
from langgraph.graph import StateGraph, END

class SideShiftState(TypedDict):
    capacity: int
    compatibility: str
    validation_passed: bool

def validate_specs(state: SideShiftState):
    state['validation_passed'] = state['capacity'] > 0 and state['compatibility'] is not None
    return {'validation_passed': state['validation_passed']}

def deploy_procurement(state: SideShiftState):
    print(f'Procuring side shift with capacity: {state['capacity']}')
    return {'validation_passed': True}

graph = StateGraph(SideShiftState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
