from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PillOrganizerState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_accessibility(state: PillOrganizerState):
    log = state.get('validation_log', [])
    compliance = state['specs'].get('accessibility_certified', False)
    log.append('Checked ADA/Accessibility compliance')
    return {'is_compliant': compliance, 'validation_log': log}

def check_material_safety(state: PillOrganizerState):
    log = state.get('validation_log', [])
    is_safe = state['specs'].get('bpa_free', True)
    log.append('Validated chemical safety for medical use')
    return {'is_compliant': state['is_compliant'] and is_safe, 'validation_log': log}

graph = StateGraph(PillOrganizerState)
graph.add_node('accessibility', validate_accessibility)
graph.add_node('safety', check_material_safety)
graph.set_entry_point('accessibility')
graph.add_edge('accessibility', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()