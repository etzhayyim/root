from typing import TypedDict
from langgraph.graph import StateGraph, END

class LampState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: LampState) -> LampState:
    required = ['wattage_rating', 'mercury_content_compliance']
    state['validation_passed'] = all(k in state['spec_data'] for k in required)
    return state

def check_hazard(state: LampState) -> str:
    return 'pass' if state['validation_passed'] else 'fail'

graph = StateGraph(LampState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
