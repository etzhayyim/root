from typing import TypedDict
from langgraph.graph import StateGraph, END

class DressingState(TypedDict):
    spec_data: dict
    validation_status: str

def validate_tech_specs(state: DressingState):
    required = ['material_safety', 'accuracy_ref']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_status': 'passed' if valid else 'rejected'}

def process_content(state: DressingState):
    # Simulate content validation for training modules
    print('Processing training content for anatomical accuracy...')
    return {'validation_status': 'verified'}

graph = StateGraph(DressingState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('process', process_content)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
