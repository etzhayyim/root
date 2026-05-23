from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ModuleState(TypedDict):
    part_number: str
    specs: dict
    validated: bool
    error_log: List[str]

def validate_specs(state: ModuleState):
    required = ['lumen', 'color_temp', 'voltage']
    missing = [f for f in required if f not in state['specs']]
    if missing:
        state['error_log'].append(f'Missing specs: {missing}')
        state['validated'] = False
    else:
        state['validated'] = True
    return state

def qc_check(state: ModuleState):
    if state['validated'] and state['specs'].get('voltage', 0) > 0:
        print('QC passed')
    return state

graph = StateGraph(ModuleState)
graph.add_node('validate', validate_specs)
graph.add_node('qc', qc_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()
