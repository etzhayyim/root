from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    spec_data: dict
    validation_passed: bool
    sds_verified: bool

def validate_purity(state: ChemicalState):
    purity = state['spec_data'].get('purity', 0)
    return {'validation_passed': purity >= 99.0}

def check_sds(state: ChemicalState):
    sds_present = state['spec_data'].get('sds_attached', False)
    return {'sds_verified': sds_present}

workflow = StateGraph(ChemicalState)
workflow.add_node('validate_purity', validate_purity)
workflow.add_node('check_sds', check_sds)

workflow.set_entry_point('validate_purity')
workflow.add_edge('validate_purity', 'check_sds')
workflow.add_edge('check_sds', END)

graph = workflow.compile()
