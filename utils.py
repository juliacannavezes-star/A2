import pandas as pd
import numpy as np

# nomes comuns em português que podemos receber — normaliza para colunas padrão usadas no app
COLUMN_MAP = {
    'sexo': 'gender',
    'genero': 'gender',
    'gênero': 'gender',
    'gender': 'gender',
    'cor': 'race',
    'cor/raça': 'race',
    'cor_raca': 'race',
    'raca': 'race',
    'raça': 'race',
    'idade': 'age',
    'idade_anos': 'age',
    'faixa_etaria': 'age_group',
    'localidade': 'location',
    'estado': 'state',
    'municipio': 'city',
    'regiao': 'region',
    'tempo_de_atuacao': 'years_active',
    'tempo_atuacao': 'years_active',
    'anos_de_atuacao': 'years_active',
    'rendimento': 'income_bracket',
    'area': 'practice_area',
    'ramo': 'practice_area'
}

# padroniza colunas
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = {}
    for c in df.columns:
        key = c.strip().lower().replace(' ', '_')
        mapped = COLUMN_MAP.get(key, None)
        if mapped:
            new_cols[c] = mapped
        else:
            # tenta correspondências parciais
            if 'sexo' in key or 'genero' in key or 'gênero' in key:
                new_cols[c] = 'gender'
            elif 'idade' in key:
                new_cols[c] = 'age'
            elif 'cor' in key or 'raça' in key or 'raca' in key:
                new_cols[c] = 'race'
            elif 'estado' in key or 'uf' in key:
                new_cols[c] = 'state'
            elif 'regiao' in key or 'região' in key:
                new_cols[c] = 'region'
            elif 'municipio' in key or 'cidade' in key:
                new_cols[c] = 'city'
            elif 'tempo' in key or 'anos' in key:
                new_cols[c] = 'years_active'
            elif 'salario' in key or 'rendimento' in key or 'salário' in key:
                new_cols[c] = 'income_bracket'
            else:
                new_cols[c] = key  # mantém algo utilizável

    df = df.rename(columns=new_cols)
    return df

# cria algumas faixas etárias se só houver idade numérica
def ensure_age_groups(df: pd.DataFrame) -> pd.DataFrame:
    if 'age' in df.columns:
        # se já existe age_group, não sobrescreve
        if 'age_group' not in df.columns:
            bins = [0, 24, 44, 64, 120]
            labels = ['<=24', '25-44', '45-64', '65+']
            try:
                df['age'] = pd.to_numeric(df['age'], errors='coerce')
                df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, include_lowest=True)
            except Exception:
                df['age_group'] = pd.NA
    return df

# mapeia estados para macro-regiões brasileiras (simples)
STATE_TO_REGION = {
    # Norte
    'AC':'Norte','AM':'Norte','AP':'Norte','PA':'Norte','RO':'Norte','RR':'Norte','TO':'Norte',
    # Nordeste
    'AL':'Nordeste','BA':'Nordeste','CE':'Nordeste','MA':'Nordeste','PB':'Nordeste','PE':'Nordeste','PI':'Nordeste','RN':'Nordeste','SE':'Nordeste',
    # Centro-Oeste
    'DF':'Centro-Oeste','GO':'Centro-Oeste','MT':'Centro-Oeste','MS':'Centro-Oeste',
    # Sudeste
    'ES':'Sudeste','MG':'Sudeste','RJ':'Sudeste','SP':'Sudeste',
    # Sul
    'PR':'Sul','RS':'Sul','SC':'Sul'
}

def map_state_to_region(state_code):
    if pd.isna(state_code):
        return None
    s = str(state_code).strip().upper()
    # alguns dados têm nomes completos do estado — tenta extrair sigla
    if len(s) == 2:
        return STATE_TO_REGION.get(s, None)
    # tenta corresponder por prefixo
    for k,v in STATE_TO_REGION.items():
        if k in s or v.lower() in s.lower() or k.lower() in s.lower():
            return v
    return None

def ensure_region(df: pd.DataFrame) -> pd.DataFrame:
    if 'region' not in df.columns:
        # tenta a partir de 'state'
        if 'state' in df.columns:
            df['region'] = df['state'].apply(map_state_to_region)
        else:
            df['region'] = pd.NA
    else:
        # padroniza nomes
        df['region'] = df['region'].astype(str).str.capitalize().replace({'Nordeste': 'Nordeste', 'Norte': 'Norte'})
    return df

# resumo estatístico simples para relatórios
def make_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    rows.append({'metric':'Total registros', 'value': n})
    if 'gender' in df.columns:
        genders = df['gender'].fillna('Não informado').value_counts(normalize=True).mul(100).round(2).astype(str) + '%'
        for k,v in genders.items():
            rows.append({'metric': f'% gênero: {k}', 'value': v})
    if 'race' in df.columns:
        races = df['race'].fillna('Não informado').value_counts(normalize=True).mul(100).round(2).astype(str) + '%'
        for k,v in races.items():
            rows.append({'metric': f'% raça/cor: {k}', 'value': v})
    if 'age_group' in df.columns:
        ages = df['age_group'].fillna('Não informado').value_counts(normalize=True).mul(100).round(2).astype(str) + '%'
        for k,v in ages.items():
            rows.append({'metric': f'% faixa etária: {k}', 'value': v})
    if 'region' in df.columns:
        regs = df['region'].fillna('Não informado').value_counts(normalize=True).mul(100).round(2).astype(str) + '%'
        for k,v in regs.items():
            rows.append({'metric': f'% região: {k}', 'value': v})
    return pd.DataFrame(rows)
