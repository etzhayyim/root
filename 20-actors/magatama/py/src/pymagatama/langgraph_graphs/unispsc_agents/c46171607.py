from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BuzzerState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: BuzzerState):
    log = []
    compliant = True
    required = ['voltage', 'spl', 'frequency']
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing field: {field}')
            compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(BuzzerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()