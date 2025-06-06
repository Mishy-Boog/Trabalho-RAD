
import re

def validar_nome(nome):
    nome = nome.strip()
    return nome.replace(" ", "").isalpha() and 8 <= len(nome) <= 20

def validar_texto(texto):
    texto = texto.strip()
    return 8 <= len(texto) <= 20

def validar_senha(senha):
    return 8 <= len(senha) <= 20

def validar_login(login):
    login = login.strip()
    return 4 <= len(login) <= 20 and login.replace("_", "").isalnum()

def validar_3dig(numero):
    try:
        numero = int(numero)
        return 1 <= numero <= 999
    except Exception as e:
        print(f"Erro de validação: {e}")
        return False

def validar_email(email):
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
    return re.match(padrao, email) is not None

def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    return len(cpf) == 11


