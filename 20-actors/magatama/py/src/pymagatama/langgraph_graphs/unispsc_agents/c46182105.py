from langgraph.graph import StateGraph, END
from typing import TypedDict
class ESDState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
def validate_esd_compliance(state: ESDState):
    resistance = state['spec_sheet'].get('surface_resistivity', 0)
    state['validation_passed'] = 1e6 <= resistance <= 1e9
    return state
graph = StateGraph(ESDState)
graph.add_node('validate', validate_esd_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()