from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoffeeWarmerState(TypedDict):
    model_id: str
    temperature_profile: str
    compliance_checked: bool
    approved: bool

def validate_specs(state: CoffeeWarmerState):
    # Business logic for commercial warmer safety checking
    state['compliance_checked'] = True
    state['approved'] = True if state['temperature_profile'] == 'standard_85C' else False
    return state

builder = StateGraph(CoffeeWarmerState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
