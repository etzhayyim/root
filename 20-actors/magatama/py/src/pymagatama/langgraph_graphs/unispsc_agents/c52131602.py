from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShadeState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: ShadeState):
    errors = []
    if not state['specifications'].get('fire_retardant_certification'):
        errors.append('Missing fire safety certification')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def finalize_order(state: ShadeState):
    print('Order processed for windows')
    return {'is_approved': True}

graph = StateGraph(ShadeState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.set_entry_point('validate')
graph.add_edge('finalize', END)
graph = graph.compile()
