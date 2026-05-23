from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class InorganicState(TypedDict):
    material_id: str
    purity: float
    safety_check_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: InorganicState) -> InorganicState:
    if state['purity'] >= 99.9:
        return {'safety_check_passed': True, 'log': ['Purity validation passed']}
    return {'safety_check_passed': False, 'log': ['Purity validation failed']}

def check_sds(state: InorganicState) -> InorganicState:
    if state['safety_check_passed']:
        return {'log': ['SDS documentation confirmed']}
    return {'log': ['SDS documentation missing']}

graph = StateGraph(InorganicState)
graph.add_node('validate', validate_purity)
graph.add_node('sds_check', check_sds)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sds_check')
graph.add_edge('sds_check', END)

# Compile the graph
app = graph.compile()
