from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FreezerProcurementState(TypedDict):
    model_number: str
    temp_range: tuple
    compliance_docs: List[str]
    is_approved: bool

def validate_specs(state: FreezerProcurementState):
    # Business logic for freezer procurement compliance
    if state['temp_range'][0] < -80:
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

def check_compliance(state: FreezerProcurementState):
    state['is_approved'] = 'ISO_CERT' in state['compliance_docs']
    return state

graph = StateGraph(FreezerProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()