from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class OxideState(TypedDict):
    raw_input: dict
    purity_check: bool
    validation_log: List[str]
    approved: bool

def validate_oxide_specs(state: OxideState):
    log = []
    purity = state['raw_input'].get('purity_percentage', 0)
    if purity >= 99.9:
        passed = True
        log.append(f'Purity {purity}% compliant.')
    else:
        passed = False
        log.append(f'Purity {purity}% insufficient.')
    return {'purity_check': passed, 'validation_log': log}

def final_approval(state: OxideState):
    return {'approved': state['purity_check']}

graph = StateGraph(OxideState)
graph.add_node('validate', validate_oxide_specs)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()