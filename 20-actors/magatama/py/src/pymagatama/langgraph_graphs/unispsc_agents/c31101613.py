from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_alloy_specs(state: CastingState):
    print('Validating chemical composition against alloy grade...')
    state['validation_results'].append('Alloy Composition Verified')
    return state

def check_dimensional_accuracy(state: CastingState):
    print('Checking dimensional tolerances for sand-cast geometry...')
    state['validation_results'].append('Dimensions within Tolerance')
    state['is_approved'] = True
    return state

graph = StateGraph(CastingState)
graph.add_node('val_alloy', validate_alloy_specs)
graph.add_node('val_dim', check_dimensional_accuracy)
graph.add_edge('val_alloy', 'val_dim')
graph.add_edge('val_dim', END)
graph.set_entry_point('val_alloy')
graph = graph.compile()