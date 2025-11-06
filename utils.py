# utils.py
import os
import io
import pandas as pd
import pdfplumber

def read_primary_dataframe(data_dir="data"):
    """
    Procura por CSV/Excel no diretório data/.
    Se não encontrar, tenta extrair do PDF usando pdfplumber.
    Retorna um DataFrame padronizado com as colunas esperadas:
      - sexo (ou genero)
      - cor_raca (ou raça/cor)
      - idade
      - uf (sigla do estado) ou municipio
      - regiao (Norte, Nordeste, Sudeste, Sul, Centro-Oeste)
      - tempo_atuacao_anos (opcional)
    """
    # 1) procurar CSV/Excel
    for fname in os.listdir(data_dir):
        lower = fname.lower()
        path = os.path.join(data_dir, fname)
        if lower.endswith(".csv"):
            df = pd.read_csv(path, dtype=str)
            return standardize_columns(df)
        if lower.endswith((".xls", ".xlsx")):
            df = pd.read_excel(path, dtype=str)
            return standardize_columns(df)

    # 2) procurar PDF e tentar extrair tabelas
    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            path = os.path.join(data_dir, fname)
            try:
                tables = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        try:
                            tbl = page.extract_table()
                            if tbl:
                                # converter a tabela para DataFrame
                                df_page = pd.DataFrame(tbl[1:], columns=tbl[0])
                                tables.append(df_page)
                        except Exception:
                            continue
                if tables:
                    df = pd.concat(tables, ignore_index=True)
                    return standardize_columns(df)
            except Exception as e:
                raise RuntimeError(f"Erro ao ler PDF: {e}")

    raise FileNotFoundError("Nenhum arquivo de dados encontrado em data/ (CSV, Excel ou PDF).")

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza nomes de colunas mais comuns para os campos do app.
    Converte tipos e cria colunas auxiliares.
    """
    df = df.copy()
    # tornar colunas minúsculas sem acentuação básica
    df.columns = [c.strip().lower() for c in df.columns]

    # mapeamentos comuns (adicione conforme necessário)
    col_map = {}
    for c in df.columns:
        if "sexo" in c or "genero" in c or "gênero" in c:
            col_map[c] = "sexo"
        if "idade" in c:
            col_map[c] = "idade"
        if "raça" in c or "raca" in c or "cor" in c:
            col_map[c] = "cor_raca"
        if c in ("uf", "estado", "sigla"):
            col_map[c] = "uf"
        if "municipio" in c or "município" in c:
            col_map[c] = "municipio"
        if "tempo" in c and "atu" in c:
            col_map[c] = "tempo_atuacao_anos"

    df = df.rename(columns=col_map)

    # garantir colunas mínimas
    if "regiao" not in df.columns and "uf" in df.columns:
        df["regiao"] = df["uf"].map(uf_para_regiao())

    # conversões
    if "idade" in df.columns:
        df["idade"] = pd.to_numeric(df["idade"], errors="coerce")

    # criar faixas etárias
    if "idade" in df.columns:
        bins = [0, 24, 34, 44, 54, 64, 200]
        labels = ["<=24","25-34","35-44","45-54","55-64","65+"]
        df["faixa_etaria"] = pd.cut(df["idade"], bins=bins, labels=labels, right=True)

    return df

def uf_para_regiao():
    return {
        # Sudeste
        "SP":"Sudeste","RJ":"Sudeste","MG":"Sudeste","ES":"Sudeste",
        # Sul
        "PR":"Sul","RS":"Sul","SC":"Sul",
        # Nordeste
        "BA":"Nordeste","PE":"Nordeste","CE":"Nordeste","RN":"Nordeste","PB":"Nordeste",
        "AL":"Nordeste","SE":"Nordeste","MA":"Nordeste","PI":"Nordeste",
        # Norte
        "AM":"Norte","PA":"Norte","AP":"Norte","RO":"Norte","RR":"Norte","TO":"Norte","AC":"Norte",
        # Centro-Oeste
        "DF":"Centro-Oeste","GO":"Centro-Oeste","MT":"Centro-Oeste","MS":"Centro-Oeste"
    }
