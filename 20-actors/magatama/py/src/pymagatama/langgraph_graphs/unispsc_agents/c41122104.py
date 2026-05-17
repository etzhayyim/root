from langgraph.graph import StateGraph, END
from typing import TypedDict
class FlaskState(TypedDict):
    flask_id: str
    is_sterile: bool
    is_surface_treated: bool
    status: str
def validate_flask(state: FlaskState):
    if state['is_sterile'] and state['is_surface_treated']:
        return {'status': 'Approved'}
    return {'status': 'Rejected'}
graph = StateGraph(FlaskState)
graph.add_node('validate', validate_flask)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()