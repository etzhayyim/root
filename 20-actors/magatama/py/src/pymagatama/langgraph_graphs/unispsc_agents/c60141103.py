from typing import TypedDict
from langgraph.graph import StateGraph, END

class CardState(TypedDict):
    card_type: str
    material_quality: str
    is_compliant: bool

def validate_materials(state: CardState):
    # Business logic for card quality assurance
    state['is_compliant'] = state.get('material_quality') == 'casino-grade'
    return state

def assembly_check(state: CardState):
    print(f'Checking specs for: {state.get('card_type')}')
    return 'end'

graph = StateGraph(CardState)
graph.add_node('validate', validate_materials)
graph.add_node('assemble', assembly_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
compile_graph = graph.compile()