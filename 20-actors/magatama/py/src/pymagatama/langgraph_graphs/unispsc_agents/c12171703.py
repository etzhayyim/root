from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SilaneProcurementState(TypedDict):
    purity_check: bool
    trace_metal_level: float
    inspection_status: str
    logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: SilaneProcurementState):
    is_pure = state['purity_check'] and state['trace_metal_level'] < 0.01
    return {'inspection_status': 'PASSED' if is_pure else 'REJECTED'}

def update_records(state: SilaneProcurementState):
    return {'logs': [f'Status recorded as {state["inspection_status"]}']}

graph = StateGraph(SilaneProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('record', update_records)
graph.set_entry_point('validate')
graph.add_edge('validate', 'record')
graph.add_edge('record', END)
graph = graph.compile()