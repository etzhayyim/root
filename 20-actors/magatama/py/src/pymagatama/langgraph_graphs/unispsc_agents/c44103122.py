import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class PrintBandState(TypedDict):
    part_number: str
    specs: dict
    validation_result: bool

def validate_specs(state: PrintBandState):
    # Business logic for validation
    is_valid = 'material' in state['specs']
    return {'validation_result': is_valid}

workflow = StateGraph(PrintBandState)
workflow.add_node('validator', validate_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()