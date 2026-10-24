import base64
from openai import OpenAI
from .config import settings

def enabled():
    return bool(settings.openai_api_key.strip())

def ask(system, prompt, image=None, mime='image/jpeg'):
    if not enabled():
        return ''
    client = OpenAI(api_key=settings.openai_api_key)
    user_content = prompt
    if image is not None:
        encoded = base64.b64encode(image).decode()
        user_content = [
            {'type':'text','text':prompt},
            {'type':'image_url','image_url':{'url':f'data:{mime};base64,{encoded}'}}
        ]
    response = client.chat.completions.create(
        model=settings.openai_model, temperature=0.2,
        messages=[{'role':'system','content':system},{'role':'user','content':user_content}]
    )
    return response.choices[0].message.content or ''
