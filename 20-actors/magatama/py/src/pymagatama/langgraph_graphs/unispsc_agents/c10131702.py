from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_code: str
    batch_number: str
    inspection_status: bool
    compliance_report: List[str]

def validate_batch(state: ProcurementState) -> ProcurementState:
    print(f'Validating batch {state[batch_number]} for commodity {state[commodity_code]}')
    return {**state, inspection_status: True}

def generate_compliance(state: ProcurementState) -> ProcurementState:
    return {**state, compliance_report: [PASSED_ORIGIN_CHECK, PASSED_TEMP_LOG_CHECK]}

graph = StateGraph(ProcurementState)
graph.add_node(validate, validate_batch)
graph.add_node(compliance, generate_compliance)
graph.set_entry_point(validate)
graph.add_edge(validate, compliance)
graph.add_edge(compliance, END)
graph = graph.compile()