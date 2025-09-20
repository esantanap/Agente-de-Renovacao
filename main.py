# main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from app.analisador import analisador

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação FastAPI
app = FastAPI(title="Agente de Renovação de Crédito", version="1.0.0")

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial do chat"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/analisar")
async def analisar_cliente(cpf: str = Form(...), pergunta: str = Form("")):
    """Endpoint para análise de cliente"""
    try:
        # Validar CPF (básico)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        if len(cpf_limpo) != 11:
            raise HTTPException(status_code=400, detail="CPF deve ter 11 dígitos")
        
        # Realizar análise
        resultado = analisador.analisar_cliente(cpf_limpo, pergunta)
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {"status": "OK", "message": "Agente de Renovação funcionando"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)