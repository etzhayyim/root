from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class PhonicsState(TypedDict):
    book_title: str
    target_age: int
    compliance_checked: bool
    validation_errors: List[str]
def validate_book_specs(state: PhonicsState):
    errors = []
    if state['target_age'] < 3: errors.append('Age range below safety threshold')
    return {'validation_errors': errors, 'compliance_checked': len(errors) == 0}
def finalize_procurement(state: PhonicsState):
    return {'compliance_checked': True}
graph = StateGraph(PhonicsState)
graph.add_node('validate', validate_book_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')validate')
graph = graph.compile()