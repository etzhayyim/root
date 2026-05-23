from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ProcurementState(TypedDict):
    commodity_code: str
    batch_id: str
    compliance_passed: bool
    validation_log: Annotated[List[str], operator.add]

def validate_chemical_compliance(state: ProcurementState) -> ProcurementState:
    # Logic for chemical purity check and hazard validation
    state['validation_log'] = [f'Validating chemical batch {state["batch_id"]} for code {state["commodity_code"]}']
    state['compliance_passed'] = True
    return state

def run_safety_protocol(state: ProcurementState) -> ProcurementState:
    state['validation_log'] = ['Running safety, hazard, and dual-use checks.']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemical_compliance)
graph.add_node('safety', run_safety_protocol)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
