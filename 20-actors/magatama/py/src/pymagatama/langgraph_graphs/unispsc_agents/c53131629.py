from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MakeupKitState(TypedDict):
    kit_id: str
    compliance_docs: List[str]
    status: str

def validate_ingredients(state: MakeupKitState):
    print(f'Validating ingredients for kit: {state["kit_id"]}')
    return {"status": "ingredient_verified"}

def check_certifications(state: MakeupKitState):
    print('Checking dermatological certifications...')
    return {"status": "cert_passed"}

graph = StateGraph(MakeupKitState)
graph.add_node("validate", validate_ingredients)
graph.add_node("certify", check_certifications)
graph.add_edge("validate", "certify")
graph.add_edge("certify", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()