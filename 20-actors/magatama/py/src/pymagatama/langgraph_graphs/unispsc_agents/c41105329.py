from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlockingAgentState(TypedDict):
    purity_level: float
    storage_temp: str
    is_compliant: bool

def validate_specs(state: BlockingAgentState):
    state['is_compliant'] = state['purity_level'] >= 0.99 and state['storage_temp'] in ['4C', '-20C']
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(BlockingAgentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
