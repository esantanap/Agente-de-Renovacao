# app/analisador.py
from typing import Dict, List, Tuple, Any
from datetime import datetime
from .database import db

class AnalisadorRenovacao:
    """
    Motor de análise para renovação de crédito baseado nas regras de negócio
    """
    
    def __init__(self):
        # Critérios de negócio
        self.LIMITE_CICLOS_CREDITO = 5
        self.LIMITE_INADIMPLENCIA_DIAS = 30
        self.PORTE_ESPERADO = "Crediamigo"
        self.TIPO_CADASTRO_ESPERADO = "Completo"
        self.LIMITE_CADIN = 0.0
        self.LIMITE_RESTRICOES_FINANCEIRAS = 0.0
    
    def analisar_cliente(self, cpf: str, pergunta: str = "") -> Dict[str, Any]:
        """
        Análise completa do cliente para renovação
        """
        try:
            # 1. Buscar dados do cliente
            cliente = db.buscar_cliente(cpf)
            
            if not cliente:
                return {
                    "erro": True,
                    "mensagem": f"Cliente com CPF {cpf} não encontrado na base de dados.",
                    "cpf": cpf,
                    "decisao": "Não Encontrado",
                    "justificativa": "Cliente não localizado no sistema.",
                    "detalhes": {}
                }
            
            # 2. Analisar critérios impeditivos
            impedimentos = self._verificar_impedimentos(cliente)
            
            # 3. Analisar critérios operacionais
            ajustes_necessarios = self._verificar_ajustes_operacionais(cliente)
            
            # 4. Determinar decisão final
            decisao, justificativa = self._determinar_decisao(impedimentos, ajustes_necessarios)
            
            # 5. Gerar resposta contextualizada
            resposta_contextual = self._gerar_resposta_contextual(pergunta, decisao, cliente, impedimentos, ajustes_necessarios)
            
            return {
                "erro": False,
                "cpf": cpf,
                "decisao": decisao,
                "justificativa": resposta_contextual,
                "detalhes": {
                    "nome": cliente.get("nome", "Não informado"),
                    "unidade_cadastro": cliente.get("unidade_cadastro", "Não informado"),
                    "impedimentos": impedimentos,
                    "ajustes": ajustes_necessarios,
                    "dados_cliente": self._resumir_dados_cliente(cliente),
                    "data_analise": datetime.now().isoformat(),
                    "criterios_aplicados": self._obter_criterios_aplicados()
                }
            }
            
        except Exception as e:
            return {
                "erro": True,
                "mensagem": f"Erro interno na análise: {str(e)}",
                "cpf": cpf,
                "decisao": "Erro",
                "justificativa": "Ocorreu um erro durante a análise. Tente novamente.",
                "detalhes": {}
            }
    
    def _verificar_impedimentos(self, cliente: Dict[str, Any]) -> List[str]:
        """
        Verificar critérios impeditivos (críticos)
        """
        impedimentos = []
        
        # 1. Restrições RFB
        if cliente.get("rfb_restricao", False):
            impedimentos.append("Restrição na Receita Federal (RFB)")
        
        # 2. Restrições BNB
        if cliente.get("bnb_restricao", False):
            impedimentos.append("Restrição interna do BNB")
        
        # 3. Débitos CADIN
        cadin_valor = cliente.get("cadin_valor", 0)
        if cadin_valor > self.LIMITE_CADIN:
            impedimentos.append(f"Débitos no CADIN: R\$ {cadin_valor:,.2f}")
        
        # 4. Quantidade excessiva de ciclos
        ciclos = cliente.get("quantidade_ciclos_credito", 0)
        if ciclos > self.LIMITE_CICLOS_CREDITO:
            impedimentos.append(f"Excesso de ciclos de crédito: {ciclos} (limite: {self.LIMITE_CICLOS_CREDITO})")
        
        # 5. Histórico de inadimplência crítico
        inadimplencia_dias = cliente.get("historico_inadimplencia_dias", 0)
        if inadimplencia_dias > self.LIMITE_INADIMPLENCIA_DIAS:
            impedimentos.append(f"Histórico de inadimplência crítico: {inadimplencia_dias} dias (limite: {self.LIMITE_INADIMPLENCIA_DIAS})")
        
        return impedimentos
    
    def _verificar_ajustes_operacionais(self, cliente: Dict[str, Any]) -> List[str]:
        """
        Verificar critérios operacionais (ajustes necessários)
        """
        ajustes = []
        
        # 1. Situação cadastral
        situacao = cliente.get("situacao_cadastral", "").strip()
        if situacao.lower() != "ativo":
            ajustes.append(f"Regularizar situação cadastral (atual: {situacao})")
        
        # 2. Porte incorreto
        porte = cliente.get("porte", "").strip()
        if porte != self.PORTE_ESPERADO:
            ajustes.append(f"Ajustar porte do cliente (atual: {porte}, esperado: {self.PORTE_ESPERADO})")
        
        # 3. Tipo de cadastro incorreto
        tipo_cadastro = cliente.get("tipo_cadastro", "").strip()
        if tipo_cadastro != self.TIPO_CADASTRO_ESPERADO:
            ajustes.append(f"Completar cadastro (atual: {tipo_cadastro}, esperado: {self.TIPO_CADASTRO_ESPERADO})")
        
        # 4. Restrições financeiras não impeditivas
        serasa_valor = cliente.get("serasa_valor", 0)
        if serasa_valor > self.LIMITE_RESTRICOES_FINANCEIRAS:
            ajustes.append(f"Regularizar restrições Serasa: R\$ {serasa_valor:,.2f}")
        
        spc_valor = cliente.get("spc_valor", 0)
        if spc_valor > self.LIMITE_RESTRICOES_FINANCEIRAS:
            ajustes.append(f"Regularizar restrições SPC: R\$ {spc_valor:,.2f}")
        
        return ajustes
    
    def _determinar_decisao(self, impedimentos: List[str], ajustes: List[str]) -> Tuple[str, str]:
        """
        Determinar decisão final baseada nos impedimentos e ajustes
        """
        if impedimentos:
            return "Impedida", f"Renovação impedida devido a {len(impedimentos)} critério(s) crítico(s) não atendido(s)."
        
        elif ajustes:
            return "Ressalvas", f"Renovação possível mediante {len(ajustes)} ajuste(s) operacional(is)."
        
        else:
            return "Aprovável", "Cliente atende todos os critérios para renovação sem restrições."
    
    def _gerar_resposta_contextual(self, pergunta: str, decisao: str, cliente: Dict, impedimentos: List[str], ajustes: List[str]) -> str:
        """
        Gerar resposta contextualizada baseada na pergunta do usuário
        """
        nome = cliente.get("nome", "Cliente")
        
        # Resposta base
        if decisao == "Aprovável":
            resposta = f"✅ **{nome}** está **APROVÁVEL** para renovação de crédito.\n\n"
            resposta += "O cliente atende todos os critérios impeditivos e operacionais estabelecidos."
        
        elif decisao == "Ressalvas":
            resposta = f"⚠️ **{nome}** pode renovar **COM RESSALVAS**.\n\n"
            resposta += "**Ajustes necessários:**\n"
            for i, ajuste in enumerate(ajustes, 1):
                resposta += f"{i}. {ajuste}\n"
        
        elif decisao == "Impedida":
            resposta = f"❌ **{nome}** está **IMPEDIDO** de renovar.\n\n"
            resposta += "**Impedimentos identificados:**\n"
            for i, impedimento in enumerate(impedimentos, 1):
                resposta += f"{i}. {impedimento}\n"
        
        # Adicionar contexto específico baseado na pergunta
        pergunta_lower = pergunta.lower()
        
        if "por que" in pergunta_lower or "motivo" in pergunta_lower:
            resposta += f"\n**Justificativa técnica:** A análise foi baseada nos critérios de negócio estabelecidos para o programa Crediamigo."
        
        if "como resolver" in pergunta_lower or "solução" in pergunta_lower:
            if ajustes:
                resposta += f"\n**Como proceder:** Execute os ajustes listados acima e realize nova análise."
            elif impedimentos:
                resposta += f"\n**Como proceder:** Os impedimentos identificados requerem resolução antes de nova tentativa de renovação."
        
        if "prazo" in pergunta_lower or "quando" in pergunta_lower:
            resposta += f"\n**Prazo:** Após correções, o cliente pode ser reanalisado imediatamente."
        
        return resposta
    
    def _resumir_dados_cliente(self, cliente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resumir dados principais do cliente
        """
        return {
            "ciclos_credito": cliente.get("quantidade_ciclos_credito", 0),
            "inadimplencia_dias": cliente.get("historico_inadimplencia_dias", 0),
            "porte": cliente.get("porte", ""),
            "tipo_cadastro": cliente.get("tipo_cadastro", ""),
            "situacao_cadastral": cliente.get("situacao_cadastral", ""),
            "unidade": cliente.get("unidade_cadastro", ""),
            "restricoes": {
                "rfb": cliente.get("rfb_restricao", False),
                "bnb": cliente.get("bnb_restricao", False),
                "cadin": cliente.get("cadin_valor", 0),
                "serasa": cliente.get("serasa_valor", 0),
                "spc": cliente.get("spc_valor", 0)
            }
        }
    
    def _obter_criterios_aplicados(self) -> Dict[str, Any]:
        """
        Retornar critérios de negócio aplicados na análise
        """
        return {
            "impeditivos": {
                "limite_ciclos": self.LIMITE_CICLOS_CREDITO,
                "limite_inadimplencia_dias": self.LIMITE_INADIMPLENCIA_DIAS,
                "restricoes_rfb": "Não permitido",
                "restricoes_bnb": "Não permitido",
                "debitos_cadin": "Não permitido"
            },
            "operacionais": {
                "porte_esperado": self.PORTE_ESPERADO,
                "tipo_cadastro_esperado": self.TIPO_CADASTRO_ESPERADO,
                "situacao_esperada": "Ativo",
                "restricoes_financeiras": "Verificadas"
            }
        }

# Instância global
analisador = AnalisadorRenovacao()
