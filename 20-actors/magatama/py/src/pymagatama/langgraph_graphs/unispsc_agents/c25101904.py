from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GolfCartState(TypedDict):
    model_id: str
    specs: dict
    validation_errors: List[str]

def validate_specs(state: GolfCartState) -> GolfCartState:
    if state['specs'].get('speed') > 40:
        state['validation_errors'].append('Speed exceeds safety threshold for golf carts.')
    return state

def check_compliance(state: GolfCartState) -> GolfCartState:
    if 'safety_cert' not in state['specs']:
        state['validation_errors'].append('Missing mandatory safety certification.')
    return state

graph = StateGraph(GolfCartState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()