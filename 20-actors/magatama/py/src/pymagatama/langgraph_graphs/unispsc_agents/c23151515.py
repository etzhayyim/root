from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WeldingGraphState):
    errors = []
    if state['specs'].get('duty_cycle', 0) < 60:
        errors.append('Duty cycle below industrial minimum.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: WeldingGraphState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'is_compliant': True})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
