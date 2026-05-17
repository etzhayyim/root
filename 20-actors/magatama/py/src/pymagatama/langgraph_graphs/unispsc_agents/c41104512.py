from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OvenAccessoryState(TypedDict):
    part_number: str
    spec_compliance: bool
    thermal_rating: float
    validation_log: List[str]

def validate_specs(state: OvenAccessoryState):
    if state['thermal_rating'] < 300:
        return {'spec_compliance': False, 'validation_log': ['Thermal rating below safety threshold']}
    return {'spec_compliance': True, 'validation_log': ['Specs validated successfully']}

graph = StateGraph(OvenAccessoryState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()