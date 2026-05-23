from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    temp_rating: float
    material_compliance: bool
    is_validated: bool

def validate_specs(state: StorageState):
    state['is_validated'] = state['temp_rating'] <= -150 and state['material_compliance']
    return state

workflow = StateGraph(StorageState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
