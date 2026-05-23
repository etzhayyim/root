from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpreadState(TypedDict):
    product_name: str
    allergen_info: list[str]
    compliance_passed: bool

def validate_ingredients(state: SpreadState):
    state['compliance_passed'] = 'peanut' in state['allergen_info'] or 'tree_nuts' in state['allergen_info']
    return state

def generate_report(state: SpreadState):
    print(f'Processing {state['product_name']}. Compliance status: {state['compliance_passed']}')
    return state

builder = StateGraph(SpreadState)
builder.add_node('validate', validate_ingredients)
builder.add_node('report', generate_report)
builder.add_edge('validate', 'report')
builder.add_edge('report', END)
builder.set_entry_point('validate')
graph = builder.compile()
