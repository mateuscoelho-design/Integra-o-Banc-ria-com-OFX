
from ofxparse import OfxParser
import psycopg2

# 1. Ler o arquivo OFX
with open("extrato.ofx", "rb") as arquivo:
    ofx = OfxParser.parse(arquivo)

transacoes = ofx.account.statement.transactions

# 2. Exibir todas as movimentações
print("EXTRATO BANCÁRIO")
print("=" * 60)

for t in transacoes:
    print(f"""
Data      : {t.date.strftime('%d/%m/%Y')}
Valor     : R$ {t.amount:.2f}
Descrição : {t.memo or 'Sem descrição'}
{"-" * 60}""")

# 3. Calcular os totais financeiros
entradas = sum(t.amount for t in transacoes if t.amount > 0)
saidas = sum(abs(t.amount) for t in transacoes if t.amount < 0)
saldo = entradas - saidas

print("\nRESUMO FINANCEIRO")
print(f"Quantidade de movimentações: {len(transacoes)}")
print(f"Total de entradas: R$ {entradas:.2f}")
print(f"Total de saídas: R$ {saidas:.2f}")
print(f"Saldo calculado: R$ {saldo:.2f}")

# 4. Classificar movimentações por valor
ordenadas = sorted(
    transacoes,
    key=lambda t: abs(t.amount),
    reverse=True
)

print("\nMOVIMENTAÇÕES DO MAIOR VALOR PARA O MENOR")
print("=" * 60)

for t in ordenadas:
    print(
        f"R$ {t.amount:>10.2f} | "
        f"{t.date.strftime('%d/%m/%Y')} | "
        f"{t.memo or 'Sem descrição'}"
    )

# 5. Exibir somente as despesas, da maior para a menor
despesas = sorted(
    [t for t in transacoes if t.amount < 0],
    key=lambda t: abs(t.amount),
    reverse=True
)

print("\nDESPESAS DO MAIOR VALOR PARA O MENOR")
print("=" * 60)

for t in despesas:
    print(
        f"R$ {abs(t.amount):>10.2f} | "
        f"{t.memo or 'Sem descrição'}"
    )

# 6. Identificar a maior despesa
if despesas:
    maior_despesa = despesas[0]

    print("\nMAIOR DESPESA")
    print(f"Descrição: {maior_despesa.memo or 'Sem descrição'}")
    print(f"Valor: R$ {abs(maior_despesa.amount):.2f}")

# 7. Conectar ao PostgreSQL (Neon)
conexao = psycopg2.connect(
    host="ep-patient-fog-aeynisgn-pooler.c-2.us-east-2.aws.neon.tech",
    port=5432,
    database="neondb",
    user="neondb_owner",
    password="npg_br2q6GfJtUpQ",
    sslmode="require"
)

cursor = conexao.cursor()

# 8. Inserir movimentações sem duplicar registros
inseridas = 0
duplicadas = 0

for t in transacoes:
    cursor.execute(
        """
        INSERT INTO movimentacoes
            (data_movimentacao, valor, descricao)
        VALUES (%s, %s, %s)
        ON CONFLICT (data_movimentacao, valor, descricao)
        DO NOTHING
        """,
        (
            t.date.date(),
            t.amount,
            t.memo or "Sem descrição"
        )
    )

    if cursor.rowcount == 1:
        inseridas += 1
    else:
        duplicadas += 1

# 9. Salvar os dados e encerrar a conexão
conexao.commit()

print("\nIMPORTAÇÃO PARA O POSTGRESQL")
print(f"Novas movimentações inseridas: {inseridas}")
print(f"Movimentações duplicadas ignoradas: {duplicadas}")

cursor.close()
conexao.close()

print("\nProcessamento concluído!")
