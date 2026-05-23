from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PhosphateProcurementState(TypedDict):
    commodity_code: str
    purity_level: float
    inspection_status: str
    logs: List[str]

def validate_purity(state: PhosphateProcurementState) -> PhosphateProcurementState:
    if state['purity_level'] < 99.9:
        state['logs'].append('Low purity: FAILED')
        state['inspection_status'] = 'REJECTED'
    else:
        state['logs'].append('Purity check: PASSED')
        state['inspection_status'] = 'CERTIFIED'
    return state

def route_by_status(state: PhosphateProcurementState) -> str:
    return 'process_order' if state['inspection_status'] == 'CERTIFIED' else 'end'

graph = StateGraph(PhosphateProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_status, {'process_order': END, 'end': END})
graph.add_edge('validate', END)
graph = graph.compile()
