def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()
def escrever_arquivo(caminho, conteudo): # Perigoso
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)