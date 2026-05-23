from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WeldingGraphState):
    errors = []
    if state['spec_data'].get('laser_class') != 'Class 4':
        errors.append('Laser safety classification requirement not met.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approval_flow(state: WeldingGraphState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_flow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
