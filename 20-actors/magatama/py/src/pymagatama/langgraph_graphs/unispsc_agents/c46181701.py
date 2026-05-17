from langgraph.graph import StateGraph, END
from typing import TypedDict
class State(TypedDict):
    safety_rating: str
    material: str
    is_compliant: bool
def validate_helmet(state: State):
    if state['safety_rating'] >= 'ANSI-Z89.1':
        return {'is_compliant': True}
    return {'is_compliant': False}
def finalize_procurement(state: State):
    return {'status': 'processed'}
graph = StateGraph(State)
graph.add_node('validate', validate_helmet)
graph.add_node('final', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()