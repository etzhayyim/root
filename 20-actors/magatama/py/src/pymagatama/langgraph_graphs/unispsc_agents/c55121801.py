from typing import TypedDict
from langgraph.graph import StateGraph, END

class TaxDiscState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_materials(state: TaxDiscState):
    # Business logic for verifying tamper-evident material compliance
    state['validation_passed'] = 'anti_counterfeit' in state['spec_data']
    return state

def check_compliance(state: TaxDiscState):
    # Business logic for issuing authority regulation check
    return 'compliant' if state['validation_passed'] else 'non-compliant'

graph = StateGraph(TaxDiscState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
