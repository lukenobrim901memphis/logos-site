const teamNameMap = {
    "isotopes": "Albuquerque",
    "bisons": "Buffalo",
    "knights": "Charlotte",
    "clippers": "Columbus",
    "bulls": "Durham",
    "chihuahuas": "El Paso",
    "stripers": "Gwinnett",
    "indians": "Indianapolis",
    "cubs": "Iowa",
    "jumbo-shrimp": "Jacksonville",
    "aviators": "Las Vegas",
    "ironpigs": "Lehigh Valley",
    "bats": "Louisville",
    "redbirds": "Memphis",
    "sounds": "Nashville",
    "tides": "Norfolk",
    "comets": "Oklahoma City",
    "storm-chasers": "Omaha",
    "aces": "Reno",
    "red-wings": "Rochester",
    "express": "Round Rock",
    "river-cats": "Sacramento",
    "bees": "Salt Lake",
    "railriders": "Scranton/Wilkes-Barre",
    "saints": "St. Paul",
    "space-cowboys": "Sugar Land",
    "mets": "Syracuse",
    "rainiers": "Tacoma",
    "mud-hens": "Toledo",
    "red-sox": "Worcester"
};

// 2. TRIGGERED BY BUTTON (HTML: onclick="loadRoster('isotopes')")
function loadRoster(selectedTeamID) {
    // UI: Reset button styles
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.style.borderColor = "#ccc";
        btn.style.boxShadow = "none";
    });

    // UI: Highlight active button
    const clickedBtn = document.querySelector(`.text-${selectedTeamID}`);
    if (clickedBtn) {
        clickedBtn.style.borderColor = "currentColor";
        clickedBtn.style.boxShadow = "0 0 8px currentColor";
    }

    // Hand off to the CSV fetcher
    fetchAndParseCSV(selectedTeamID);
}

// 3. HANDLES THE CSV LOADING
async function fetchAndParseCSV(selectedTeamID) {
    const csvPath = 'triple-a-rosters.csv';
    
    // 1. Get the exact name from your map (e.g., "Sacramento")
    const targetTeamName = teamNameMap[selectedTeamID];

    Papa.parse(csvPath, {
        download: true,
        header: false,
        skipEmptyLines: true,
        complete: function(results) {
            const tbody = document.getElementById("roster-body");
            if (tbody) tbody.innerHTML = "";
            const teamData = results.data.filter(row => {
                if (!row[4]) return false;
                
                const rowTeam = row[4].trim();
                return rowTeam === targetTeamName;
            });

            console.log(`Filtering for: ${targetTeamName}. Found ${teamData.length} players.`);

            if (teamData.length > 0) {
                renderRoster(teamData, selectedTeamID);
            } else {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px;">No active roster data found for ${targetTeamName}</td></tr>`;
            }
        }
    });
}

// 4. BUILDS THE TABLE
function renderRoster(rosterData, teamId) {
    const tbody = document.getElementById("roster-body");
    const countDisplay = document.getElementById("active-count");
    const titleDisplay = document.getElementById("team-title");
    
    if (!tbody) return;
    
    tbody.innerHTML = ""; 
    let activeCounter = 0;
if (titleDisplay) {
        titleDisplay.innerText = teamNameMap[teamId] + " Roster";
    }

    const statusOrder = {
        "Active": 1, 
        "Rehab Assignment": 1, 
        "Promoted": 2, 
        "Demoted": 3, 
        "Not Yet Reported": 4,
        "Development List": 5, 
        "Injured List": 6, 
        "60-day IL": 7,
        "Full-Season IL": 8,
        "Restricted List": 9,
        "Traded": 10,
        "DFA": 11,
        "Claimed": 12,
        "Retired": 13,
        "Free Agent": 14
    };
    const posOrder = { "P": 1, "C": 2, "INF": 3, "OF": 4 };

    // Sort the list
    rosterData.sort((a, b) => {
        const sA = statusOrder[a[5]] || 99;
        const sB = statusOrder[b[5]] || 99;
        if (sA !== sB) return sA - sB;
        
        const pA = posOrder[a[1]] || 99;
        const pB = posOrder[b[1]] || 99;
        if (pA !== pB) return pA - pB;

        return getSortName(a[2]).localeCompare(getSortName(b[2]));
    });

    rosterData.forEach(player => {
        const row = document.createElement("tr");
        row.classList.add(`text-${teamId}`);

        // Handle faded opacity for inactive players
        if (statusOrder[player[5]] > 1 || !statusOrder[player[5]]) {
            row.classList.add("inactive");
        }
        const status = player[5] ? player[5].trim() : "";
        if (status === "Active") {
            activeCounter++;
        }
        if (status !== "Active" && status !== "Rehab Assignment") {
            row.classList.add("inactive");
        }

        const isFortyMan = player[6] && player[6].trim().toLowerCase() === 'yes';
        const nameClass = isFortyMan ? "forty-man-bold" : "";

        // Raw player[2] preserves capitalization from CSV
        row.innerHTML = `
            <td>${player[0] || '—'}</td> 
            <td>${player[1] || '—'}</td>
            <td class="${nameClass}">${player[2] || 'Unknown'}</td>
            <td>${player[3] || '—'}</td>
            <td>${player[5] || '—'}</td>
        `;
        tbody.appendChild(row);

        if (countDisplay) {
        countDisplay.innerText = activeCounter;
    }
    });
}

// 5. HELPER FUNCTION (Must be outside other functions)
function getSortName(fullName) {
    if (!fullName) return "";
    const parts = fullName.trim().split(" ");
    const suffixes = ["jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"];
    let lastIdx = parts.length - 1;

    if (parts.length > 1 && suffixes.includes(parts[lastIdx].toLowerCase())) {
        lastIdx--; 
    }
    return parts[lastIdx].toLowerCase();
}