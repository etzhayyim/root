from typing import TypedDict
from langgraph.graph import StateGraph, END

class EvidenceKitState(TypedDict):
    kit_id: str
    is_sterile: bool
    tamper_evident: bool
    validation_status: str

def validate_integrity(state: EvidenceKitState):
    if state['is_sterile'] and state['tamper_evident']:
        return {'validation_status': 'COMPLIANT'}
    return {'validation_status': 'REJECTED'}

def process_kit(state: EvidenceKitState):
    print(f'Processing kit: {state[\'kit_id\']}')
    return {'validation_status': 'PROCESSED'}

graph = StateGraph(EvidenceKitState)
graph.add_node('validate', validate_integrity)
graph.add_node('process', process_kit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()