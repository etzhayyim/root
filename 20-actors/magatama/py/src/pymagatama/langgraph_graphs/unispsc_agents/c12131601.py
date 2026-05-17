from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity_level: float
    safety_clearance: bool
    messages: Annotated[Sequence[str], operator.add]

def validate_catalyst_purity(state: CatalystState):
    is_pure = state['purity_level'] >= 99.5
    return {'safety_clearance': is_pure, 'messages': [f'Purity check: {is_pure}']}

def process_catalyst_logistics(state: CatalystState):
    status = 'APPROVED' if state['safety_clearance'] else 'FLAGGED_FOR_INSPECTION'
    return {'messages': [f'Logistics Status: {status}']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_catalyst_purity)
graph.add_node('logistics', process_catalyst_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()