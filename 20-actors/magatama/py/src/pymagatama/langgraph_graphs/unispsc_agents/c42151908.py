from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlaskProcessState(TypedDict):
    flask_id: str
    material_spec: str
    is_validated: bool
    error_logs: List[str]

def validate_flask_specs(state: FlaskProcessState):
    # Simulate validation logic for dental flasks
    is_valid = 'ISO' in state['material_spec']
    return {'is_validated': is_valid}

def route_process(state: FlaskProcessState):
    return 'validate' if not state.get('is_validated') else END

graph = StateGraph(FlaskProcessState)
graph.add_node('validate', validate_flask_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()