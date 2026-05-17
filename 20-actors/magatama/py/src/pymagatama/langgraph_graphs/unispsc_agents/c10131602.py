from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class AnimalProcurementState(TypedDict):
    commodity_id: str
    inspection_status: str
    health_certs: Annotated[List[str], operator.add]
    validation_log: Annotated[List[str], operator.add]

def validate_health_docs(state: AnimalProcurementState) -> AnimalProcurementState:
    if not state.get('health_certs'):
        return {**state, 'inspection_status': 'REJECTED', 'validation_log': ['Missing health certification']}
    return {**state, 'inspection_status': 'VALIDATED', 'validation_log': ['Health docs verified']}

def route_to_quarantine(state: AnimalProcurementState) -> str:
    return 'quarantine_check' if state['inspection_status'] == 'VALIDATED' else END

builder = StateGraph(AnimalProcurementState)
builder.add_node('health_check', validate_health_docs)
builder.set_entry_point('health_check')
builder.add_conditional_edges('health_check', route_to_quarantine, {'quarantine_check': END})
builder.add_edge('health_check', END)
graph = builder.compile()