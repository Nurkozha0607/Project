import json

# Open and load JSON file
with open("sample-data.json") as f:
    data = json.load(f)

print("Interface Status")
print("=" * 80)
print(f"{'DN':50} {'Description':20} {'Speed':8} {'MTU':6}")
print("-" * 50, "-" * 20, "-" * 6, "-" * 6)

# Loop through interfaces
for item in data["imdata"]:
    attributes = item["l1PhysIf"]["attributes"]
    
    dn = attributes["dn"]
    descr = attributes["descr"]
    speed = attributes["speed"]
    mtu = attributes["mtu"]

    print(f"{dn:50} {descr:20} {speed:8} {mtu:6}")