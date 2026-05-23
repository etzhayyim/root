from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class EndEffectorState(TypedDict):
    spec_id: str
    payload_requirement: float
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_payload(state: EndEffectorState):
    limit = 50.0
    if state['payload_requirement'] > limit:
        return {'validation_logs': ['Payload exceeds standard industrial limit.'], 'is_compliant': False}
    return {'validation_logs': ['Payload verified.'], 'is_compliant': True}

def check_compatibility(state: EndEffectorState):
    if state['is_compliant']:
        return {'validation_logs': ['Compatibility check passed.'], 'is_compliant': True}
    return {'validation_logs': ['Compatibility check skipped.'], 'is_compliant': False}

graph = StateGraph(EndEffectorState)
graph.add_node('validate', validate_payload)
graph.add_node('compatibility', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()
