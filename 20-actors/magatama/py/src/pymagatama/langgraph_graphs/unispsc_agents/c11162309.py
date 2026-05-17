from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity_level: float
    reaction_efficiency: float
    compliance_checks: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState):
    is_pure = state['purity_level'] > 0.98
    return {'compliance_checks': ['purity_passed'] if is_pure else ['purity_failed']}

def check_reactivity(state: CatalystState):
    is_efficient = state['reaction_efficiency'] > 0.85
    return {'compliance_checks': ['reactivity_passed'] if is_efficient else ['reactivity_failed']}

graph = StateGraph(CatalystState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_reactivity', check_reactivity)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_reactivity')
graph.add_edge('check_reactivity', END)
app = graph.compile()