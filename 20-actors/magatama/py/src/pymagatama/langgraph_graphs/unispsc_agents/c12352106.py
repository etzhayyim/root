from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity_level: float
    processing_steps: Annotated[Sequence[str], operator.add]
    is_validated: bool

def validate_catalyst_purity(state: CatalystState) -> CatalystState:
    # Logic for chemical purity validation
    state['is_validated'] = state['purity_level'] > 0.99
    return state

def run_synthesis_protocol(state: CatalystState) -> CatalystState:
    # Logic for process control setup
    state['processing_steps'].append('reaction_parameters_set')
    return state

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_catalyst_purity)
graph.add_node('protocol', run_synthesis_protocol)
graph.add_edge('validate', 'protocol')
graph.add_edge('protocol', END)
graph.set_entry_point('validate')
graph = graph.compile()
