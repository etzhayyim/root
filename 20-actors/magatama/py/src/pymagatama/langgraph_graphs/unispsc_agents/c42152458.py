from langgraph.graph import StateGraph, END
from typing import TypedDict
class State(TypedDict):
    spec_data: dict
    validation_passed: bool
def validate_viscosity(state: State):
    viscosity = state['spec_data'].get('viscosity', 0)
    return {'validation_passed': 50 <= viscosity <= 200}
def check_compliance(state: State):
    return {'validation_passed': state.get('biocompatibility_certificate') is not None}
graph = StateGraph(State)
graph.add_node('validate', validate_viscosity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
