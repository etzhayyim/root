from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SidingGraphState(TypedDict):
    material_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_material(state: SidingGraphState):
    errors = []
    if state.get('material_specs', {}).get('weather_rating') != 'Class A':
        errors.append('Weather resistance rating is below standard.')
    return {'validation_errors': errors}

def decision_node(state: SidingGraphState):
    return 'END' if not state['validation_errors'] else 'END'

graph = StateGraph(SidingGraphState)
graph.add_node('validate', validate_material)
graph.add_node('decision', decision_node)
graph.add_edge('validate', 'decision')
graph.set_entry_point('validate')
graph.add_edge('decision', END)
graph = graph.compile()
