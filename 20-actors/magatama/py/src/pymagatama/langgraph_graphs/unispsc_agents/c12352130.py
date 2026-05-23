from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CeramicState(TypedDict):
    purity: float
    particle_size: float
    impurity_data: dict
    approved: bool

def validate_purity(state: CeramicState):
    is_pure = state['purity'] >= 99.9
    return {'approved': is_pure}

def check_size(state: CeramicState):
    is_size_ok = 0.5 <= state['particle_size'] <= 5.0
    return {'approved': state['approved'] and is_size_ok}

graph = StateGraph(CeramicState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_size', check_size)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_size')
graph.add_edge('check_size', END)
compile_graph = graph.compile()
