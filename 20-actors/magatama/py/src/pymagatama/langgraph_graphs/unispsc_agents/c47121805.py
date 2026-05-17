from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CleaningSpec(TypedDict):
    pressure: float
    flow_rate: float
    safety_compliant: bool

class CleaningState(TypedDict):
    specs: CleaningSpec
    validation_log: List[str]

def validate_specs(state: CleaningState):
    log = []
    if state['specs']['pressure'] > 50.0:
        log.append('High-pressure safety protocols triggered.')
    if not state['specs']['safety_compliant']:
        log.append('Safety compliance failure.')
    return {'validation_log': log}

graph = StateGraph(CleaningState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()