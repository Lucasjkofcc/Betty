import ast
import operator
OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}
def calcular(expressao):
    def avaliar(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in OPERADORES:
            esquerda = avaliar(node.left)
            direita = avaliar(node.right)
            return OPERADORES[type(node.op)](esquerda, direita)

        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERADORES:
            return OPERADORES[type(node.op)](avaliar(node.operand))

        raise ValueError("Expressão inválida.")

    arvore = ast.parse(expressao, mode="eval")
    return avaliar(arvore.body)
