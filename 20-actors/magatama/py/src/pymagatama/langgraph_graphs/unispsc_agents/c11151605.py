from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalProcurementState(TypedDict):
    alloy_id: str
    composition_data: dict
    compliance_status: bool
    validation_logs: List[str]

def validate_alloy_specs(state: MetalProcurementState) -> MetalProcurementState:
    # Logic to validate alloy chemical composition against ISO standards
    state['validation_logs'].append('Validating composition...')
    state['compliance_status'] = True
    return state

def check_export_controls(state: MetalProcurementState) -> MetalProcurementState:
    # Logic to check dual-use export control status
    state['validation_logs'].append('Checking export controls...')
    return state

graph = StateGraph(MetalProcurementState)
graph.add_node('validate', validate_alloy_specs)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)

app = graph.compile()
