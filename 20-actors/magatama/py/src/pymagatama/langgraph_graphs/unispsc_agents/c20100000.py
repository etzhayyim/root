from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class HeavyMachineryState(TypedDict):
    machinery_id: str
    inspection_status: str
    load_profile: float
    safety_logs: Annotated[list, add_messages]

def validate_machinery_spec(state: HeavyMachineryState):
    # Simulate CAD/spec validation logic for heavy machinery
    status = 'VALID' if state['load_profile'] < 10000 else 'MANUAL_REVIEW_REQUIRED'
    return {'inspection_status': status}

def deploy_safety_protocol(state: HeavyMachineryState):
    # Workflow step for safety compliance
    return {'safety_logs': ['Protocol Alpha Initialized for ' + state['machinery_id']]}

graph = StateGraph(HeavyMachineryState)
graph.add_node('validate', validate_machinery_spec)
graph.add_node('safety', deploy_safety_protocol)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)

# Compile the graph
graph = graph.compile()