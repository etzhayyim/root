from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeAccessoryState(TypedDict):
    part_number: str
    compatibility_confirmed: bool
    validation_error: str

def validate_accessory_specs(state: OfficeAccessoryState):
    # Simulate logic to check if the part number exists in the ERP catalog
    if state['part_number'].startswith('FAIL'):
        return {'compatibility_confirmed': False, 'validation_error': 'Invalid Part Number'}
    return {'compatibility_confirmed': True, 'validation_error': None}

def process_procurement(state: OfficeAccessoryState):
    print(f'Processing procurement for {state['part_number']}')
    return {}

graph = StateGraph(OfficeAccessoryState)
graph.add_node('validate', validate_accessory_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
app = graph.compile()
