from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class EquipmentState(TypedDict):
    kit_id: str
    safety_certifications: List[str]
    verification_status: bool

def validate_certification(state: EquipmentState):
    required = ['EN1891', 'EN12278']
    valid = all(cert in state['safety_certifications'] for cert in required)
    return {'verification_status': valid}

def finalize_procurement(state: EquipmentState):
    return {'verification_status': True}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_certification)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
