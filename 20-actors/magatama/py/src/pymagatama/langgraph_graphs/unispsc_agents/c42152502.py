from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalBibState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_materials(state: DentalBibState):
    data = state['spec_data']
    valid = data.get('layers', 0) >= 2 and data.get('is_waterproof', False)
    return {'validation_passed': valid, 'error_log': [] if valid else ['Invalid material specs']}

def finish(state: DentalBibState):
    return state

graph = StateGraph(DentalBibState)
graph.add_node('validate', validate_materials)
graph.add_node('finish', finish)
graph.add_edge('validate', 'finish')
graph.set_entry_point('validate')
graph.set_finish_point('finish')
graph = graph.compile()