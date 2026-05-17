from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    spec_data: dict
    validation_logs: List[str]
    approved: bool

def validate_catalyst_purity(state: CatalystState):
    purity = state['spec_data'].get('purity_percentage', 0)
    if purity >= 99.9:
        return {'validation_logs': ['Purity standard met'], 'approved': True}
    return {'validation_logs': ['Purity below threshold'], 'approved': False}

def route_by_validation(state: CatalystState):
    return 'process_order' if state['approved'] else 'reject_order'

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_catalyst_purity)
graph.add_node('process_order', lambda s: {'validation_logs': s['validation_logs'] + ['Processing']})
graph.add_node('reject_order', lambda s: {'validation_logs': s['validation_logs'] + ['Rejected']})

graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process_order', END)
graph.add_edge('reject_order', END)

graph = graph.compile()