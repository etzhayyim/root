from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_specs: dict
    validation_log: List[str]
    approved: bool

def validate_copper_casting(state: ProcurementState):
    specs = state['part_specs']
    logs = []
    if 'grade' not in specs:
        logs.append('Validation Failed: Missing ASTM/ISO grade')
    if 'tolerance' not in specs:
        logs.append('Validation Failed: Dimensional tolerance required')
    return {'validation_log': logs, 'approved': len(logs) == 0}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_copper_casting)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()