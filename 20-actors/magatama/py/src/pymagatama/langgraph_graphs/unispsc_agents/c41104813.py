from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RefluxProcessState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: RefluxProcessState):
    errors = []
    if 'material' not in state['part_specs']: errors.append('Missing material info')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def check_compliance(state: RefluxProcessState):
    # Dual-use regulatory check
    return {'is_approved': state['is_approved'] and 'CAGE_code' in state['part_specs']}

graph = StateGraph(RefluxProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
