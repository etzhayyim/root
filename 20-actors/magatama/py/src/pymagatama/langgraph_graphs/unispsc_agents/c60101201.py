from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class StickerProcurementState(TypedDict):
    status: str
    items: List[str]
    compliance_passed: bool

def validate_theme(state: StickerProcurementState):
    print('Validating content alignment...')
    state['compliance_passed'] = True
    return 'process_order'

def process_order(state: StickerProcurementState):
    print('Processing sticker shipment...')
    state['status'] = 'processed'
    return END

graph = StateGraph(StickerProcurementState)
graph.add_node('validate_theme', validate_theme)
graph.add_node('process_order', process_order)
graph.set_entry_point('validate_theme')
graph.add_edge('validate_theme', 'process_order')
graph.add_edge('process_order', END)
app = graph.compile()
