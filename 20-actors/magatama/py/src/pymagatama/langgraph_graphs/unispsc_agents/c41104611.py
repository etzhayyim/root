from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    insulation_type: str
    thermal_rating: float
    compliance_docs: List[str]
    approved: bool

def validate_thermal_specs(state: FurnaceState):
    if state['thermal_rating'] > 1200:
        return {'approved': True}
    return {'approved': False}

def check_compliance(state: FurnaceState):
    return {'compliance_docs': ['MSDS', 'ISO-14001']}

graph = StateGraph(FurnaceState)
graph.add_node('validate', validate_thermal_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'validate')
graph.add_edge('validate', END)
compiled_graph = graph.compile()
