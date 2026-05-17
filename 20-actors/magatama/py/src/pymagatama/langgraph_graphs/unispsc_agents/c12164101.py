from typing import TypedDict, Annotated, Sequence, List
from langgraph.graph import StateGraph, END
import operator

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: Annotated[List[str], operator.add]
    validation_status: bool

def validate_purity(state: ChemicalIngestState):
    is_pure = state['purity_level'] >= 0.99
    return {'validation_status': is_pure, 'compliance_checks': ['purity_check_passed'] if is_pure else ['purity_check_failed']}

def route_compliance(state: ChemicalIngestState):
    return 'validate' if not state['compliance_checks'] else END

builder = StateGraph(ChemicalIngestState)
builder.add_node('validate', validate_purity)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()