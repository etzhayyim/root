from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TubeState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_materials(state: TubeState):
    grade = state['specs'].get('material_grade')
    is_valid = grade in ['ASTM A519', 'JIS G3445']
    return {'is_compliant': is_valid, 'validation_log': ['Material grade checked']}

def check_integrity(state: TubeState):
    pressure = state['specs'].get('pressure_rating', 0)
    if pressure > 5000: state['validation_log'].append('High pressure testing required')
    return {'validation_log': state['validation_log']}

graph = StateGraph(TubeState)
graph.add_node('material_check', validate_materials)
graph.add_node('integrity_check', check_integrity)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'integrity_check')
graph.add_edge('integrity_check', END)
app = graph.compile()
