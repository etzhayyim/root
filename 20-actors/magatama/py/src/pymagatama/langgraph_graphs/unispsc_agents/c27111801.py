from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TapeMeasureState(TypedDict):
    specs: dict
    validation_result: bool
    errors: List[str]

def validate_specs(state: TapeMeasureState):
    errors = []
    if state['specs'].get('length', 0) <= 0:
        errors.append('Invalid length')
    return {'validation_result': len(errors) == 0, 'errors': errors}

graph_builder = StateGraph(TapeMeasureState)
graph_builder.add_node('validator', validate_specs)
graph_builder.set_entry_point('validator')
graph_builder.add_edge('validator', END)
graph = graph_builder.compile()