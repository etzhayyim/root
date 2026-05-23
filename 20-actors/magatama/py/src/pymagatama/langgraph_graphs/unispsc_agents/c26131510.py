import operator
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PlantState(TypedDict):
    specifications: dict
    validation_results: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_emissions(state: PlantState):
    compliance = state['specifications'].get('emissions_level', 0) < 50
    return {'validation_results': ['Emissions Check: ' + ('Pass' if compliance else 'Fail')], 'is_compliant': compliance}

def structural_check(state: PlantState):
    is_safe = state['specifications'].get('seismic_rating', 0) >= 7
    return {'validation_results': ['Seismic Check: ' + ('Pass' if is_safe else 'Fail')], 'is_compliant': is_safe}

graph = StateGraph(PlantState)
graph.add_node('emissions', validate_emissions)
graph.add_node('structure', structural_check)
graph.set_entry_point('emissions')
graph.add_edge('emissions', 'structure')
graph.add_edge('structure', END)
app = graph.compile()
