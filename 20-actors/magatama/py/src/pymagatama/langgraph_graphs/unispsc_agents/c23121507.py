from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: WeldingGraphState):
    specs = state.get('spec_data', {})
    errors = []
    if specs.get('duty_cycle') < 0.6: errors.append('Duty cycle below industrial standard')
    res = {'validation_errors': errors}
    return res

def approval_step(state: WeldingGraphState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
