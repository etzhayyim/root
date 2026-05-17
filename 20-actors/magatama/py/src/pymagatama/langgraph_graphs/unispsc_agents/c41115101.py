from langgraph.graph import StateGraph, END
from typing import TypedDict

class CoalTestState(TypedDict):
    instrument_type: str
    validation_passed: bool
    safety_check: bool

def validate_specs(state: CoalTestState):
    state['validation_passed'] = bool(state['instrument_type'])
    return state

def safety_protocol(state: CoalTestState):
    state['safety_check'] = True
    return state

graph = StateGraph(CoalTestState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_protocol)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()