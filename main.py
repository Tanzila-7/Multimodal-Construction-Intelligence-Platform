import json
from io import BytesIO
import httpx
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .ai import enabled, ask

app=FastAPI(title='Construction Intelligence API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])

class Valuation(BaseModel):
    location:str
    area_sqft:float=Field(gt=0)
    age_years:int=Field(default=0,ge=0)
    quality:str='Standard'
class Planning(BaseModel):
    project_name:str
    project_type:str='Residential'
    duration_weeks:int=Field(default=12,ge=1,le=260)
    budget_inr:float=Field(default=5000000,gt=0)
    notes:str=''
class Question(BaseModel):
    question:str
    context:str=''

@app.get('/')
def root(): return {'message':'Construction Intelligence API','docs':'/docs'}
@app.get('/api/health')
def health(): return {'status':'ok','mode':'AI' if enabled() else 'DEMO','ai_enabled':enabled()}

async def read_image(file):
    if file.content_type not in ('image/jpeg','image/png','image/webp'):
        raise HTTPException(400,'Use JPEG, PNG or WEBP.')
    data=await file.read()
    if len(data)>8*1024*1024: raise HTTPException(413,'Maximum image size is 8 MB.')
    try: Image.open(BytesIO(data)).verify()
    except (UnidentifiedImageError,OSError): raise HTTPException(400,'Invalid image.')
    return data,file.content_type

def parse(raw):
    raw=raw.strip()
    if raw.startswith('```'): raw=raw.split('\n',1)[-1].rsplit('```',1)[0]
    try: return json.loads(raw)
    except Exception: raise HTTPException(502,'AI returned invalid JSON.')

@app.post('/api/analyze/{kind}')
async def analyze(kind:str,file:UploadFile=File(...)):
    if kind not in ('safety','cracks'): raise HTTPException(404,'Unknown analysis module.')
    data,mime=await read_image(file)
    prompt=('Screen visible construction-site hazards such as PPE, falls, scaffolding, electrical risks and housekeeping.' if kind=='safety' else 'Screen for visible cracks and surface defects. Do not infer depth, cause or structural capacity.')
    system='You are a cautious construction visual screening assistant. Return JSON only: {"summary":"...","findings":[{"title":"...","severity":"low|medium|high|unknown","description":"...","recommendation":"..."}]}. Report uncertainty.'
    raw=ask(system,prompt,data,mime)
    if raw:
        result=parse(raw)
    else:
        result={'summary':'Demo mode: uploaded image is not interpreted without an AI API key.','findings':[{'title':'Professional review required','severity':'unknown','description':'Demo mode does not perform image-specific analysis.','recommendation':'Arrange an in-person review by the responsible safety officer or structural engineer.'}]}
    result.update({'module':kind,'limitations':'Preliminary visual screening only. Not a certified inspection or structural diagnosis.'})
    return result

@app.post('/api/valuation')
def valuation(req:Valuation):
    factor={'Basic':0.85,'Standard':1.0,'Premium':1.25}.get(req.quality,1.0)
    value=req.area_sqft*4500*factor*max(0.65,1-req.age_years*0.008)
    return {'estimated_value':round(value,2),'currency':'INR','assumptions':['Illustrative base rate ₹4,500/sqft',f'Location: {req.location}',f'Quality: {req.quality}'],'disclaimer':'Not a market appraisal. Verify local comparable sales, title, condition and legal details.'}

@app.post('/api/planning')
def planning(req:Planning):
    prompt=f'Return JSON only with keys milestones, tasks, assumptions. tasks array objects: task, week_start, week_end, dependency. Plan project {req.project_name}, type {req.project_type}, duration {req.duration_weeks} weeks, budget INR {req.budget_inr}.'
    raw=ask('You are a construction project planner. Output valid JSON only.',prompt)
    if raw: return {'project_name':req.project_name,**parse(raw)}
    w=req.duration_weeks
    names=['Survey and approvals','Design and procurement','Site preparation and foundation','Structure and envelope','MEP and finishing','Testing and handover']
    tasks=[]
    for i,n in enumerate(names):
        s=max(1,round(1+i*(w-1)/6)); e=min(w,max(s,round((i+1)*w/6)))
        tasks.append({'task':n,'week_start':s,'week_end':e,'dependency':names[i-1] if i else None})
    return {'project_name':req.project_name,'milestones':['Approvals','Foundation','Structure','Services tested','Handover'],'tasks':tasks,'assumptions':['Demo schedule; adapt to drawings, permits, procurement and site conditions.']}

@app.post('/api/assistant')
def assistant(req:Question):
    answer=ask('You are a practical construction knowledge assistant. Do not replace licensed engineering, legal or safety advice.',f'Context: {req.context}\nQuestion: {req.question}')
    return {'answer':answer or 'Demo answer: define the project context, consult drawings and applicable local codes, document measurable checks, and ask the responsible engineer or safety officer to verify critical decisions.','safety_note':'Verify safety-critical and structural guidance with qualified professionals.'}

@app.get('/api/weather')
async def weather(latitude:float,longitude:float):
    if not -90<=latitude<=90 or not -180<=longitude<=180: raise HTTPException(400,'Invalid coordinates.')
    params={'latitude':latitude,'longitude':longitude,'current':'temperature_2m,precipitation,wind_speed_10m,weather_code','daily':'precipitation_probability_max,wind_speed_10m_max','timezone':'auto'}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r=await client.get('https://api.open-meteo.com/v1/forecast',params=params); r.raise_for_status(); d=r.json()
    except httpx.HTTPError: raise HTTPException(502,'Weather service unavailable.')
    c=d.get('current',{}); rain=c.get('precipitation',0); wind=c.get('wind_speed_10m',0)
    advice='Rain reported: review excavation stability, electrical protection and slip hazards.' if rain and rain>0 else ('Strong wind: review lifting and work-at-height limits.' if wind and wind>30 else 'Continue routine site weather monitoring.')
    return {'current':c,'daily':d.get('daily',{}),'advisory':advice,'disclaimer':'Indicative only; follow official alerts and site procedures.'}
