from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrassProcurementState(TypedDict):
    material_spec: str
    compliance_docs: List[str]
    validation_status: bool

def validate_material(state: BrassProcurementState):
    # Business logic for brass specification compliance
    is_valid = 'JIS_H3100' in state['material_spec']
    return {'validation_status': is_valid}

def process_certifications(state: BrassProcurementState):
    # Verify mill certs presence
    return {'compliance_docs': state.get('compliance_docs', []) + ['MILL_CERT_VERIFIED']}

graph = StateGraph(BrassProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('certify', process_certifications)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
app = graph.compile()
