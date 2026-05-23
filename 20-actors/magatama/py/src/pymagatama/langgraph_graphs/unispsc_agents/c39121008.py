from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SignalConverterState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: SignalConverterState):
    errors = []
    if not state['specs'].get('input_signal_range'):
        errors.append('Missing input signal range')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: SignalConverterState):
    return 'process_order' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(SignalConverterState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', lambda s: {'is_compliant': True})
graph.add_node('flag_for_review', lambda s: {'is_compliant': False})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process_order', END)
graph.add_edge('flag_for_review', END)
graph = graph.compile()
