from langgraph.graph import StateGraph, END
from typing import TypedDict
class TableState(TypedDict):
    spec: dict
    is_valid: bool
def validate_table_specs(state: TableState):
    s = state['spec']
    is_valid = s.get('max_weight', 0) > 0 and s.get('material') in ['Stainless Steel', 'Medical Grade Coated']
    return {'is_valid': is_valid}
workflow = StateGraph(TableState)
workflow.add_node('validate', validate_table_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
