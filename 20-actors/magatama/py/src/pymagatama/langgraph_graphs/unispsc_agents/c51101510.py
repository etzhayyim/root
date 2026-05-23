from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalIngestState(TypedDict):
    cas_number: str
    purity_level: float
    compliance_checks: List[str]
    approved: bool

def validate_purity(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['purity_level'] >= 99.9:
        state['compliance_checks'].append('PurityValidated')
        state['approved'] = True
    else:
        state['approved'] = False
    return state

def security_audit(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['approved']:
        state['compliance_checks'].append('SecurityCleared')
    return state

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('audit', security_audit)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
