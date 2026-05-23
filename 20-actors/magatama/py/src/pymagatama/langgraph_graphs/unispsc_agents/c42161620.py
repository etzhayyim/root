from typing import TypedDict
from langgraph.graph import StateGraph, END

class DialysisPumpState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: DialysisPumpState):
    required = ['flow_rate_accuracy', 'iso_cert']
    missing = [f for f in required if f not in state['spec_data']]
    state['is_compliant'] = len(missing) == 0
    state['validation_log'] = [f'Missing: {f}' for f in missing]
    return state

def check_regulatory(state: DialysisPumpState):
    if state.get('is_compliant'):
        state['validation_log'].append('Regulatory audit passed')
    return state

graph = StateGraph(DialysisPumpState)
graph.add_node('validate', validate_specs)
graph.add_node('regulatory', check_regulatory)
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph.set_entry_point('validate')
graph = graph.compile()
