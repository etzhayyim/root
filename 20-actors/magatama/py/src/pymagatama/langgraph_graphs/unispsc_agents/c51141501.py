from typing import TypedDict
from langgraph.graph import StateGraph, END

class AcetazolamideState(TypedDict):
    purity: float
    gmp_certified: bool
    temp_log_valid: bool

def validate_purity(state: AcetazolamideState):
    return {'purity_check': state['purity'] >= 99.0}

def check_compliance(state: AcetazolamideState):
    return {'compliant': state['gmp_certified'] and state['temp_log_valid']}

builder = StateGraph(AcetazolamideState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()