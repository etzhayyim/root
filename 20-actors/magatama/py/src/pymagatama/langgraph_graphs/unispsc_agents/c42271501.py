from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ApneaMonitorState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    validation_status: bool

def validate_compliance(state: ApneaMonitorState):
    state['validation_status'] = len(state['compliance_docs']) >= 2
    return 'validate_compliance'

def process_monitor_data(state: ApneaMonitorState):
    print(f'Processing monitor: {state[\"device_id\"]}')
    return 'process_data'

graph = StateGraph(ApneaMonitorState)
graph.add_node('validate_compliance', validate_compliance)
graph.add_node('process_data', process_monitor_data)
graph.set_entry_point('validate_compliance')
graph.add_edge('validate_compliance', 'process_data')
graph.add_edge('process_data', END)
graph = graph.compile()