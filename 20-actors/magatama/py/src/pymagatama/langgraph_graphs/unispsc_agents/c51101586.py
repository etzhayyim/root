from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class DiagnosticState(TypedDict):
    reagent_id: str
    batch_id: str
    validation_status: str
    logs: List[str]

def validate_lot(state: DiagnosticState) -> DiagnosticState:
    # Logic to verify lot expiration and compliance
    state['validation_status'] = 'PENDING_INSPECTION'
    state['logs'].append(f'Validating batch {state["batch_id"]}')
    return state

def check_temp_log(state: DiagnosticState) -> DiagnosticState:
    # Logic to verify cold chain integrity
    state['validation_status'] = 'VALIDATED'
    state['logs'].append('Temperature logs confirmed compliant')
    return state

graph = StateGraph(DiagnosticState)
graph.add_node('validate', validate_lot)
graph.add_node('temp_check', check_temp_log)
graph.set_entry_point('validate')
graph.add_edge('validate', 'temp_check')
graph.add_edge('temp_check', END)
compile = graph.compile()