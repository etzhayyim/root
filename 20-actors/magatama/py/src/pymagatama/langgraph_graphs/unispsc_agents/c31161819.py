from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    part_numbers: List[str]
    compliance_checked: bool
    validation_log: List[str]

def validate_specs(state: WasherState):
    log = [f'Validating {p}' for p in state['part_numbers']]
    return {'validation_log': log, 'compliance_checked': True}

def finalize_order(state: WasherState):
    return {'validation_log': state['validation_log'] + ['Order ready for procurement']}

graph = StateGraph(WasherState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
app = graph.compile()