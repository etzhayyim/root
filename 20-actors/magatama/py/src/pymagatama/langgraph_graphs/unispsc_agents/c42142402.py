from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SuctionSupplyState(TypedDict):
    item_id: str
    specifications: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_medical_standards(state: SuctionSupplyState):
    errors = []
    if not state['specifications'].get('sterility_cert'):
        errors.append('Missing Sterility Certification')
    if not state['specifications'].get('biocompatibility'):
        errors.append('Biocompatibility test required')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

graph = StateGraph(SuctionSupplyState)
graph.add_node('validate', validate_medical_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()