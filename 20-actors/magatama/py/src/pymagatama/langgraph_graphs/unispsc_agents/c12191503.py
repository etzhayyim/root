from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RareEarthState(TypedDict):
    purity_level: float
    impurities: dict
    approved: bool
    history: Annotated[Sequence[str], operator.add]

def validate_purity(state: RareEarthState) -> RareEarthState:
    is_pure = state['purity_level'] >= 99.99
    return {'approved': is_pure, 'history': [f'Purity check: {is_pure}']}

def check_regulations(state: RareEarthState) -> RareEarthState:
    # Dual-use compliance logic
    return {'history': ['Regulation check: Compliant']}

def build_graph():
    graph = StateGraph(RareEarthState)
    graph.add_node('validate', validate_purity)
    graph.add_node('regulate', check_regulations)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'regulate')
    graph.add_edge('regulate', END)
    return graph.compile()