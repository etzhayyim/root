from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SealKitState(TypedDict):
    kit_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_materials(state: SealKitState):
    material = state.get('specs', {}).get('material')
    state['validation_passed'] = material is not None
    state['log'].append(f"Material check: {state['validation_passed']}")
    return state

def check_compatibility(state: SealKitState):
    state['log'].append("Running chemical compatibility simulation...")
    return state

graph = StateGraph(SealKitState)
graph.add_node("validate", validate_materials)
graph.add_node("compatibility", check_compatibility)
graph.set_entry_point("validate")
graph.add_edge("validate", "compatibility")
graph.add_edge("compatibility", END)
graph = graph.compile()
