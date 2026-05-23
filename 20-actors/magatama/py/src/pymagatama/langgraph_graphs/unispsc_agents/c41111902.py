from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CounterState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_counter_specs(state: CounterState):
    errors = []
    if 'frequency' not in state['specs']:
        errors.append('Missing frequency specification')
    if 'voltage' not in state['specs']:
        errors.append('Missing input voltage rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_export_control(state: CounterState):
    # Business logic for high-frequency dual-use checks
    if state.get('specs', {}).get('frequency', 0) > 1000000:
         return {'is_compliant': False}
    return {}

graph = StateGraph(CounterState)
graph.add_node('validate', validate_counter_specs)
graph.add_node('export_check', check_export_control)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
