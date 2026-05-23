from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScrapbookPaperState(TypedDict):
    paper_weight: int
    is_acid_free: bool
    passed_validation: bool

def validate_paper_quality(state: ScrapbookPaperState):
    if state['paper_weight'] >= 160 and state['is_acid_free']:
        return {'passed_validation': True}
    return {'passed_validation': False}

graph_builder = StateGraph(ScrapbookPaperState)
graph_builder.add_node('validate', validate_paper_quality)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
