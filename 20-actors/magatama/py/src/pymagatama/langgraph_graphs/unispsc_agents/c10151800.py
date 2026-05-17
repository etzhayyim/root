from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    raw_batch_id: str
    purity: float
    origin: str
    compliant: bool
    history: List[str]

def validate_ore(state: MineralState):
    if state['purity'] > 0.95:
        return {'compliant': True, 'history': state['history'] + ['Purity check passed']}
    return {'compliant': False, 'history': state['history'] + ['Purity check failed']}

def route_by_compliance(state: MineralState):
    return 'process' if state['compliant'] else 'reject'

def process_ore(state: MineralState):
    return {'history': state['history'] + ['Processing through refinery queue']}

def reject_ore(state: MineralState):
    return {'history': state['history'] + ['Rejecting batch for quality variance']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_ore)
graph.add_node('process', process_ore)
graph.add_node('reject', reject_ore)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph.add_edge('reject', END)
graph = graph.compile()