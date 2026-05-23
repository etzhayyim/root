from typing import TypedDict
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    product_id: str
    sterile_check: bool
    compliance_validated: bool

def validate_sterilization(state: CatheterState):
    state['sterile_check'] = True
    return 'sterile_check'

def check_compliance(state: CatheterState):
    state['compliance_validated'] = True
    return 'compliance_validated'

graph = StateGraph(CatheterState)
graph.add_node('sterilization', validate_sterilization)
graph.add_node('compliance', check_compliance)
graph.add_edge('sterilization', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('sterilization')
graph = graph.compile()
