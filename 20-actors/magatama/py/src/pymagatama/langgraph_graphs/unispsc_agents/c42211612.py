from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    spec_id: str
    compliance_docs: List[str]
    approved: bool

def validate_specs(state: ProcurementState):
    # Simulate CAD/Spec validation for medical equipment
    is_compliant = all(d in ['ISO_7176', 'JIS_T_0925'] for d in state['compliance_docs'])
    print(f'Validating spec {state['spec_id']} for medical safety...')
    return {'approved': is_compliant}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
