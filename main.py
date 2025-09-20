# main.py - VERSÃO ATUALIZADA COM LÓGICA REAL
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from pathlib import Path

# Importar módulos da aplicação
try:
    from app.database import db
    from app.analisador import analisador
except ImportError:
    print("⚠️ Módulos da aplicação não encontrados. Criando estrutura...")
    # Criar diretório app se não existir
    if not Path("app").exists():
        os.makedirs("app")
        # Criar __init__.py
        with open("app/__init__.py", "w") as f:
            f.write("# Módulos da aplicação\n")
    
    # Importar após criar estrutura
    from app.database import db
    from app.analisador import analisador

# Criar diretórios necessários
for dir_path in ["templates", "static/css", "static/js"]:
    if not Path(dir_path).exists():
        os.makedirs(dir_path)
        print(f"�� Diretório '{dir_path}' criado")

# Criar instância do FastAPI
app = FastAPI(
    title="Agente de Renovação - BNB Crediamigo",
    description="Sistema inteligente de análise automática para renovação de crédito",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# =====================================================
# MODELOS DE DADOS
# =====================================================

class AnaliseRequest(BaseModel):
    cpf: str
    pergunta: str

# =====================================================
# ROTAS DA INTERFACE WEB
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página inicial - Interface do Chat"""
    try:
        return templates.TemplateResponse("chat.html", {"request": request})
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Agente de Renovação - BNB Crediamigo</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; }}
                .status {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .error {{ background: #fee; border-left: 4px solid #ef4444; }}
                .success {{ background: #efe; border-left: 4px solid #10b981; }}
                .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px; }}
                .code {{ background: #f1f5f9; padding: 10px; border-radius: 4px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Agente de Renovação</h1>
                <p>Sistema Inteligente de Análise de Crédito - BNB Crediamigo</p>
            </div>
            
            <div class="status error">
                <h2>❌ Interface em Configuração</h2>
                <p><strong>Erro:</strong> {str(e)}</p>
                <p>O arquivo de interface ainda não foi configurado.</p>
            </div>
            
            <div class="status success">
                <h2>✅ API Funcionando</h2>
                <p>O motor de análise está operacional. Você pode:</p>
                <a href="/docs" class="button">📖 Ver Documentação da API</a>
                <a href="/health" class="button">�� Verificar Status do Sistema</a>
                <a href="/test-db" class="button">🗄️ Testar Conexão com Banco</a>
            </div>
            
            <div class="status">
                <h2>🎯 Funcionalidades Disponíveis</h2>
                <ul>
                    <li><strong>Análise Automática:</strong> Classificação em Aprovável, Ressalvas ou Impedida</li>
                    <li><strong>Critérios Impeditivos:</strong> RFB, BNB, CADIN, Ciclos, Inadimplência</li>
                    <li><strong>Critérios Operacionais:</strong> Porte, Cadastro, Restrições Financeiras</li>
                    <li><strong>Respostas Contextuais:</strong> Baseadas na pergunta do usuário</li>
                </ul>
            </div>
        </body>
        </html>
        """, status_code=200)

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Interface do Chat"""
    return await root(request)

# =====================================================
# ROTAS DA API
# =====================================================

@app.get("/health")
async def health_check():
    """Verificação de saúde completa do sistema"""
    try:
        # Testar conexão com banco
        db_status = db.test_connection()
        
        return {
            "status": "healthy" if db_status else "degraded",
            "message": "Agente de Renovação operacional",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "database": "connected" if db_status else "disconnected",
                "analyzer": "operational",
                "api": "operational",
                "templates": Path("templates/chat.html").exists(),
                "static_files": Path("static").exists()
            },
            "business_rules": {
                "limite_ciclos": 5,
                "limite_inadimplencia_dias": 30,
                "porte_esperado": "Crediamigo",
                "tipo_cadastro_esperado": "Completo"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Erro no sistema: {str(e)}",
            "components": {
                "database": "error",
                "analyzer": "unknown",
                "api": "operational"
            }
        }

@app.get("/test-db")
async def test_database():
    """Testar conexão específica com banco de dados"""
    try:
        if db.test_connection():
            # Buscar estatísticas básicas
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE rfb_restricao = '1' OR bnb_restricao = '1'")
            com_restricoes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE quantidade_ciclos_credito > 5")
            excesso_ciclos = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "database_status": "connected",
                "statistics": {
                    "total_clientes": total_clientes,
                    "com_restricoes": com_restricoes,
                    "excesso_ciclos": excesso_ciclos
                },
                "message": "Banco de dados operacional"
            }
        else:
            return {
                "database_status": "disconnected",
                "message": "Falha na conexão com banco de dados"
            }
    except Exception as e:
        return {
            "database_status": "error",
            "message": f"Erro ao testar banco: {str(e)}"
        }

@app.post("/api/v1/analisar")
async def analisar_cliente(request: AnaliseRequest):
    """
    Analisar elegibilidade de cliente para renovação de crédito
    Aplica regras de negócio completas baseadas em critérios impeditivos e operacionais
    """
    try:
        # Validar CPF básico
        cpf = request.cpf.replace(".", "").replace("-", "").strip()
        if not cpf.isdigit() or len(cpf) != 11:
            raise HTTPException(status_code=400, detail="CPF inválido. Deve conter 11 dígitos.")
        
        # Executar análise completa
        resultado = analisador.analisar_cliente(cpf, request.pergunta)
        
        if resultado.get("erro"):
            if "não encontrado" in resultado.get("mensagem", "").lower():
                raise HTTPException(status_code=404, detail=resultado["mensagem"])
            else:
                raise HTTPException(status_code=500, detail=resultado["mensagem"])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno na análise: {str(e)}")

@app.get("/api/v1/criterios")
async def obter_criterios():
    """Obter critérios de negócio aplicados na análise"""
    return {
        "criterios_impeditivos": {
            "restricoes_rfb": "Não permitido",
            "restricoes_bnb": "Não permitido", 
            "debitos_cadin": "Valor deve ser zero",
            "limite_ciclos_credito": 5,
            "limite_inadimplencia_dias": 30
        },
        "criterios_operacionais": {
            "situacao_cadastral": "Ativo",
            "porte_esperado": "Crediamigo",
            "tipo_cadastro_esperado": "Completo",
            "restricoes_serasa": "Verificadas",
            "restricoes_spc": "Verificadas"
        },
        "decisoes_possiveis": {
            "aprovavel": "Sem impedimentos críticos ou operacionais",
            "ressalvas": "Requer ajustes operacionais",
            "impedida": "Impedimentos críticos detectados"
        }
    }

# =====================================================
# INICIALIZAÇÃO
# =====================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Agente de Renovação - BNB Crediamigo...")
    print("🎯 Motor de análise com regras de negócio ativas")
    print("📱 Interface: http://127.0.0.1:8001/")
    print("📖 Documentação: http://127.0.0.1:8001/docs")
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)