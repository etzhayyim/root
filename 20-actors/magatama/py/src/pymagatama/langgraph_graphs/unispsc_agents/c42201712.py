from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class UltrasoundState(TypedDict):
    device_id: str
    specs: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: UltrasoundState):
    required = ['DICOMCompatibility', 'ElectricalSafetyStandard']
    missing = [f for f in required if f not in state['specs']]
    return {'validation_results': [f'Missing spec: {m}' for m in missing], 'approved': len(missing) == 0}

def clinical_compliance(state: UltrasoundState):
    return {'validation_results': state['validation_results'] + ['Compliance verified']}

graph = StateGraph(UltrasoundState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', clinical_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()