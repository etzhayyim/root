from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    cas_number: str
    validation_logs: List[str]
    approved: bool

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity'] >= 0.99:
        state['validation_logs'].append('Purity check passed')
        state['approved'] = True
    else:
        state['validation_logs'].append('Purity insufficient for high-grade spec')
        state['approved'] = False
    return state

def safety_audit(state: ChemicalState) -> ChemicalState:
    if state['cas_number']:
        state['validation_logs'].append('CAS Registry check successful')
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('audit', safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph = graph.compile()