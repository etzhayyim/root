from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FountainState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_nsf_compliance(state: FountainState):
    compliance = state['specs'].get('compliance_standard')
    return {'validated': compliance == 'NSF/ANSI 61', 'compliance_report': 'Validated against NSF standards'}

def process_fountain_order(state: FountainState):
    return {'compliance_report': 'Process completed for drinking unit deployment'}

builder = StateGraph(FountainState)
builder.add_node('validate', validate_nsf_compliance)
builder.add_node('process', process_fountain_order)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()
