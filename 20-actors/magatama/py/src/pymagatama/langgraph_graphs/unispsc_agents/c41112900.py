from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NavState(TypedDict):
    equipment_id: str
    specs: dict
    validation_passed: bool
    compliance_tags: List[str]

def validate_nav_specs(state: NavState):
    required = ['calibration', 'imo_cert']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_export_control(state: NavState):
    tags = ['dual-use'] if state['specs'].get('precision') == 'military' else []
    return {'compliance_tags': tags}

graph = StateGraph(NavState)
graph.add_node('validate', validate_nav_specs)
graph.add_node('export', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()