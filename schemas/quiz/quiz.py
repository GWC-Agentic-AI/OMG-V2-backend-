from pydantic import BaseModel, model_validator

class GenerateQuizRequest(BaseModel):
    auth : bool = True  
    num_of_questions: int

class TranslateRequest(BaseModel):
    auth : bool = True
    lang_code: str
    quiz_id:int
