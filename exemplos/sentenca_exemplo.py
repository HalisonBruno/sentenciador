"""Exemplo de sentenca.py no DSL Python.

Teste: python gerador_docx/gerador.py \\
    --input exemplos/sentenca_exemplo.py \\
    --output exemplos/sentenca_exemplo.docx

Note que NÃO emitimos cc(PROCESSO), ch('SENTENÇA'), ch('RELATÓRIO'),
ch('FUNDAMENTAÇÃO'), ch('DISPOSITIVO') nem o fecho com assinatura —
tudo isso é adicionado pelo gerador automaticamente.
"""

PROCESSO = "Processo nº 1000123-45.2025.8.26.0100"

RELATORIO = [
    bp(
        "Trata-se de ação de cobrança ajuizada por ALFA SERVIÇOS LTDA "
        "em face de BETA COMÉRCIO EIRELI. A autora sustenta ter prestado "
        "serviços de consultoria contratados em 03/2024, emitiu nota "
        "fiscal no valor de R$ 42.000,00, não quitada."
    ),
    bp(
        "Citada, BETA apresenta contestação. Alega que parte dos serviços "
        "não foi entregue conforme o escopo e pede a improcedência."
    ),
    bp("Houve réplica. Intimadas, as partes não requerem outras provas."),
    el(),
    bp("É o relatório."),
]

FUNDAMENTACAO = [
    sh("I. DO JULGAMENTO ANTECIPADO"),
    el(),
    bp(
        "A controvérsia é essencialmente documental, prescindindo de "
        "dilação probatória. Aplica-se o art. 355, I, do Código de "
        "Processo Civil."
    ),
    sh("II. DO MÉRITO"),
    el(),
    bp(
        "O contrato juntado às fls. 15/22 prevê, com clareza, o escopo "
        "dos serviços. Os e-mails e entregáveis constantes dos autos "
        "demonstram cumprimento integral das obrigações pela autora."
    ),
    bp("Dispõe o Código Civil:"),
    cp(
        "Art. 476. Nos contratos bilaterais, nenhum dos contratantes, "
        "antes de cumprida a sua obrigação, pode exigir o implemento da "
        "do outro."
    ),
    bp(
        "A ré, porém, sequer indicou com precisão qual entregável estaria "
        "faltando, limitando-se a alegação genérica, o que não se admite."
    ),
]

DISPOSITIVO = [
    bp(
        "Ante o exposto, JULGO PROCEDENTE o pedido, com resolução de "
        "mérito (CPC, art. 487, I), para condenar a ré ao pagamento de "
        "R$ 42.000,00, corrigidos pelo IPCA desde o vencimento e "
        "acrescidos de juros de 1% ao mês a partir da citação. Condeno "
        "ainda a ré ao pagamento das custas processuais e de honorários "
        "advocatícios de sucumbência, fixados em 10% sobre o valor "
        "atualizado da condenação (CPC, art. 85, § 2º). Publique-se. "
        "Registre-se. Intime-se."
    ),
]
