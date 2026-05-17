from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PickerState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: PickerState):
    log = []
    compliant = True
    if state['specs'].get('weight_capacity_kg', 0) < 0.5:
        log.append('Weight capacity too low for industrial use.')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(PickerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()