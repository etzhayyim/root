from typing import TypedDict
from langgraph.graph import StateGraph, END

class OCRProcessState(TypedDict):
    input_path: str
    config: dict
    validation_result: bool
    engine_output: str

def validate_format(state: OCRProcessState):
    path = state['input_path']
    return {'validation_result': path.lower().endswith(('.pdf', '.tiff', '.png'))}

def run_ocr(state: OCRProcessState):
    # Simulate high-precision OCR extraction workflow
    return {'engine_output': 'Processed text data extraction complete.'}

graph = StateGraph(OCRProcessState)
graph.add_node('validate', validate_format)
graph.add_node('execute', run_ocr)
graph.add_edge('validate', 'execute')
graph.add_edge('execute', END)
graph.set_entry_point('validate')
ocr_workflow = graph.compile()