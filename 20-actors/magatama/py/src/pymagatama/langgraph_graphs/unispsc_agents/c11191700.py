from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    batch_id: str
    purity_level: float
    hazard_check_passed: bool
    process_logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState):
    is_pure = state['purity_level'] >= 0.99
    return {'hazard_check_passed': is_pure, 'process_logs': [f'Purity check: {is_pure}']}

def safety_protocol(state: CatalystState):
    if state['hazard_check_passed']:
        return {'process_logs': ['Safety protocol cleared for transport']}
    return {'process_logs': ['CRITICAL: Safety violation detected']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_protocol)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()