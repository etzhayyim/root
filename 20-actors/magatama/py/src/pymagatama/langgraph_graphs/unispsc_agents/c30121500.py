from typing import TypedDict
from langgraph.graph import StateGraph, END

class BitumenState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliant: bool

def validate_bitumen_specs(state: BitumenState):
    # Business logic for checking technical specs like flash point and penetration
    mandatory_fields = ['flash_point', 'viscosity', 'sds_verified']
    valid = all(key in state['spec_data'] for key in mandatory_fields)
    return {'validation_result': valid, 'compliant': valid}

def check_regulatory_compliance(state: BitumenState):
    # Check hazardous material transport protocols
    is_compliant = state['validation_result'] and state['spec_data'].get('hazmat_approved', False)
    return {'compliant': is_compliant}

graph = StateGraph(BitumenState)
graph.add_node('spec_validation', validate_bitumen_specs)
graph.add_node('regulatory_check', check_regulatory_compliance)
graph.set_entry_point('spec_validation')
graph.add_edge('spec_validation', 'regulatory_check')
graph.add_edge('regulatory_check', END)
graph = graph.compile()