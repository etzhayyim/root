from langgraph.graph import StateGraph, END
from typing import TypedDict
class ComponentState(TypedDict):
    specs: dict
    validated: bool
graph = StateGraph(ComponentState)
def validate_hydroform_specs(state: ComponentState):
    required = ['Material Grade', 'Dimensional Tolerance']
    state['validated'] = all(k in state['specs'] for k in required)
    return state
graph.add_node('validate', validate_hydroform_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()