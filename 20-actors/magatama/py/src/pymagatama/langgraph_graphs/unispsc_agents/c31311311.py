from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    material: str
    pressure_test: bool
    compliance_docs: List[str]

def validate_material(state: PipeState):
    return {'material': 'Waspalloy' if state['material'] == 'Waspalloy' else 'Invalid'}

def verify_specs(state: PipeState):
    is_compliant = state['pressure_test'] and len(state['compliance_docs']) > 0
    return {'pressure_test': is_compliant}

graph = StateGraph(PipeState)
graph.add_node("validate", validate_material)
graph.add_node("verify", verify_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", "verify")
graph.add_edge("verify", END)
app = graph.compile()