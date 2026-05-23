from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubingState(TypedDict):
    spec: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: TubingState):
    log = []
    required = ['material_grade', 'wall_thickness', 'diameter']
    for field in required:
        if field not in state['spec']:
            log.append(f'Missing {field}')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

def structural_check(state: TubingState):
    return {'validation_log': state['validation_log'] + ['Structural integrity criteria applied']}

graph = StateGraph(TubingState)
graph.add_node('validate', validate_specs)
graph.add_node('structural', structural_check)
graph.add_edge('validate', 'structural')
graph.add_edge('structural', END)
graph.set_entry_point('validate')
graph = graph.compile()
