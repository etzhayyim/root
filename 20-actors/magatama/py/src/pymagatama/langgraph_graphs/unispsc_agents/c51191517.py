from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    compliant: bool
    logs: List[str]

def validate_quality(state: ChemicalState):
    is_pure = state['purity'] >= 99.0
    return {'compliant': is_pure, 'logs': ['Purity check passed'] if is_pure else ['Purity check failed']}

def safety_check(state: ChemicalState):
    if state['compliant']:
        return {'logs': state['logs'] + ['MSDS verified']}
    return {'logs': state['logs'] + ['MSDS review skipped']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_quality)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
app = graph.compile()