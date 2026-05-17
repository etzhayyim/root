from langgraph.graph import StateGraph, END
from typing import TypedDict

class SludgeCollectorState(TypedDict):
    equipment_spec: dict
    validation_checklist: list
    is_compliant: bool

def validate_specs(state: SludgeCollectorState):
    specs = state['equipment_spec']
    compliance = 'corrosion_rating' in specs and 'flow_rate' in specs
    return {'is_compliant': compliance, 'validation_checklist': ['Spec integrity check']}

def process_procurement(state: SludgeCollectorState):
    if state['is_compliant']:
        return {'validation_checklist': state['validation_checklist'] + ['Material safety verified']}
    return {'validation_checklist': state['validation_checklist'] + ['FAILED_COMPLIANCE']}

graph = StateGraph(SludgeCollectorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')