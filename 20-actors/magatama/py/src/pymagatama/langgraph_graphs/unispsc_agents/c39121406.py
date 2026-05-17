from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReceptacleState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: ReceptacleState):
    required = ['Voltage Rating', 'Amperage', 'Safety Certification']
    compliance = all(key in state['spec_data'] for key in required)
    return {"is_compliant": compliance}

graph = StateGraph(ReceptacleState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()