class Utility:
    def __init__(self,utility_id,name,code):
        self.utility_id=utility_id
        self.name=name
        self.code=code

    def __repr__(self):
        return f"<Utility {self.code}: {self.name}>"

ecg = Utility(1,"Electricity Company of Ghana","ECG")
print(ecg)

import pandas as pd
df = pd.read_csv('utilities.csv')

utility_list=[]

for _,row in df.iterrows():
     u = Utility(
        utility_id=int(row['Utility ID']),
        name=row['Name'],
        code=row['Code'],
    )
     utility_list.append(u)

print(f"Built {len(utility_list)} Utility objects")
for u in utility_list[:3]:
    print(" ", u)

utilities = {}  
for _, row in df.iterrows():
    u = Utility(
        utility_id=int(row['Utility ID']),
        name=row['Name'],
        code=row['Code'],
    )
    utilities[u.utility_id] = u

print(utilities[3])          
print(utilities.get(999))       

class Line:
    def __init__(self, line_id, utility_id, source_substation_id, destination_substation_id):
        self.line_id = line_id
        self.utility_id = utility_id
        self.source_substation_id = source_substation_id
        self.destination_substation_id = destination_substation_id

    def __repr__(self):
        return f"<Line {self.line_id}: substation {self.source_substation_id} -> substation {self.destination_substation_id}>"

lines_df = pd.read_csv('lines.csv')

lines = []
for _, row in lines_df.iterrows():
    line = Line(
        line_id=int(row['Line ID']),
        utility_id=int(row['Utility ID']),
        source_substation_id=int(row['Source Substation ID']),
        destination_substation_id=int(row['Destination Substation ID']),
    )
    lines.append(line)

print(lines[0])

class Substation:
    def __init__(self, substation_id, short_name, region):
        self.substation_id = substation_id
        self.short_name = short_name
        self.region = region

    def __repr__(self):
        return f"<Substation {self.short_name} ({self.region})>"


class Line:
    def __init__(self, line_id, source_substation_id, destination_substation_id):
        self.line_id = line_id
        self.source_substation_id = source_substation_id
        self.destination_substation_id = destination_substation_id
        
        self.source_substation = None
        self.destination_substation = None

    def __repr__(self):
        src = self.source_substation.short_name if self.source_substation else "UNKNOWN"
        dst = self.destination_substation.short_name if self.destination_substation else "UNKNOWN"
        return f"<Line {self.line_id}: {src} -> {dst}>"


sub_df = pd.read_csv('substations.csv')
substations = {}
for _, row in sub_df.iterrows():
    s = Substation(int(row['Substation ID']), row['Short Name'], row['Region'])
    substations[s.substation_id] = s


first_row = lines_df.iloc[0]
line = Line(
    line_id=int(first_row['Line ID']),
    source_substation_id=int(first_row['Source Substation ID']),
    destination_substation_id=int(first_row['Destination Substation ID']),
)

print("Before resolving:", line)


line.source_substation = substations.get(line.source_substation_id)
line.destination_substation = substations.get(line.destination_substation_id)

print("After resolving: ", line)

if line.source_substation:
    print("Now I can reach the region directly:", line.source_substation.region)
else:
    print("Source substation is an orphan reference, no region available")

class Line:
    def __init__(self, line_id, source_substation_id, destination_substation_id):
        self.line_id = line_id
        self.source_substation_id = source_substation_id
        self.destination_substation_id = destination_substation_id
        self.source_substation = None
        self.destination_substation = None

    def is_orphan(self):
        return self.source_substation is None or self.destination_substation is None

    def __repr__(self):
        src = self.source_substation.short_name if self.source_substation else "UNKNOWN"
        dst = self.destination_substation.short_name if self.destination_substation else "UNKNOWN"
        return f"<Line {self.line_id}: {src} -> {dst}>"


lines = []
orphans = []

for _, row in lines_df.iterrows():
    line = Line(
        line_id=int(row['Line ID']),
        source_substation_id=int(row['Source Substation ID']),
        destination_substation_id=int(row['Destination Substation ID']),
    )
    line.source_substation = substations.get(line.source_substation_id)
    line.destination_substation = substations.get(line.destination_substation_id)

    if line.is_orphan():
        orphans.append(line.line_id)

    lines.append(line)

print(f"Built {len(lines)} Line objects")
print(f"Orphans found: {len(orphans)}")
print(lines[0])
print(lines[10])

class GridDataRepository:

    def __init__(self, substations_csv, lines_csv):
        self.substations_csv = substations_csv
        self.lines_csv = lines_csv
        self.substations = {}
        self.lines = []

    def load(self):
        self._load_substations()
        self._load_lines()
        return self  

    def _load_substations(self):
        df = pd.read_csv(self.substations_csv)
        for _, row in df.iterrows():
            s = Substation(int(row['Substation ID']), row['Short Name'], row['Region'])
            self.substations[s.substation_id] = s

    def _load_lines(self):
        df = pd.read_csv(self.lines_csv)
        for _, row in df.iterrows():
            line = Line(
                line_id=int(row['Line ID']),
                source_substation_id=int(row['Source Substation ID']),
                destination_substation_id=int(row['Destination Substation ID']),
            )
            line.source_substation = self.substations.get(line.source_substation_id)
            line.destination_substation = self.substations.get(line.destination_substation_id)
            self.lines.append(line)

    def orphan_count(self):
        return sum(1 for line in self.lines if line.is_orphan())


repo = GridDataRepository('substations.csv', 'lines.csv').load()
print(f"Substations: {len(repo.substations)}")
print(f"Lines: {len(repo.lines)}")
print(f"Orphans: {repo.orphan_count()}")

def to_dataframe(repo):
    records = []
    for line in repo.lines:
        records.append({
            'Line ID': line.line_id,
            'Source Substation': line.source_substation.short_name if line.source_substation else None,
            'Source Region': line.source_substation.region if line.source_substation else None,
            'Destination Substation': line.destination_substation.short_name if line.destination_substation else None,
            'Is Orphan': line.is_orphan(),
        })
    return pd.DataFrame(records)

flat = to_dataframe(repo)
print(flat.head(3))
flat.to_csv('integrated_grid_data.csv', index=False)

from dataclasses import dataclass


class SubstationManual:
    def __init__(self, substation_id, short_name, region):
        self.substation_id = substation_id
        self.short_name = short_name
        self.region = region
    def __repr__(self):
        return f"<Substation {self.short_name} ({self.region})>"

@dataclass
class Substation:
    substation_id: int
    short_name: str
    region: str
    def __repr__(self):
        return f"<Substation {self.short_name} ({self.region})>"

a = SubstationManual(1, "Achimota", "Greater Accra")
b = Substation(1, "Achimota", "Greater Accra")
print(a)
print(b)
print("Identical behavior:", str(a) == str(b))