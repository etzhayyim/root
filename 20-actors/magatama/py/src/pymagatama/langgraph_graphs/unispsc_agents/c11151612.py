from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class NickelProcurementState(TypedDict):
    material_id: str
    purity_level: float
    certification_verified: bool
    inspection_result: str
    workflow_log: Annotated[Sequence[str], operator.add]

def validate_material_specs(state: NickelProcurementState) -> NickelProcurementState:
    if state['purity_level'] >= 99.9:
        return {'certification_verified': True, 'workflow_log': ['Specs validated: High Purity']}
    return {'certification_verified': False, 'workflow_log': ['Specs failed: Purity below 99.9%']}

def perform_inspection(state: NickelProcurementState) -> NickelProcurementState:
    if state['certification_verified']:
        return {'inspection_result': 'PASS', 'workflow_log': ['Inspection passed']}
    return {'inspection_result': 'FAIL', 'workflow_log': ['Inspection flagged']}

graph = StateGraph(NickelProcurementState)
graph.add_node('validate', validate_material_specs)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)

app = graph.compile()