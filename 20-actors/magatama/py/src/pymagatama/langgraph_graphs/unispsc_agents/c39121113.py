from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MCCState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: MCCState):
    errors = []
    if state['spec_data'].get('busbar_amps', 0) < 600:
        errors.append('Amperage capacity sub-standard for heavy industrial use.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approval_step(state: MCCState):
    print('Proceeding to engineering safety review...')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(MCCState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()