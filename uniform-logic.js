const mlbData = {
    "ARI": {
        names: [{ stop: 2026, name: "Arizona Diamondbacks" }],
        colors: [
            { stop: 2015, color: "#A6192E" },
            { stop: 2019, color: "#545859" },
            { stop: 2023, color: "#D9C89D" },
            { stop: 2026, color: "#2CCCD3" }
        ]
    },
    "ATL": {
        names: [{ stop: 2026, name: "Atlanta Braves" }],
        colors: [{ stop: 2017, color: "#002855" }, { stop: 2026, color: "#0C2340" }]
    },
    "BAL": {
        names: [{ stop: 2026, name: "Baltimore Orioles" }],
        colors: [{ stop: 2026, color: "#FC4C02" }]
    },
    "BOS": {
        names: [{ stop: 2026, name: "Boston Red Sox" }],
        colors: [{ stop: 2026, color: "#C8102E" }]
    },
    "CHC": {
        names: [{ stop: 2026, name: "Chicago Cubs" }],
        colors: [{ stop: 2026, color: "#002F6C" }]
    },
    "CHW": {
        names: [{ stop: 2026, name: "Chicago White Sox" }],
        colors: [{ stop: 2026, color: "#8D9093" }]
    },
    "CIN": {
        names: [{ stop: 2026, name: "Cincinnati Reds" }],
        colors: [{ stop: 2012, color: "#D50032" }, { stop: 2026, color: "#BA0C2F" }]
    },
    "CLE": {
        names: [{ stop: 2021, name: "Cleveland Indians" }, { stop: 2026, name: "Cleveland Guardians" }],
        colors: [{ stop: 2026, color: "#D50032" }]
    },
    "COL": {
        names: [{ stop: 2026, name: "Colorado Rockies" }],
        colors: [{ stop: 2016, color: "#24125F" }, { stop: 2026, color: "#330072" }]
    },
    "DET": {
        names: [{ stop: 2026, name: "Detroit Tigers" }],
        colors: [{ stop: 2026, color: "#0C2340" }]
    },
    "HOU": {
        names: [{ stop: 2026, name: "Houston Astros" }],
        colors: [{ stop: 2012, color: "#9A3324" }, { stop: 2026, color: "#CF4520" }]
    },
    "KCR": {
        names: [{ stop: 2026, name: "Kansas City Royals" }],
        colors: [{ stop: 2025, color: "#002D72" }, { stop: 2026, color: "#0032A0" }]
    },
    "LAA": {
        names: [{ stop: 2015, name: "L.A. Angels of Anaheim" }, { stop: 2026, name: "Los Angeles Angels" }],
        colors: [{ stop: 2011, color: "#89764B" }, { stop: 2026, color: "#BA0C2F" }]
    },
    "LAD": {
        names: [{ stop: 2026, name: "Los Angeles Dodgers" }],
        colors: [{ stop: 2026, color: "#002F6C" }]
    },
    "MIA": {
        names: [{ stop: 2011, name: "Florida Marlins" }, { stop: 2026, name: "Miami Marlins" }],
        colors: [{ stop: 2011, color: "#009CA6" }, { stop: 2018, color: "#F9423A" }, { stop: 2026, color: "#00A3E0" }]
    },
    "MIL": {
        names: [{ stop: 2026, name: "Milwaukee Brewers" }],
        colors: [{ stop: 2015, color: "#89734C" }, { stop: 2019, color: "#FED141" }, { stop: 2026, color: "#13294B" }]
    },
    "MIN": {
        names: [{ stop: 2026, name: "Minnesota Twins" }],
        colors: [{ stop: 2014, color: "#BA0C2F" }, { stop: 2022, color: "#B9975B" }, { stop: 2026, color: "#0C2340" }]
    },
    "NYM": {
        names: [{ stop: 2026, name: "New York Mets" }],
        colors: [{ stop: 2026, color: "#002D72" }]
    },
    "NYY": {
        names: [{ stop: 2026, name: "New York Yankees" }],
        colors: [{ stop: 2026, color: "#0C2340" }]
    },
    "OAK": {
        names: [{ stop: 2024, name: "Oakland Athletics" }, { stop: 2026, name: "Athletics" }],
        colors: [{ stop: 2026, color: "#024638" }]
    },
    "PHI": {
        names: [{ stop: 2026, name: "Philadelphia Phillies" }],
        colors: [{ stop: 2026, color: "#BA0C2F" }]
    },
    "PIT": {
        names: [{ stop: 2026, name: "Pittsburgh Pirates" }],
        colors: [{ stop: 2026, color: "#FFC72C" }]
    },
    "SDP": {
        names: [{ stop: 2026, name: "San Diego Padres" }],
        colors: [{ stop: 2013, color: "#B3A369" }, { stop: 2015, color: "#041E42" }, { stop: 2016, color: "#FFC72C" }, { stop: 2019, color: "#041E42" }, { stop: 2026, color: "#3E342F" }]
    },
    "SEA": {
        names: [{ stop: 2026, name: "Seattle Mariners" }],
        colors: [{ stop: 2026, color: "#00685E" }]
    },
    "SFG": {
        names: [{ stop: 2026, name: "San Francisco Giants" }],
        colors: [{ stop: 2026, color: "#FA4616" }]
    },
    "STL": {
        names: [{ stop: 2026, name: "St. Louis Cardinals" }],
        colors: [{ stop: 2026, color: "#BA0C2F" }]
    },
    "TBR": {
        names: [{ stop: 2026, name: "Tampa Bay Rays" }],
        colors: [{ stop: 2026, color: "#69B3E7" }]
    },
    "TEX": {
        names: [{ stop: 2026, name: "Texas Rangers" }],
        colors: [{ stop: 2019, color: "#BA0C2F" }, { stop: 2026, color: "#002D72" }]
    },
    "TOR": {
        names: [{ stop: 2026, name: "Toronto Blue Jays" }],
        colors: [{ stop: 2011, color: "#605E5C" }, { stop: 2026, color: "#003DA5" }]
    },
    "WSN": {
        names: [{ stop: 2026, name: "Washington Nationals" }],
        colors: [{ stop: 2026, color: "#BA0C2F" }]
    }
};

