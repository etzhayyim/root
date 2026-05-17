from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClassroomSupplyState(TypedDict):
    item_name: str
    safety_check_passed: bool
    compliance_docs: List[str]

def validate_safety(state: ClassroomSupplyState):
    # Simulate material safety compliance check for classroom items
    state['safety_check_passed'] = 'Non-toxic certification' in state.get('compliance_docs', [])
    return state

def finalize_procurement(state: ClassroomSupplyState):
    print(f"Processing procurement for {state['item_name']}")
    return state

graph = StateGraph(ClassroomSupplyState)
graph.add_node("safety_check", validate_safety)
graph.add_node("finalize", finalize_procurement)
graph.set_entry_point("safety_check")
graph.add_edge("safety_check", "finalize")
graph.add_edge("finalize", END)
compiled_graph = graph.compile()