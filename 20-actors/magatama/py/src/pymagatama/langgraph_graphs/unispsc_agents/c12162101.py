from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ChemicalState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalState) -> ChemicalState:
    state['is_approved'] = state['purity_level'] >= 99.9
    return state

def check_compliance(state: ChemicalState) -> ChemicalState:
    checks = ['MSDS_VERIFIED', 'EXPORT_CONTROL_CLEARED']
    state['compliance_checks'] = checks
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
compile = graph.compile()