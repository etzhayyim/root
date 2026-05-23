from typing import TypedDict
from langgraph.graph import StateGraph, END

class SludgeProcessorState(TypedDict):
    capacity: float
    material_type: str
    validation_passed: bool

def validate_specs(state: SludgeProcessorState):
    state['validation_passed'] = state['capacity'] > 0 and state['material_type'] != ''
    return state

def route_processing(state: SludgeProcessorState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(SludgeProcessorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
