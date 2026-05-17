from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: BearingState):
    errors = []
    if not state['specifications'].get('load_rating'):
        errors.append('Missing required load rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_compliance(state: BearingState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
app = graph.compile()