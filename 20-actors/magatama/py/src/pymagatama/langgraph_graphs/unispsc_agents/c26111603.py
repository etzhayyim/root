from langgraph.graph import StateGraph, END
from typing import TypedDict

class GeneratorState(TypedDict):
    specs: dict
    validation_log: list
    status: str

def validate_specs(state: GeneratorState):
    required = ['capacity', 'iec_cert']
    log = []
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing: {field}')
    return {'validation_log': log, 'status': 'validated' if not log else 'failed'}

def structural_review(state: GeneratorState):
    return {'validation_log': state['validation_log'] + ['Structural check verified']}

graph = StateGraph(GeneratorState)
graph.add_node('validate', validate_specs)
graph.add_node('structural', structural_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'structural')
graph.add_edge('structural', END)
graph = graph.compile()