from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrawingPaperState(TypedDict):
    gsm: float
    acid_free: bool
    application: str
    validation_errors: List[str]

def validate_paper_specs(state: DrawingPaperState):
    errors = []
    if state['gsm'] < 60 or state['gsm'] > 200:
        errors.append('GSM out of typical drafting range')
    return {'validation_errors': errors}

workflow = StateGraph(DrawingPaperState)
workflow.add_node('validate', validate_paper_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
