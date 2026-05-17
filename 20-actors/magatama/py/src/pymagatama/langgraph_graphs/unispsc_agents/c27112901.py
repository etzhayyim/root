from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolProcessState(TypedDict):
    tool_id: str
    pressure_rating: int
    is_verified: bool
    validation_errors: List[str]

def validate_specs(state: ToolProcessState):
    errors = []
    if state['pressure_rating'] < 1000:
        errors.append('Insufficient pressure rating for industrial use')
    return {'is_verified': len(errors) == 0, 'validation_errors': errors}

def route_verification(state: ToolProcessState):
    return 'verified' if state['is_verified'] else END

graph = StateGraph(ToolProcessState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()