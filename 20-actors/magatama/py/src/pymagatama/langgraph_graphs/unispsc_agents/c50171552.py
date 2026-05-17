from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SeasoningState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_ingredients(state: SeasoningState):
    errors = []
    if 'ingredients' not in state['spec_data']:
        errors.append('Missing ingredients list')
    if 'allergens' not in state['spec_data']:
        errors.append('Missing allergen disclosure')
    return {**state, 'validation_errors': errors}

def check_compliance(state: SeasoningState):
    approved = len(state['validation_errors']) == 0
    return {**state, 'approved': approved}

graph = StateGraph(SeasoningState)
graph.add_node('validate', validate_ingredients)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()