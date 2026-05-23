from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict

class RibbonState(TypedDict):
    model_number: str
    is_compatible: bool
    validation_log: str

def validate_compatibility(state: RibbonState):
    # Business logic for ink ribbon compatibility check
    valid_models = ['EPSON-LQ-590', 'OKI-ML-8490']
    result = state['model_number'] in valid_models
    return {'is_compatible': result, 'validation_log': 'Compatibility confirmed' if result else 'Not compatible'}

def route_by_compatibility(state: RibbonState):
    return 'process' if state['is_compatible'] else END

graph = StateGraph(RibbonState)
graph.add_node('validate', validate_compatibility)
graph.add_node('process', lambda x: {'validation_log': 'Proceeding to procurement'})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compatibility)
graph.add_edge('process', END)
graph = graph.compile()
