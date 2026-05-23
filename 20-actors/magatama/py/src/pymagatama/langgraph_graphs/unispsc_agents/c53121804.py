from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    case_specs: dict
    validation_logs: List[str]
    is_approved: bool

def validate_durability(state: ProcurementState):
    specs = state.get('case_specs', {})
    if specs.get('durability_rating', 0) > 5:
        state['validation_logs'].append('Durability check passed')
    return {'validation_logs': state['validation_logs']}

def check_compliance(state: ProcurementState):
    state['is_approved'] = True
    return {'is_approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_durability)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
