const teamNameMap = {
    "aguilas": "Aguilas Cibaenas",
    "estrellas": "Estrellas Orientales",
    "gigantes": "Gigantes del Cibao",
    "leones": "Leones del Escogido",
    "tigres": "Tigres del Licey",
    "toros": "Toros del Este",
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
    const csvPath = 'lidom-rosters.csv';
    
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
    const titleDisplay = document.getElementById("team-title");

    if (!tbody) return;

    tbody.innerHTML = "";

    if (titleDisplay) {
        titleDisplay.innerText = teamNameMap[teamId] + " Roster";
    }

    const statusOrder = { "Active": 1, "Inactive": 2 };
    const posOrder = { "P": 1, "C": 2, "INF": 3, "OF": 4 };

    // Sort the list
    rosterData.sort((a, b) => {
    const sA = statusOrder[(a[5] || "").trim()] || 99;
    const sB = statusOrder[(b[5] || "").trim()] || 99;
    if (sA !== sB) return sA - sB;

    const pA = posOrder[a[1]] || 99;
    const pB = posOrder[b[1]] || 99;
    if (pA !== pB) return pA - pB;

    // Sort by jersey number (blank or non-numeric numbers go last)
    const nA = parseInt(a[0], 10);
    const nB = parseInt(b[0], 10);
    return (isNaN(nA) ? 999 : nA) - (isNaN(nB) ? 999 : nB);
});

    rosterData.forEach(player => {
        const row = document.createElement("tr");
        row.classList.add(`text-${teamId}`);

        const status = (player[5] || "").trim();

        // Fade anyone who isn't Active
        if (status !== "Active") {
            row.classList.add("inactive");
        }

        row.innerHTML = `
            <td>${player[0] || '—'}</td>
            <td>${player[1] || '—'}</td>
            <td>${player[2] || 'Unknown'}</td>
            <td>${player[3] || '—'}</td>
            <td>${status || '—'}</td>
        `;
        tbody.appendChild(row);
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