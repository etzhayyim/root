from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalSupplyState(TypedDict):
    supply_id: str
    material: str
    is_sterile: bool
    compliance_ok: bool

def validate_materials(state: SurgicalSupplyState):
    # Business logic for surgical hand protector material validation
    state['compliance_ok'] = state['material'] in ['Nitrile', 'Latex', 'Neoprene']
    return state

def check_sterility(state: SurgicalSupplyState):
    # Logic for confirming sterility logs
    if not state.get('is_sterile'):
        print('Non-sterile item detected - flagging for review.')
    return state

graph = StateGraph(SurgicalSupplyState)
graph.add_node('validate', validate_materials)
graph.add_node('sterility', check_sterility)
graph.add_edge('validate', 'sterility')
graph.add_edge('sterility', END)
graph.set_entry_point('validate')

# Compile the graph
app = graph.compile()