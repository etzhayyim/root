from typing import TypedDict
from langgraph.graph import StateGraph, END
class PatchCordState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list
def validate_specs(state: PatchCordState):
    required = ['Category', 'Connector Type']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_result': valid, 'error_log': [] if valid else ['Missing specs']}
def route_step(state: PatchCordState):
    return 'validate' if state['validation_result'] else END
graph = StateGraph(PatchCordState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
