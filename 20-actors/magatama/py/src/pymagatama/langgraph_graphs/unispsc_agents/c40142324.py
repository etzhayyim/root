from langgraph.graph import StateGraph, END; from typing import TypedDict; class ProcureState(TypedDict): specs: dict; valid: bool
def validate_specs(state: ProcureState): return {'valid': 'IP Rating' in state['specs'] and 'Material Composition' in state['specs']}
builder = StateGraph(ProcureState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()