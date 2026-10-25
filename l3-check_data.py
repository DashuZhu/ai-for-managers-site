"""Проверка учебных CSV без облака. Python 3, только стандартная библиотека."""
import csv, json
from pathlib import Path
from decimal import Decimal
ROOT = Path(__file__).resolve().parent
with (ROOT / '05-Заявки.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f, delimiter=';'))
seen, clean, journal = {}, [], []
for line, row in enumerate(rows, 2):
    key = row['id']
    if key in seen:
        if row != seen[key]:
            raise ValueError(f'Конфликт версий id {key}, строка {line}; нужно решение человека')
        journal.append({'line': line, 'id': key, 'reason': 'точный дубль; сохранена первая строка'})
        continue
    seen[key] = row
    clean.append(row)
known = [r for r in clean if r['hours'].strip()]
def total(items):
    return sum((Decimal(r['hours']) for r in items if r['hours'].strip()), Decimal(0))
report = dict(rows_raw=len(rows), unique_ids=len(seen), excluded=journal,
              missing_hours=[r['id'] for r in clean if not r['hours'].strip()],
              known_hours_unique=str(total(clean)), naive_raw_sum=str(total(rows)),
              closed_hours=str(total(r for r in known if r['status']=='закрыта')),
              open_known_hours=str(total(r for r in known if r['status']=='открыта')))
with (ROOT / '06-Инвестиционный-пример.csv').open(encoding='utf-8-sig', newline='') as f:
    flows = [(int(r['period_year']), Decimal(r['cashflow_rub'])) for r in csv.DictReader(f, delimiter=';')]
def npv(rate):
    return sum(v / (Decimal(1) + rate)**t for t, v in flows)
rate = Decimal('0.12')
low, high = Decimal(0), Decimal(1)
assert npv(low) > 0 > npv(high), 'Учебный интервал IRR не содержит корень'
for _ in range(100):
    mid = (low+high)/2
    if npv(mid) > 0: low=mid
    else: high=mid
report['npv_12_percent'] = str(npv(rate).quantize(Decimal('0.01')))
report['irr'] = str(((low+high)/2).quantize(Decimal('0.00000001')))
# Проверочные числа заданы отдельно от алгоритма. Несовпадение останавливает выдачу образца.
assert (len(rows), len(clean), total(clean), report['closed_hours'], report['open_known_hours']) == (12,11,Decimal(24),'13','11')
assert report['missing_hours'] == ['T008'] and len(journal)==1 and journal[0]['id']=='T007'
assert report['npv_12_percent']=='151387.93' and report['irr']=='0.19300974'
with (ROOT/'Образец-очищенные-заявки.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0].keys(),delimiter=';');writer.writeheader();writer.writerows(clean)
(ROOT/'Журнал-проверки.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
