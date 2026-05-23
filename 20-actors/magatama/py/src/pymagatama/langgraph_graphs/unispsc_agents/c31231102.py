from typing import TypedDict
from langgraph.graph import StateGraph, END

class BerylliumStockState(TypedDict):
    purity_level: float
    toxic_handling_approved: bool
    export_license_verified: bool

def validate_material(state: BerylliumStockState):
    assert state['purity_level'] >= 99.0, 'Purity insufficient'
    return {'toxic_handling_approved': True}

def check_compliance(state: BerylliumStockState):
    return {'export_license_verified': state['export_license_verified']}

graph = StateGraph(BerylliumStockState)
graph.add_node('validation', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validation', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validation')
graph = graph.compile()
