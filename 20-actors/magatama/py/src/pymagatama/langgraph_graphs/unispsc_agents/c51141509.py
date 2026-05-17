from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcureState(TypedDict):
    product_name: str
    regulatory_valid: bool
    batch_records: List[str]

def validate_compliance(state: ProcureState):
    print(f'Validating GMP for {state['product_name']}')
    return {'regulatory_valid': True}

def check_expiry(state: ProcureState):
    print('Checking shelf life for sensitive pharmaceutical')
    return {'batch_records': ['Verified_Expiration_Date']}

graph = StateGraph(ProcureState)
graph.add_node('validate', validate_compliance)
graph.add_node('expiry', check_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph = graph.compile()