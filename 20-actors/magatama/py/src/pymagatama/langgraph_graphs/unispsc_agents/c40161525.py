from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterHousingState(TypedDict):
    spec_sheet: dict
    validation_results: dict

def validate_pressure_compliance(state: FilterHousingState):
    pressure = state['spec_sheet'].get('max_pressure')
    state['validation_results'] = {'pressure_ok': pressure > 0}
    return state

def check_material_safety(state: FilterHousingState):
    material = state['spec_sheet'].get('material')
    state['validation_results']['material_compatible'] = material in ['SS316', 'Carbon Steel', 'Polypropylene']
    return state

graph = StateGraph(FilterHousingState)
graph.add_node("validate_pressure", validate_pressure_compliance)
graph.add_node("check_material", check_material_safety)
graph.set_entry_point("validate_pressure")
graph.add_edge("validate_pressure", "check_material")
graph.add_edge("check_material", END)
compiled_graph = graph.compile()