import pandas as pd
import time

# pandas config
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 100)

# configs
seed = 19032025

# metrics
start_time = time.time()

df = pd.read_csv('data/lp3_proiecte_optiuni.csv')

# new atributes
df['grupa'] = df['Echipa'].apply(lambda x: x.split('-')[0])
df['domenii'] = df['Optiuni'].apply(lambda x: x.replace(' ', '').split(',') if not pd.isna(x) else [])
df['d1'] = df['domenii'].apply(lambda x: x[0].split('-')[0].strip() if len(x) > 0 else '')
df['d2'] = df['domenii'].apply(lambda x: x[1].split('-')[0].strip() if len(x) > 1 else '')
df['d3'] = df['domenii'].apply(lambda x: x[2].split('-')[0].strip() if len(x) > 2 else '')

# corectare domenii duplicat
df['d3'] = df.apply(lambda x: x['d3'] if x['d3'] not in (x['d1'], x['d2']) else '', axis=1)
df['d2'], df['d3'] = zip(*df.apply(lambda x: (x['d3'], '') if x['d1'] == x['d2'] else (x['d2'], x['d3']), axis=1))

# alocare runda 1
r1 = df[df['d1'] != ''].groupby(['grupa', 'd1'], group_keys=False)["Echipa"]. \
    apply(lambda x: x.sample(n=1, replace=False, random_state=seed)).reset_index()
r1_l = list(r1['Echipa'])
df['alocare'], df['runda'] = \
    zip(*df.apply(lambda x: (x['d1'], '1') if x['Echipa'] in r1_l else ('', ''), axis=1))

# corectie optiune 2, sa nu fie deja alocat domeniul in runda 1
def cor(x):
    alese = list(df[df['grupa'] == x['grupa']]['alocare'])
    if (x['d2'] in alese) and (x['d3'] not in alese):
        return x['d3'], ''
    elif (x['d2'] in alese) and (x['d3'] in alese):
        return '', ''
    else:
        return x['d2'], x['d3']


df['d2'], df['d3'] = zip(*df.apply(cor, axis=1))

# alocare runda 2
r2 = df[(df['d2'] != '') & (df['alocare'] == '')].groupby(['grupa', 'd2'], group_keys=False)["Echipa"]. \
    apply(lambda x: x.sample(n=1, replace=False, random_state=seed)).reset_index()
r2_l = list(r2['Echipa'])
df['alocare'], df['runda'] = \
    zip(*df.apply(lambda x: (x['d2'], '2') if x['Echipa'] in r2_l else (x['alocare'], x['runda']), axis=1))

# corectie optiune 3, sa nu fie deja alocat domeniul in runda 1 sau 2
df['d3'] = df.apply(lambda x: '' if x['d3'] in list(df[df['grupa'] == x['grupa']]['alocare']) else x['d3'], axis=1)

# alocare runda 3
r3 = df[(df['d3'] != '') & (df['alocare'] == '')].groupby(['grupa', 'd3'], group_keys=False)["Echipa"]. \
    apply(lambda x: x.sample(n=1, replace=False, random_state=seed))

if not r3.empty:
    r3_l = list(r3)
    df['alocare'], df['runda'] = \
        zip(*df.apply(lambda x: (x['d3'], '3') if x['Echipa'] in r3_l else (x['alocare'], x['runda']), axis=1))

# tema alocata
df['tema_proiect'] = df.apply(
    lambda x: next((t for t in x['domenii'] if (x['alocare'] != '') & (t.startswith(x['alocare']))),
                   'De alocat manual'), axis=1)

# salvare rezultate
print(df)
df.to_csv('data/alocari_teme.csv')

# metrics
execution_time = time.time() - start_time
print("Total execution time %s" % execution_time)
