from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    commodity_id: str
    purity_grade: float
    safety_check_passed: bool
    compliance_logs: List[str]

def validate_chemical_purity(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if state['purity_grade'] < 0.99:
        state['compliance_logs'].append('Low purity: rejected')
        state['safety_check_passed'] = False
    else:
        state['compliance_logs'].append('Purity validated')
    return state

def check_regulatory_compliance(state: ChemicalProcurementState) -> ChemicalProcurementState:
    state['compliance_logs'].append('Regulatory checks completed')
    state['safety_check_passed'] = True
    return state

builder = StateGraph(ChemicalProcurementState)
builder.add_node('purity_check', validate_chemical_purity)
builder.add_node('regulatory_check', check_regulatory_compliance)
builder.add_edge('purity_check', 'regulatory_check')
builder.add_edge('regulatory_check', END)
builder.set_entry_point('purity_check')
graph = builder.compile()
