from typing import TypedDict
from langgraph.graph import StateGraph, END

class CorkState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_cork_spec(state: CorkState):
    # Business logic for food-grade cork inspection
    moisture = state['spec_data'].get('moisture_content', 0)
    compliant = 4.0 <= moisture <= 8.0
    return {'is_compliant': compliant}

workflow = StateGraph(CorkState)
workflow.add_node('validate', validate_cork_spec)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()