from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RoadState(TypedDict):
    project_id: str
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_civil_specs(state: RoadState):
    specs = state['specifications']
    is_valid = all(k in specs for k in ['bearing_capacity', 'pavement_type'])
    return {'is_compliant': is_valid, 'validation_log': ['Specs checked']}

def approve_procurement(state: RoadState):
    return {'validation_log': state['validation_log'] + ['Procurement approved']}

graph = StateGraph(RoadState)
graph.add_node('validate', validate_civil_specs)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
