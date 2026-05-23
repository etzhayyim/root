from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EMSState(TypedDict):
    product_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: EMSState):
    errors = []
    if 'ISO_13485_certification' not in state['product_specs']:
        errors.append('Missing ISO 13485 certification.')
    if state['product_specs'].get('load_capacity', 0) < 150:
        errors.append('Load capacity below mandatory safety threshold.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(EMSState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
