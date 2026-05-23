from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class State(TypedDict):
    material_id: str
    purity_level: float
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: State) -> State:
    if state['purity_level'] >= 99.9:
        return {'validation_logs': ['Purity check passed'], 'is_approved': True}
    return {'validation_logs': ['Purity check failed'], 'is_approved': False}

def route_by_approval(state: State) -> str:
    return 'end' if state['is_approved'] else 'end'

graph = StateGraph(State)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
