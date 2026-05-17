from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: StorageState):
    errors = []
    if 'capacity' not in state['specifications']: errors.append('Missing capacity')
    if 'raid_level' not in state['specifications']: errors.append('Missing RAID level')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(StorageState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()