from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SemiconductorChemicalState(TypedDict):
    material_id: str
    purity_level: float
    compliance_tags: List[str]
    validation_status: str

def validate_chemical_purity(state: SemiconductorChemicalState):
    if state['purity_level'] >= 99.999:
        return {'validation_status': 'COMPLIANT'}
    return {'validation_status': 'REJECTED'}

def check_export_controls(state: SemiconductorChemicalState):
    # Simulated compliance logic
    return {'compliance_tags': ['DUAL_USE_REVIEWED']}

builder = StateGraph(SemiconductorChemicalState)
builder.add_node('validate', validate_chemical_purity)
builder.add_node('export', check_export_controls)
builder.add_edge('export', 'validate')
builder.add_edge('validate', END)
builder.set_entry_point('export')
graph = builder.compile()