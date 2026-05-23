from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    cas_number: str
    purity: float
    compliance_cleared: bool

def validate_chemical_specs(state: ChemicalProcurementState):
    state['compliance_cleared'] = (state['purity'] >= 99.0 and state['cas_number'] == '6381-59-5')
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_chemical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
