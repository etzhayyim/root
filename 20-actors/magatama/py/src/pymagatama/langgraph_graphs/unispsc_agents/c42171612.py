from langgraph.graph import StateGraph, END
from typing import TypedDict
class StretcherState(TypedDict):
    spec_data: dict
    validation_checks: list
    is_compliant: bool
def validate_specs(state: StretcherState):
    check = 'load_capacity' in state['spec_data'] and state['spec_data']['load_capacity'] > 150
    return {'validation_checks': ['load_capacity_check'], 'is_compliant': check}
def check_regulatory(state: StretcherState):
    reg = state['spec_data'].get('certification') in ['FDA', 'CE']
    state['validation_checks'].append('reg_cert_check')
    state['is_compliant'] &= reg
    return state
graph = StateGraph(StretcherState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_regulatory', check_regulatory)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_regulatory')
graph.add_edge('check_regulatory', END)
graph = graph.compile()