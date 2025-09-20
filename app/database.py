# app/database.py
import pyodbc
from typing import Optional, Dict, Any
import os
from datetime import datetime

class DatabaseConnection:
    def __init__(self):
        # Configurações do banco - ajuste conforme seu ambiente
        self.connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"  # Ajuste conforme seu servidor
            "DATABASE=RenovacaoCredito;"
            "Trusted_Connection=yes;"
        )
        
    def get_connection(self):
        """Criar conexão com o banco"""
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            print(f"Erro ao conectar com banco: {e}")
            raise
    
    def buscar_cliente(self, cpf: str) -> Optional[Dict[str, Any]]:
        """Buscar dados do cliente no banco"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                id, cpf, nome, situacao_cadastral, rfb_restricao, bnb_restricao,
                cadin_valor, quantidade_ciclos_credito, historico_inadimplencia_dias,
                unidade_cadastro, porte, tipo_cadastro, serasa_valor, spc_valor,
                data_ultima_analise
            FROM clientes 
            WHERE cpf = ?
            """
            
            cursor.execute(query, cpf)
            row = cursor.fetchone()
            
            if row:
                # Converter resultado em dicionário
                columns = [desc[0] for desc in cursor.description]
                cliente_data = dict(zip(columns, row))
                
                # Converter valores para tipos apropriados
                cliente_data['rfb_restricao'] = str(cliente_data['rfb_restricao']).strip() == '1'
                cliente_data['bnb_restricao'] = str(cliente_data['bnb_restricao']).strip() == '1'
                cliente_data['cadin_valor'] = self._safe_float_conversion(cliente_data['cadin_valor'])
                cliente_data['serasa_valor'] = self._safe_float_conversion(cliente_data['serasa_valor'])
                cliente_data['spc_valor'] = self._safe_float_conversion(cliente_data['spc_valor'])
                cliente_data['quantidade_ciclos_credito'] = self._safe_int_conversion(cliente_data['quantidade_ciclos_credito'])
                cliente_data['historico_inadimplencia_dias'] = self._safe_int_conversion(cliente_data['historico_inadimplencia_dias'])
                
                return cliente_data
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar cliente {cpf}: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_connection(self) -> bool:
        """Testar conexão com o banco"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clientes")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Conexão OK - {count} clientes na base")
            return True
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            return False

    def _safe_float_conversion(self, value) -> float:
        """Converter valor para float de forma segura, tratando NULLs e strings 'NULL'"""
        if value is None:
            return 0.0
        
        # Converter para string e verificar se é 'NULL' ou vazio
        str_value = str(value).strip().upper()
        if str_value in ['NULL', 'NONE', '']:
            return 0.0
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int_conversion(self, value) -> int:
        """Converter valor para int de forma segura, tratando NULLs e strings 'NULL'"""
        if value is None:
            return 0
        
        # Converter para string e verificar se é 'NULL' ou vazio
        str_value = str(value).strip().upper()
        if str_value in ['NULL', 'NONE', '']:
            return 0
        
        try:
            # Try to convert to float first, then to int to handle float strings
            return int(float(value))
        except (ValueError, TypeError):
            return 0

# Instância global
db = DatabaseConnection()