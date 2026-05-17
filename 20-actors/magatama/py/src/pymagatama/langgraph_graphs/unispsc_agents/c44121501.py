from langgraph.graph import StateGraph, END
from typing import TypedDict
class MailerState(TypedDict):
    diameter: float
    length: float
    material_compliance: bool
    is_approved: bool
def validate_specs(state: MailerState):
    state['is_approved'] = state['diameter'] > 0 and state['length'] > 0 and state['material_compliance']
    return state
graph = StateGraph(MailerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()