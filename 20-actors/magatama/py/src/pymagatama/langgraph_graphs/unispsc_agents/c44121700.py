from typing import TypedDict
from langgraph.graph import StateGraph, END

class WritingInstrumentState(TypedDict):
    item_name: str
    ink_level: float
    compliance_passed: bool

def validate_ink_spec(state: WritingInstrumentState):
    # Business logic for ink quality validation
    return {'compliance_passed': state.get('ink_level', 0) > 0.8}

def process_procurement(state: WritingInstrumentState):
    return {'item_name': f'Validated: {state['item_name']}'}

graph = StateGraph(WritingInstrumentState)
graph.add_node('validate', validate_ink_spec)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
