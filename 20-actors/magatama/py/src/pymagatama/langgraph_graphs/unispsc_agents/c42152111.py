from typing import TypedDict
from langgraph.graph import StateGraph, END
class DentalState(TypedDict):
    material_id: str
    curing_spec: float
    compliance_ok: bool
class HardenerProcessor:
    def validate_specs(self, state: DentalState) -> DentalState:
        state['compliance_ok'] = state['curing_spec'] > 0
        return state
    def check_safety(self, state: DentalState) -> DentalState:
        if state['compliance_ok']:
            print(f'Processing material {state["material_id"]} for clinical use.')
        return state
processor = HardenerProcessor()
graph = StateGraph(DentalState)
graph.add_node('validate', processor.validate_specs)
graph.add_node('safety', processor.check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
