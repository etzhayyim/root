from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PrintingGraphState(TypedDict):
    specs: dict
    validation_report: List[str]
    approved: bool

def validate_specs(state: PrintingGraphState):
    errors = []
    if state['specs'].get('accuracy', 0) < 0.05:
        errors.append('Registration accuracy insufficient for high-end gravure')
    return {'validation_report': errors, 'approved': len(errors) == 0}

graph = StateGraph(PrintingGraphState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