/** UI CONTROLLERS **/

function updateTeamDropdown() {
    const year = parseInt(document.getElementById('year-select').value);
    const teamSelect = document.getElementById('uni-team-select');
    const currentVal = teamSelect.value || "ARI";
    
    teamSelect.innerHTML = "";
    Object.keys(mlbData).forEach(code => {
        const data = mlbData[code];
        const nameEntry = data.names.find(n => year <= n.stop) || data.names[data.names.length - 1];
        
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = nameEntry.name;
        if (code === currentVal) opt.selected = true;
        teamSelect.appendChild(opt);
    });
}

function getTeamColor(teamCode, year) {
    const data = mlbData[teamCode];
    if (!data) return "#000000";
    const colorEntry = data.colors.find(c => parseInt(year) <= c.stop);
    return colorEntry ? colorEntry.color : data.colors[data.colors.length - 1].color;
}

async function loadFullYearCalendar() {
    const team = document.getElementById('uni-team-select').value;
    const year = document.getElementById('year-select').value;
    const container = document.getElementById('full-year-container');
    
    container.innerHTML = "<p class='loading'>Loading Schedule...</p>";

    try {
        const response = await fetch(`mlb-uniforms-${year}.csv?v=${Date.now()}`);
        if (!response.ok) throw new Error("CSV not found");
        const csvText = await response.text();
        const rows = Papa.parse(csvText, { header: false, skipEmptyLines: true }).data;

        container.innerHTML = "";
        const accentColor = getTeamColor(team, year);

        // Defined Season Blocks
        const season = [
            { index: 2, name: "March / April" },
            { index: 4, name: "May" },
            { index: 5, name: "June" },
            { index: 6, name: "July" },
            { index: 7, name: "August" },
            { index: 8, name: "September / October" }
        ];

        season.forEach(monthObj => {
            renderMonth(monthObj, team, year, rows, container, accentColor);
        });
    } catch (err) {
        container.innerHTML = `<p class="error">Data for ${year} is not yet available.</p>`;
    }
}

function renderMonth(monthObj, team, year, rows, container, accent) {
    const section = document.createElement('div');
    section.className = 'month-section';
    section.innerHTML = `<div class="month-title" style="background-color: ${accent}">${monthObj.name} ${year}</div>`;

    const grid = document.createElement('div');
    grid.className = 'calendar-container';

    // Labels
    ['S','M','T','W','T','F','S'].forEach(day => {
        grid.innerHTML += `<div class="day-label">${day}</div>`;
    });

    const firstDay = new Date(year, monthObj.index, 1).getDay();
    const daysInMonth = new Date(year, monthObj.index + 1, 0).getDate();

    for (let i = 0; i < firstDay; i++) grid.innerHTML += `<div class="calendar-cell empty"></div>`;

    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${monthObj.index + 1}/${d}/${year.toString().slice(-2)}`;
        
        // Logic for OAK/ATH Transition
        const dailyGames = rows.filter(r => {
            const isDate = r[0] === dateStr;
            const isTeam = (r[1] === team || r[3] === team) || 
                           (team === "OAK" && (r[1] === "ATH" || r[3] === "ATH"));
            return isDate && isTeam;
        });

        const cell = document.createElement('div');
        cell.className = 'calendar-cell';
        if (dailyGames.length === 0) {
        cell.classList.add('off-day')}
        
        cell.innerHTML = `<span class="day-number">${d}</span>`;

        if (dailyGames.length > 0) {
            if (dailyGames.length === 1) {
                renderJersey(cell, dailyGames[0], team);
            } else {
                const dh = document.createElement('div');
                dh.className = 'dh-container';
                const g1 = document.createElement('div'); g1.className = 'dh-game';
                const g2 = document.createElement('div'); g2.className = 'dh-game';
                renderJersey(g1, dailyGames[0], team);
                renderJersey(g2, dailyGames[1], team);
                dh.append(g1, Object.assign(document.createElement('div'), {className:'dh-divider'}), g2);
                cell.appendChild(dh);
            }
        }
        grid.appendChild(cell);
    }
    section.appendChild(grid);
    container.appendChild(section);
}

function renderJersey(el, row, selectedTeam) {
    const year = document.getElementById('year-select').value;
    const isHome = row[1] === selectedTeam || (selectedTeam === "OAK" && row[1] === "ATH");
    const jersey = isHome ? row[2] : row[4];
    el.classList.add(isHome ? 'is-home' : 'is-away');

    const cleanName = jersey.toLowerCase().trim().replace(/\s+/g, '-');
    const img = document.createElement('img');
    img.src = `images/jerseys/${year}/${selectedTeam}/${cleanName}.png`;
    img.className = 'jersey-icon';
    img.onerror = () => img.style.display = 'none';
    el.appendChild(img);
}

window.onload = () => {
    updateTeamDropdown();
    loadFullYearCalendar();
};

function handleYearChange() {
    updateTeamDropdown();
    loadFullYearCalendar();
}