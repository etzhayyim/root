from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_code: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_medical_specs(state: ProcurementState):
    required = ['ISO_13485', 'FDA_Clearance']
    passed = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_passed': passed}

def clinical_safety_check(state: ProcurementState):
    print('Performing clinical safety compliance check...')
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('safety', clinical_safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()