from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChutneyState(TypedDict):
    product_name: str
    quality_docs: List[str]
    approved: bool

def validate_quality(state: ChutneyState):
    required = ['HACCP', 'IngredientsInfo']
    all_docs = all(doc in state['quality_docs'] for doc in required)
    return {'approved': all_docs}

def route_by_approval(state: ChutneyState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ChutneyState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()