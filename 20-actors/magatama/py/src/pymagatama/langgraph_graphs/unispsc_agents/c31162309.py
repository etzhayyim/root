from typing import TypedDict
from langgraph.graph import StateGraph, END

class RackState(TypedDict):
    dimensions: dict
    load_capacity: float
    status: str

def validate_specs(state: RackState):
    print('Validating load capacity and dimensions...')
    valid = state['load_capacity'] > 0 and 'depth' in state['dimensions']
    return {'status': 'validated' if valid else 'rejected'}

def finalize_order(state: RackState):
    print('Finalizing order specifications.')
    return {'status': 'ordered'}

graph = StateGraph(RackState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
