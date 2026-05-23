from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RepairKitState(TypedDict):
    kit_id: str
    model_compatibility: List[str]
    spec_check_passed: bool

def validate_compatibility(state: RepairKitState):
    state['spec_check_passed'] = len(state['model_compatibility']) > 0
    return state

def route_verification(state: RepairKitState):
    return 'process' if state['spec_check_passed'] else END

graph = StateGraph(RepairKitState)
graph.add_node('validate', validate_compatibility)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_verification, {'process': 'process'})
graph.add_edge('process', END)
graph = graph.compile()
