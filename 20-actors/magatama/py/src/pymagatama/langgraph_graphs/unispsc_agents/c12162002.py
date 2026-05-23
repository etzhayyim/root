from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_code: str
    purity_level: float
    compliance_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalState) -> ChemicalState:
    state['is_approved'] = state['purity_level'] >= 0.99
    return state

def check_compliance(state: ChemicalState) -> ChemicalState:
    state['compliance_checks'].append('SafetyDataSheetVerified')
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
