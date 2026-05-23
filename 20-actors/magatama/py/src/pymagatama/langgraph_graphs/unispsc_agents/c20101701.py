from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class DrillProcurementState(TypedDict):
    material_specs: dict
    validation_logs: List[str]
    approved: bool

def validate_material(state: DrillProcurementState) -> DrillProcurementState:
    hardness = state['material_specs'].get('hardness_hrc', 0)
    if hardness >= 55:
        state['validation_logs'].append('Material hardness within spec')
        state['approved'] = True
    else:
        state['validation_logs'].append('Material hardness insufficient')
        state['approved'] = False
    return state

def check_certification(state: DrillProcurementState) -> DrillProcurementState:
    if state.get('approved', False):
        state['validation_logs'].append('Certification verified')
    return state

graph = StateGraph(DrillProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
