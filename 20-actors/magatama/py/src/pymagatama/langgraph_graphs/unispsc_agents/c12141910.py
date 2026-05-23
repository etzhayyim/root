from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    material_id: str
    purity: float
    process_specs: dict
    is_validated: bool
    error_logs: List[str]

def validate_catalyst_specs(state: CatalystState):
    is_valid = state['purity'] >= 99.5
    return {'is_validated': is_valid, 'error_logs': [] if is_valid else ['Purity below threshold']}

def route_by_validation(state: CatalystState):
    return 'VALID' if state['is_validated'] else 'REJECT'

def finalize_order(state: CatalystState):
    return {'material_id': state['material_id'] + '_APPROVED'}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_catalyst_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
