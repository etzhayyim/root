from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class DrillingState(TypedDict):
    requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: DrillingState) -> DrillingState:
    logs = ['Validating torque and diameter constraints.']
    state['is_approved'] = state['requirements'].get('torque_rating_nm', 0) > 500
    return {'validation_logs': logs, 'is_approved': state['is_approved']}

def route_procurement(state: DrillingState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(DrillingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement, {'approved': END, 'rejected': END})

graph = graph.compile()
