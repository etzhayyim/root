from typing import TypedDict
from langgraph.graph import StateGraph, END

class TransferBenchState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: TransferBenchState):
    log = []
    compliant = True
    if state['spec_data'].get('weight_capacity_kg', 0) < 150:
        log.append('Weight capacity below safety threshold')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(TransferBenchState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()