from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_material(state: PipeState):
    grade = state['spec_data'].get('ASTM_grade')
    is_valid = grade in ['Grade 2', 'Grade 5']
    return {'validation_log': [f'Material Grade check: {is_valid}'], 'is_compliant': is_valid}

def check_weld_integrity(state: PipeState):
    ultrasonic = state['spec_data'].get('ultrasonic_report')
    status = 'Pass' if ultrasonic else 'Fail'
    return {'validation_log': state['validation_log'] + [f'Weld Audit: {status}']}

graph = StateGraph(PipeState)
graph.add_node('material_check', validate_material)
graph.add_node('weld_audit', check_weld_integrity)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'weld_audit')
graph.add_edge('weld_audit', END)
graph = graph.compile()