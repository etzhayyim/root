from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ModelState(TypedDict):
    model_type: str
    parts_count: int
    is_validated: bool

def validate_model_components(state: ModelState):
    print(f'Validating components for {state['model_type']}...')
    validated = state['parts_count'] > 0
    return {'is_validated': validated}

workflow = StateGraph(ModelState)
workflow.add_node('validator', validate_model_components)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()