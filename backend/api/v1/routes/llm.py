from fastapi import APIRouter, HTTPException, Request
import openai
import os

router = APIRouter()

# Load your OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/chat")
async def llm(request: Request):
    try:
        # Parse the JSON body to get the message
        data = await request.json()
        prompt = data.get("message")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Call OpenAI's API with a different model
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",  # Change to your desired model
            prompt=prompt,
            max_tokens=150
        )
        print('4')
        return {"response": response.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
