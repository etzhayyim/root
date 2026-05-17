from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChevronState(TypedDict):
    spec: dict
    approved: bool
    error: str

def validate_chevron_spec(state: ChevronState):
    required = ['material_composition', 'dimensions']
    if all(k in state['spec'] for k in required):
        return {'approved': True}
    return {'approved': False, 'error': 'Missing required fields'}

def finalize_order(state: ChevronState):
    print('Chevron order processed successfully.')
    return {'approved': True}

graph = StateGraph(ChevronState)
graph.add_node('validate', validate_chevron_spec)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.set_entry_point('validate')
graph.add_edge('finalize', END)
graph = graph.compile()