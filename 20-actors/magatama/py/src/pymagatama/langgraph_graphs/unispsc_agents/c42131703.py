from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SurgicalPackState(TypedDict):
    pack_id: str
    is_sterile: bool
    compliance_docs: List[str]
    approved: bool

def validate_sterility(state: SurgicalPackState):
    return {"is_sterile": True}

def check_compliance(state: SurgicalPackState):
    required = ["ISO13485", "CE_Mark"]
    return {"approved": all(doc in state['compliance_docs'] for doc in required)}

graph = StateGraph(SurgicalPackState)
graph.add_node("validate", validate_sterility)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
compiled_graph = graph.compile()
