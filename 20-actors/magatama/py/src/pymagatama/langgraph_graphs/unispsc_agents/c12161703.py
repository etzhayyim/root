from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class State(TypedDict):
    batch_id: str
    purity_level: float
    verified: bool
    logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: State):
    is_pure = state['purity_level'] >= 99.9
    return {'verified': is_pure, 'logs': [f'Purity check: {is_pure} (Level: {state['purity_level']})']}

def route_verification(state: State):
    return 'process' if state['verified'] else END

def process_batch(state: State):
    return {'logs': ['Processing high-purity ceramic batch for industrial supply chain.']}

graph = StateGraph(State)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_verification)
graph.add_edge('process', END)
graph = graph.compile()
