from langgraph.graph import StateGraph, END
from typing import TypedDict
class StrainerState(TypedDict):
    pressure_rating: int
    fluid_type: str
    mesh_size: int
    validation_passed: bool
def validate_specs(state: StrainerState):
    if state['pressure_rating'] > 0 and state['mesh_size'] > 0:
        state['validation_passed'] = True
    else:
        state['validation_passed'] = False
    return 'validate_specs'
def route_result(state: StrainerState):
    return 'end'
graph = StateGraph(StrainerState)
graph.add_node('validate_specs', validate_specs)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', END)
graph = graph.compile()