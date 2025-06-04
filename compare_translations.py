import json
import sys

print("Python:", sys.version)

with open("translations/en.json", "r", encoding="utf-8") as f:
    en_data = json.load(f)

with open("translations/pl.json", "r", encoding="utf-8") as f:
    pl_data = json.load(f)


def get_all_keys_with_values(data, prefix=""):
    keys_values = {}
    for k, v in data.items():
        current = prefix + "." + k if prefix else k
        if isinstance(v, dict):
            keys_values.update(get_all_keys_with_values(v, current))
        else:
            keys_values[current] = v
    return keys_values


en_keys_values = get_all_keys_with_values(en_data)
pl_keys_values = get_all_keys_with_values(pl_data)

print(f"EN klucze: {len(en_keys_values)}")
print(f"PL klucze: {len(pl_keys_values)}")

print("\nBrakujące w EN:")
for k in sorted(set(pl_keys_values.keys()) - set(en_keys_values.keys())):
    print(f"- {k}")

print("\nBrakujące w PL:")
for k in sorted(set(en_keys_values.keys()) - set(pl_keys_values.keys())):
    print(f"- {k}")

print("\nWartości różniące się:")
for k in sorted(set(en_keys_values.keys()) & set(pl_keys_values.keys())):
    if isinstance(en_keys_values[k], str) and isinstance(pl_keys_values[k], str):
        if "{" in en_keys_values[k] or "{" in pl_keys_values[k]:
            # Sprawdzanie różnic w formatowaniu
            en_placeholders = [p.strip("{}") for p in en_keys_values[k].split("{")[1:]]
            pl_placeholders = [p.strip("{}") for p in pl_keys_values[k].split("{")[1:]]

            en_placeholders = [p.split("}")[0] for p in en_placeholders]
            pl_placeholders = [p.split("}")[0] for p in pl_placeholders]

            if set(en_placeholders) != set(pl_placeholders):
                print(
                    f"- {k}: Różne placeholdery EN:{en_placeholders} vs PL:{pl_placeholders}"
                )
