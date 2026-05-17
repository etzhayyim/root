from typing import TypedDict, Annotated, Sequence, List
from langgraph.graph import StateGraph, END
import operator

class SemiconductorState(TypedDict):
    purity: float
    specs: List[str]
    validation_log: Annotated[List[str], operator.add]

def validate_purity(state: SemiconductorState) -> dict:
    if state['purity'] < 99.99:
        return {'validation_log': ['Critical: Purity below 99.99 threshold.']}
    return {'validation_log': ['Purity validation passed.']}

def check_compliance(state: SemiconductorState) -> dict:
    if 'iso_9001' not in state['specs']:
        return {'validation_log': ['Warning: ISO 9001 missing.']}
    return {'validation_log': ['Compliance check passed.']}

graph = StateGraph(SemiconductorState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()