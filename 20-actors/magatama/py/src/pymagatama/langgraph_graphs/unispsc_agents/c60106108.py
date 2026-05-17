from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HazardState(TypedDict):
    materials: List[str]
    compliance_docs: List[str]
    hazard_level: str
    approved: bool

def validate_materials(state: HazardState):
    # Simulate safety check for hazardous teaching materials
    hazard_check = all('SDS' in doc for doc in state['compliance_docs'])
    return {'approved': hazard_check}

def safety_routing(state: HazardState):
    return 'process' if state['approved'] else END

graph_builder = StateGraph(HazardState)
graph_builder.add_node('safety_check', validate_materials)
graph_builder.set_entry_point('safety_check')
graph_builder.add_edge('safety_check', END)
graph = graph_builder.compile()