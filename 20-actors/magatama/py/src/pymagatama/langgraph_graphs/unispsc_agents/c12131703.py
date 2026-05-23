from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class SilaneProcessState(TypedDict):
    purity_level: float
    contamination_trace: List[str]
    validation_passed: bool

def validate_purity(state: SilaneProcessState):
    passed = state['purity_level'] >= 99.9999
    return {'validation_passed': passed}

def check_contaminants(state: SilaneProcessState):
    if any('metal' in c for c in state['contamination_trace']):
        return {'validation_passed': False}
    return {'validation_passed': True}

graph = StateGraph(SilaneProcessState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_contaminants', check_contaminants)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_contaminants')
graph.add_edge('check_contaminants', END)
app = graph.compile()
