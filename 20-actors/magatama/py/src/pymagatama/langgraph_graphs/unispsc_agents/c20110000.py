from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ProcurementState(TypedDict):
    part_numbers: List[str]
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_part(state: ProcurementState):
    log = [f'Validating part: {p}' for p in state['part_numbers']]
    return {'validation_log': log}

def check_compliance(state: ProcurementState):
    is_approved = len(state['part_numbers']) > 0
    return {'is_approved': is_approved}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_part)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
