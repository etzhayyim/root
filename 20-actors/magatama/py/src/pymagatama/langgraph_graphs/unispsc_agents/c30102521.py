from langgraph.graph import StateGraph, END
from typing import TypedDict

class FoamRubberState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: FoamRubberState):
    specs = state['spec_data']
    val_passed = ('thickness_tolerance_mm' in specs and 'flame_retardancy_rating' in specs)
    return {'validation_passed': val_passed}

def process_procurement(state: FoamRubberState):
    return {'error_log': ['Specs validated successfully'] if state['validation_passed'] else ['Missing critical specs']}

graph = StateGraph(FoamRubberState)
graph.add_node('validator', validate_specs)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validator')
graph.add_edge('validator', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()