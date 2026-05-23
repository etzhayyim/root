from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class OpSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool
def validate_medical_compliance(state: OpSpecState):
    errors = []
    if 'iso_13485' not in state['spec_data']: errors.append('Missing certification')
    return {'validation_errors': errors}
def finalize_procurement(state: OpSpecState):
    return {'approved': len(state['validation_errors']) == 0}
graph = StateGraph(OpSpecState)
graph.add_node('validate', validate_medical_compliance)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
