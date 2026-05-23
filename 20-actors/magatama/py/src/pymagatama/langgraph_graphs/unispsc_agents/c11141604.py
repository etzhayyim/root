from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CarbonFiberState(TypedDict):
    material_id: str
    specifications: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_tensile_strength(state: CarbonFiberState):
    strength = state['specifications'].get('tensile_strength_mpa', 0)
    if strength >= 3000:
        return {'validation_logs': ['Tensile strength meets aerospace standards'], 'is_compliant': True}
    return {'validation_logs': ['Tensile strength below threshold'], 'is_compliant': False}

def check_dual_use(state: CarbonFiberState):
    if state['specifications'].get('export_license_number'):
        return {'validation_logs': ['Export compliance confirmed'], 'is_compliant': True}
    return {'validation_logs': ['Export license required for this grade'], 'is_compliant': False}

graph = StateGraph(CarbonFiberState)
graph.add_node('validate_physics', validate_tensile_strength)
graph.add_node('verify_regulatory', check_dual_use)
graph.set_entry_point('validate_physics')
graph.add_edge('validate_physics', 'verify_regulatory')
graph.add_edge('verify_regulatory', END)
graph = graph.compile()
