from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicroscopeState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list

def validate_specs(state: MicroscopeState):
    required = ['magnification', 'class_ii_clearance']
    log = []
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing {field}')
    return {'validation_log': log, 'approved': len(log) == 0}

def finalize_order(state: MicroscopeState):
    return {'validation_log': state['validation_log'] + ['Order verification complete']}

graph = StateGraph(MicroscopeState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
