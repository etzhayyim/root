from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GearProcurementState(TypedDict):
    gear_ratio: float
    material: str
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: GearProcurementState):
    log = state.get('validation_log', [])
    is_compliant = state['gear_ratio'] > 0 and state['material'] != 'unknown'
    log.append(f'Validation result: {is_compliant}')
    return {'is_compliant': is_compliant, 'validation_log': log}

def check_export_control(state: GearProcurementState):
    log = state.get('validation_log', [])
    if state['material'] == 'titanium_alloy':
        log.append('Flag: Potential dual-use export control.')
    return {'validation_log': log}

graph = StateGraph(GearProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()