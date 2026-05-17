from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CoatingState(TypedDict):
    purity: float
    grain_size: float
    inspection_passed: bool
    validation_log: List[str]

def validate_specs(state: CoatingState):
    log = []
    passed = True
    if state['purity'] < 99.999:
        log.append('Purity check failed: below 5N grade.')
        passed = False
    if state['grain_size'] > 50.0:
        log.append('Grain size excessive for PVD application.')
        passed = False
    return {'inspection_passed': passed, 'validation_log': log}

def finalize(state: CoatingState):
    return {'validation_log': state['validation_log'] + ['Process finalized.']}

graph = StateGraph(CoatingState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()