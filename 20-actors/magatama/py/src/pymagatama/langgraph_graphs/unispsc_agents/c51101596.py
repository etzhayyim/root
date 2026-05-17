from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class BioReagentState(TypedDict):
    lot_id: str
    purity: float
    temp_log: Annotated[list[float], operator.add]
    is_validated: bool

def validate_purity(state: BioReagentState):
    # Perform specialized purity validation logic
    state['is_validated'] = state['purity'] >= 99.0
    return state

def check_temp_stability(state: BioReagentState):
    # Check cold chain integrity
    valid = all(t >= 2.0 and t <= 8.0 for t in state['temp_log'])
    state['is_validated'] = state['is_validated'] and valid
    return state

graph = StateGraph(BioReagentState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_temp_stability', check_temp_stability)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_temp_stability')
graph.add_edge('check_temp_stability', END)
compiled_graph = graph.compile()