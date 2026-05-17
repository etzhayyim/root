from langgraph.graph import StateGraph, END
from typing import TypedDict
class TubingState(TypedDict):
    spec_data: dict
    validated: bool
    error: str
def validate_specs(state: TubingState):
    required = ['material', 'pressure_rating']
    if all(k in state['spec_data'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required fields'}
def finalize_order(state: TubingState):
    print('Order processing complete')
    return state
graph = StateGraph(TubingState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()