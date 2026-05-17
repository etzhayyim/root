from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    task_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_payload(state: RobotState):
    payload = state['specs'].get('payload_capacity_kg', 0)
    if payload > 50:
        return {'validation_log': ['Payload exceeds standard safety limits - initiate structural integrity audit.']}
    return {'validation_log': ['Payload within safe operational threshold.']}

def check_certification(state: RobotState):
    certs = state['specs'].get('certifications', [])
    if 'ISO10218' not in certs:
        return {'status': 'CERT_REQUIRED', 'validation_log': ['ISO10218 certification missing.']}
    return {'status': 'APPROVED'}

graph = StateGraph(RobotState)
graph.add_node('validate_payload', validate_payload)
graph.add_node('check_certification', check_certification)
graph.set_entry_point('validate_payload')
graph.add_edge('validate_payload', 'check_certification')
graph.add_edge('check_certification', END)
app = graph.compile()