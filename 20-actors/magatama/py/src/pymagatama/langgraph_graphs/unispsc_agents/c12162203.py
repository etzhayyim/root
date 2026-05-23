from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    material_code: str
    purity_level: float
    hazard_check: bool
    validation_log: Annotated[Sequence[str], operator.add]

def validate_catalyst_purity(state: CatalystState):
    is_pure = state['purity_level'] >= 99.5
    return {'validation_log': [f'Purity check: {is_pure} (Level: {state['purity_level']}%)']}

def safety_compliance_check(state: CatalystState):
    is_safe = not state['hazard_check']
    return {'validation_log': [f'Safety check: {is_safe}']}

graph = StateGraph(CatalystState)
graph.add_node('purity_check', validate_catalyst_purity)
graph.add_node('safety_check', safety_compliance_check)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
