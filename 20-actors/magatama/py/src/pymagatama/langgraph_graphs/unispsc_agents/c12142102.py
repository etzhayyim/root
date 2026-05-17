from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class EthanolState(TypedDict):
    purity: float
    safety_check_passed: bool
    log: Annotated[list[str], operator.add]

def validate_purity(state: EthanolState):
    if state['purity'] >= 99.5:
        return {'safety_check_passed': True, 'log': ['Purity validation passed']}
    return {'safety_check_passed': False, 'log': ['Purity below threshold']}

def process_procurement(state: EthanolState):
    if state['safety_check_passed']:
        return {'log': ['Procurement order generated']}
    return {'log': ['Procurement halted due to quality']}

graph = StateGraph(EthanolState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()