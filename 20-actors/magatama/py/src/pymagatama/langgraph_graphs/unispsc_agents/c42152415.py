from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentalCeramicState(TypedDict):
    material_id: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_certifications(state: DentalCeramicState):
    print(f'Validating ISO compliance for {state["material_id"]}')
    return {'validation_passed': 'ISO 6872' in state['compliance_docs']}

def route_by_validation(state: DentalCeramicState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(DentalCeramicState)
graph.add_node('validate', validate_certifications)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END})
graph.compile()