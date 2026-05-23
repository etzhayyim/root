from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    spec_data: dict
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_specs(state: BearingState):
    log = []
    if state['spec_data'].get('load_rating_dynamic', 0) <= 0:
        log.append('Invalid load rating detected')
    return {'validation_log': log}

def quality_check(state: BearingState):
    approved = len(state['validation_log']) == 0
    return {'is_approved': approved}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('qc', quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()
