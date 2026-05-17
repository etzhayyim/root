from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    lot_id: str
    temperature_logs: List[float]
    status: str
    compliance_check: bool

def validate_storage(state: ReagentState) -> ReagentState:
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs']) if state['temperature_logs'] else 25.0
    state['compliance_check'] = 2.0 <= avg_temp <= 8.0
    state['status'] = 'COMPLIANT' if state['compliance_check'] else 'NON_COMPLIANT'
    return state

def route_reagent(state: ReagentState) -> str:
    return 'VALIDATED' if state['compliance_check'] else 'FLAGGED'

graph = StateGraph(ReagentState)
graph.add_node('storage_validation', validate_storage)
graph.add_edge('storage_validation', END)
graph.set_entry_point('storage_validation')
compiled_graph = graph.compile()