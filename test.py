out = {"id": "123"}
table = {"id": "123", "date": "2022-11-15", "comment": None}
data = {"id": "123", "date": "2022-11-22"}

for t, d in zip(table.items(), data.items()):
    out |= dict([d])

print(out)