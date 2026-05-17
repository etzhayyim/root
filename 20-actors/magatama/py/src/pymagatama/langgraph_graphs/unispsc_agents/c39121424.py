from typing import TypedDict
from langgraph.graph import StateGraph, END

class TerminalBlockState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_insulation(state: TerminalBlockState):
    rating = state['spec_data'].get('UL94_rating')
    return {'is_compliant': rating in ['V-0', 'V-1']}

def router(state: TerminalBlockState):
    return 'validate' if state.get('spec_data') else END

graph = StateGraph(TerminalBlockState)
graph.add_node('validate', validate_insulation)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()