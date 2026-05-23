from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CalamineState(TypedDict):
    batch_id: str
    quality_docs: List[str]
    is_compliant: bool

def validate_gmp(state: CalamineState):
    state['is_compliant'] = 'GMP' in state['quality_docs']
    return state

def check_expiry(state: CalamineState):
    print(f'Verifying shelf life for batch {state['batch_id']}')
    return state

graph = StateGraph(CalamineState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_expiry', check_expiry)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_expiry')
graph.add_edge('check_expiry', END)
graph = graph.compile()
