from typing import TypedDict
from langgraph.graph import StateGraph, END

class CanvasPaperState(TypedDict):
    paper_gsm: int
    texture_type: str
    is_acid_free: bool
    validation_passed: bool

def validate_specs(state: CanvasPaperState):
    passed = state['paper_gsm'] >= 200 and state['is_acid_free']
    return {'validation_passed': passed}

def finish_process(state: CanvasPaperState):
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(CanvasPaperState)
graph.add_node('validate', validate_specs)
graph.add_node('finish', finish_process)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph = graph.compile()
