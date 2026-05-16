import json, csv
team_map = {"Arizona Diamondbacks":"ARI","Atlanta Braves":"ATL","Baltimore Orioles":"BAL","Boston Red Sox":"BOS","Chicago Cubs":"CHC","Chicago White Sox":"CWS","Cincinnati Reds":"CIN","Cleveland Guardians":"CLE","Cleveland Indians":"CLE","Colorado Rockies":"COL","Detroit Tigers":"DET","Houston Astros":"HOU","Kansas City Royals":"KC","Los Angeles Angels":"LAA","Los Angeles Dodgers":"LAD","Miami Marlins":"MIA","Florida Marlins":"MIA","Milwaukee Brewers":"MIL","Minnesota Twins":"MIN","New York Mets":"NYM","New York Yankees":"NYY","Oakland Athletics":"OAK","Athletics":"ATH","Philadelphia Phillies":"PHI","Pittsburgh Pirates":"PIT","San Diego Padres":"SDP","San Francisco Giants":"SFG","Seattle Mariners":"SEA","St. Louis Cardinals":"STL","Tampa Bay Rays":"TBR","Texas Rangers":"TEX","Toronto Blue Jays":"TOR","Washington Nationals":"WSN"}
with open('download.json', 'r') as f:
    data = json.load(f)
with open('mlb-uniforms-2026.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    # Swapped Header: Away first, then Home
    writer.writerow(['Date', 'AwayTeam', 'AwayJersey', 'HomeTeam', 'HomeJersey'])
    for d_obj in data.get('dates', []):
        y, m, d = d_obj.get('date').split('-')
        fmt_date = f"{int(m)}/{int(d)}/{y[2:]}"
        for g in d_obj.get('games', []):
            h = team_map.get(g['teams']['home']['team']['name'].strip(), g['teams']['home']['team']['name'])
            a = team_map.get(g['teams']['away']['team']['name'].strip(), g['teams']['away']['team']['name'])
            # FLIPPED ORDER: Away (a) is columns 1-2, Home (h) is columns 3-4
            writer.writerow([fmt_date, a, '', h, ''])
