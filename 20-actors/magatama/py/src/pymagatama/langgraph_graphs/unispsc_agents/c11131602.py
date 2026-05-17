from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SiWaferState(TypedDict):
    spec_requirements: dict
    inspection_results: Annotated[Sequence[dict], operator.add]
    is_compliant: bool

def validate_purity(state: SiWaferState):
    purity = state['spec_requirements'].get('purity_grade', 0)
    return {'inspection_results': [{'step': 'purity', 'passed': purity >= 99.9999999}] }

def check_defects(state: SiWaferState):
    defects = state['spec_requirements'].get('defect_density', 10)
    return {'inspection_results': [{'step': 'defects', 'passed': defects < 1}] }

def finalize_compliance(state: SiWaferState):
    all_passed = all(r['passed'] for r in state['inspection_results'])
    return {'is_compliant': all_passed}

graph = StateGraph(SiWaferState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_defects', check_defects)
graph.add_node('compliance', finalize_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_defects')
graph.add_edge('check_defects', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()