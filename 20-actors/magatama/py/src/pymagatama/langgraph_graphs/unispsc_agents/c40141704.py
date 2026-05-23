import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class SpigotState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: Annotated[list, operator.add]

def validate_spec(state: SpigotState):
    required = ['Material Grade', 'Pressure Rating']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_result': not missing, 'error_log': [f'Missing: {missing}'] if missing else []}

def approve_procurement(state: SpigotState):
    return {'validation_result': True}

graph = StateGraph(SpigotState)
graph.add_node('validate', validate_spec)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
