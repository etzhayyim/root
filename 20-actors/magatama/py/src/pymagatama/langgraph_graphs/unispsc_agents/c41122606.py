from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    model_id: str
    specs: dict
    validation_log: List[str]

def validate_specs(state: DispenserState):
    log = []
    if not state['specs'].get('sterilization_compliance'):
        log.append('Error: Missing sterilization documentation.')
    return {'validation_log': log}

def approval_check(state: DispenserState):
    return 'APPROVED' if not state['validation_log'] else 'FLAGGED'

graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()