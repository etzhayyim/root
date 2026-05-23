from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MicroState(TypedDict):
    media_type: str
    compliance_docs: List[str]
    verification_status: bool

def validate_culture_safety(state: MicroState):
    state['verification_status'] = 'biosafety_check' in state['compliance_docs']
    return {'verification_status': state['verification_status']}

def process_transformation_kit(state: MicroState):
    return {'media_type': 'validated_' + state['media_type']}

graph = StateGraph(MicroState)
graph.add_node('safety_check', validate_culture_safety)
graph.add_node('kit_process', process_transformation_kit)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'kit_process')
graph.add_edge('kit_process', END)
graph = graph.compile()
