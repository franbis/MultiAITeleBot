from pydantic import BaseModel



class Translation(BaseModel):
	src_lang: str
	dst_lang: str
	original_text: str
	translated_text: str