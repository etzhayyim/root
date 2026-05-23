from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitState(TypedDict):
    kit_id: str
    components: List[str]
    compliance_checked: bool

def validate_components(state: KitState):
    print(f'Validating components for kit: {state["kit_id"]}')
    return {"compliance_checked": len(state["components"]) > 0}

def final_approval(state: KitState):
    print('Proceeding to procurement approval step.')
    return {}

graph = StateGraph(KitState)
graph.add_node("validate", validate_components)
graph.add_node("approve", final_approval)
graph.set_entry_point("validate")
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
app = graph.compile()
