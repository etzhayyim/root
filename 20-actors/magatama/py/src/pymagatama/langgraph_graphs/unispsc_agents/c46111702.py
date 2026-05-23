from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class IRDetectorState(TypedDict):
    specs: dict
    compliance_checks: Annotated[List[str], operator.add]
    is_approved: bool

def validate_tech_specs(state: IRDetectorState):
    checks = []
    if 'ECCN' in state['specs']:
        checks.append('ECCN_VALIDATED')
    return {'compliance_checks': checks}

def export_control_review(state: IRDetectorState):
    is_approved = state['specs'].get('ECCN') != 'EAR99_EXPORT_RESTRICTED'
    return {'is_approved': is_approved}

graph = StateGraph(IRDetectorState)
graph.add_node('validate_specs', validate_tech_specs)
graph.add_node('export_review', export_control_review)
graph.add_edge('validate_specs', 'export_review')
graph.add_edge('export_review', END)
graph.set_entry_point('validate_specs')
graph = graph.compile()
