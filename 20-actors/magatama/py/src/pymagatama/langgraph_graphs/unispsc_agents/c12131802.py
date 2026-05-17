from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AluminumTargetState(TypedDict):
    purity: float
    impurities_ppm: dict
    physical_specs: dict
    approved: bool

def validate_purity(state: AluminumTargetState):
    state['approved'] = state['purity'] >= 99.999
    return state

def check_impurities(state: AluminumTargetState):
    # Simulate impurity threshold check
    if any(val > 1.0 for val in state['impurities_ppm'].values()):
        state['approved'] = False
    return state

graph = StateGraph(AluminumTargetState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_impurities', check_impurities)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_impurities')
graph.add_edge('check_impurities', END)
app = graph.compile()