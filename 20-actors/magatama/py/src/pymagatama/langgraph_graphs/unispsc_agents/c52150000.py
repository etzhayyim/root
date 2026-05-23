from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_safety(state: KitchenwareState):
    # Simulate material safety check
    docs = state.get('compliance_docs', [])
    is_approved = 'FDA' in docs or 'JIS' in docs
    return {'is_approved': is_approved}

def quality_check(state: KitchenwareState):
    print(f'Performing quality assurance on {state['item_name']}')
    return {}

graph = StateGraph(KitchenwareState)
graph.add_node('safety_check', validate_safety)
graph.add_node('quality_check', quality_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()
