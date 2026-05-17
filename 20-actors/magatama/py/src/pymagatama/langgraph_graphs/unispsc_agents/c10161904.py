from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FeedProcurementState(TypedDict):
    commodity_code: str
    batch_id: str
    moisture: float
    status: str
    audit_logs: List[str]

def validate_moisture(state: FeedProcurementState) -> FeedProcurementState:
    if state['moisture'] > 14.0:
        state['status'] = 'REJECTED: High Moisture'
    else:
        state['status'] = 'PASSED: Moisture Check'
    return state

def check_certification(state: FeedProcurementState) -> FeedProcurementState:
    if 'PASSED' in state['status']:
        state['audit_logs'].append('Non-GMO certificate verified.')
    return state

graph = StateGraph(FeedProcurementState)
graph.add_node('validate_moisture', validate_moisture)
graph.add_node('check_cert', check_certification)
graph.add_edge('validate_moisture', 'check_cert')
graph.add_edge('check_cert', END)
graph.set_entry_point('validate_moisture')
compiled_graph = graph.compile()