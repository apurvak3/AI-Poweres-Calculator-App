from fastapi import FastAPI, APIRouter, Request 
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import google.generativeai as genai
import base64
import json
from io import BytesIO
from PIL import Image
import ast
import os
from dotenv import load_dotenv

templates = Jinja2Templates(directory="templates")



# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERVER_URL = os.getenv("SERVER_URL", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
ENV = os.getenv("ENV", "dev")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request schema
class ImageData(BaseModel):
    image: str  # Base64 image
    dict_of_vars: dict = {}

# API Router
router = APIRouter()

def analyze_image(img: Image, dict_of_vars: dict):
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    dict_of_vars_str = json.dumps(dict_of_vars, ensure_ascii=False)

    # Convert image to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")  # Ensure PNG format
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    prompt = (
        f"You are given an image containing mathematical expressions, equations, or graphical problems. Solve them accurately. "
        f"Use PEMDAS for expressions. You can have five types of cases: "
        f"1. Simple math expressions (e.g., 2+2). Return a list of one dict. "
        f"2. Set of equations (e.g., x^2+2x+1=0). Solve for variables and return multiple dicts. "
        f"3. Assignments (e.g., x=4). Mark 'assign' as True. "
        f"4. Graphical math problems (e.g., trigonometry, physics). Return one dict. "
        f"5. Abstract concepts (e.g., emotions, history). Return one dict. "
        f"Given user variables: {dict_of_vars_str}."
    )

    # Send both prompt and image to Gemini
    response = model.generate_content([prompt, {"type": "image/png", "data": img_base64}])

    print(response.text)

    try:
        answers = ast.literal_eval(response.text)
    except Exception as e:
        print(f"Error parsing response: {e}")
        answers = []

    for answer in answers:
        answer['assign'] = answer.get('assign', False)

    return answers

@router.post("/")
async def run(data: ImageData):
    # Ensure proper base64 decoding
    header, encoded = data.image.split(",", 1)  # Split on first comma
    image_data = base64.b64decode(encoded)
    
    image_bytes = BytesIO(image_data)
    image = Image.open(image_bytes)

    # Process Image
    responses = analyze_image(image, dict_of_vars=data.dict_of_vars)

    return {"message": "Image processed", "data": responses, "status": "success"}


app.include_router(router, prefix="/calculate", tags=["calculate"])

@app.get("/")
async def serve_homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True, loop="auto")  # Changed to 8001

