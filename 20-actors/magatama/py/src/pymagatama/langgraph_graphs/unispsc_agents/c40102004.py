from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoilerState(TypedDict):
    spec_data: dict
    is_compliant: bool
    safety_check: bool

def validate_emissions(state: BoilerState):
    nox_level = state['spec_data'].get('nox_level', 100)
    state['is_compliant'] = nox_level < 50
    return state

def safety_audit(state: BoilerState):
    state['safety_check'] = state['spec_data'].get('has_emergency_shutoff', False)
    return state

graph = StateGraph(BoilerState)
graph.add_node('validate', validate_emissions)
graph.add_node('audit', safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
app = graph.compile()