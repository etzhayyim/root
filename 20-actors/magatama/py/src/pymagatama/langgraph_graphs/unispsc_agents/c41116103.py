from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodBankState(TypedDict):
    lot_id: str
    temp_log: list
    qc_passed: bool

def validate_cold_chain(state: BloodBankState):
    # Business logic for cold chain monitoring verification
    return {'qc_passed': all(t < 8.0 for t in state['temp_log'])} if state['temp_log'] else {'qc_passed': False}

def update_inventory(state: BloodBankState):
    print(f'Updating inventory for lot: {state.get('lot_id')}')
    return {}

graph = StateGraph(BloodBankState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()
