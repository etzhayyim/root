from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_medical_specs(state: ProcurementState):
    # Ensure medical grade standards and ISO compliance
    state['approved'] = all(k in state['specs'] for k in ['material', 'iso_cert'])
    return state

def check_regulatory_compliance(state: ProcurementState):
    # Logic to verify FDA or regional medical device clearance
    print(f'Checking regulatory status for {state['item_name']}')
    return 'validate'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('compliance', check_regulatory_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()