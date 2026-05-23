from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CapState(TypedDict):
    specs: dict
    compliance_passed: bool
    validation_log: List[str]

def validate_compliance(state: CapState):
    s = state['specs']
    passed = s.get('material') == 'non-woven' and s.get('sterile') is True
    return {'compliance_passed': passed, 'validation_log': ['Compliance check completed']}

def route_by_compliance(state: CapState):
    return 'process' if state['compliance_passed'] else END

graph = StateGraph(CapState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', lambda s: {'validation_log': s['validation_log'] + ['Order ready for procurement']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
