from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterState(TypedDict):
    filter_id: str
    compliance_docs: list
    is_validated: bool

def validate_specs(state: FilterState):
    state['is_validated'] = all(doc for doc in state['compliance_docs'])
    print(f'Validating filter {state['filter_id']}')
    return state

builder = StateGraph(FilterState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
