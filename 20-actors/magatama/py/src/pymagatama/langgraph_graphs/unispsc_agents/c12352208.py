from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CatalystState(TypedDict):
    material_id: str
    purity: float
    safety_check_passed: bool
    log: Annotated[list, add_messages]

def validate_catalyst_purity(state: CatalystState):
    is_valid = state['purity'] >= 99.5
    return {'safety_check_passed': is_valid, 'log': [f'Purity check: {is_valid}']}

def process_safety_clearance(state: CatalystState):
    if not state['safety_check_passed']:
        raise ValueError('Safety clearance denied due to purity standards.')
    return {'log': ['Safety clearance processed successfully']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_catalyst_purity)
graph.add_node('safety', process_safety_clearance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
