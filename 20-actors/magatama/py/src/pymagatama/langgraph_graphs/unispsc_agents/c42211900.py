from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_ergonomic_safety(state: ProcurementState):
    state['validation_log'].append('Checking ergonomic standards for disabled users')
    state['is_compliant'] = True
    return state

def check_regulatory_approval(state: ProcurementState):
    state['validation_log'].append('Verifying medical grade certification')
    return state

def graph_builder():
    workflow = StateGraph(ProcurementState)
    workflow.add_node('validate', validate_ergonomic_safety)
    workflow.add_node('regulatory', check_regulatory_approval)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', 'regulatory')
    workflow.add_edge('regulatory', END)
    return workflow.compile()

graph = graph_builder()