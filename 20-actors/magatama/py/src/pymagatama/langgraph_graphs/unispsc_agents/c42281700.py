from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningState(TypedDict):
    product_id: str
    compliance_checked: bool
    safety_validated: bool

def validate_chemistry(state: CleaningState):
    print(f'Validating chemical safety for {state["product_id"]}')
    return {'safety_validated': True}

def check_compliance(state: CleaningState):
    print(f'Verifying ISO 15883 compliance for {state["product_id"]}')
    return {'compliance_checked': True}

graph = StateGraph(CleaningState)
graph.add_node('validate', validate_chemistry)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
