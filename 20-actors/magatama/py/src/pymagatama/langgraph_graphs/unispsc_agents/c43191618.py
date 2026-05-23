from typing import TypedDict, Annotated, Sequence, Union
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class PeripheralState(TypedDict):
    item_name: str
    model: str
    compatibility_check: bool
    validation_log: Annotated[Sequence[str], add_messages]

def validate_peripheral(state: PeripheralState):
    log = f'Validating compatibility for {state['item_name']}'
    return {'compatibility_check': True, 'validation_log': [log]}

def generate_procurement_spec(state: PeripheralState):
    return {'validation_log': ['Spec generated successfully']}

graph = StateGraph(PeripheralState)
graph.add_node('validate', validate_peripheral)
graph.add_node('spec_gen', generate_procurement_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'spec_gen')
graph.add_edge('spec_gen', END)
graph = graph.compile()
