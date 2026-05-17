from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class ResnatronState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool
def validate_specs(state: ResnatronState):
    errors = []
    if 'frequency' not in state['specs']: errors.append('Frequency missing')
    return {'validation_errors': errors}
def check_export_compliance(state: ResnatronState):
    is_approved = len(state['validation_errors']) == 0
    return {'approved': is_approved}
graph = StateGraph(ResnatronState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()