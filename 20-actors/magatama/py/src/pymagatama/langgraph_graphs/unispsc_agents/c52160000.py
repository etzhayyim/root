from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectronicsState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: ElectronicsState):
    log = []
    required = ['cert_mark', 'voltage']
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing {field}')
    return {'is_compliant': len(log) == 0, 'validation_log': log}

graph = StateGraph(ElectronicsState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()