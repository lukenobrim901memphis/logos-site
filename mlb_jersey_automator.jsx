// --- CONFIGURATION ---
var userHome = Folder.myDocuments.parent.fsName; 
var icloudRoot = userHome + "/Library/Mobile Documents/com~apple~CloudDocs/Sports/Jerseys/MLB";

var sourceFolder = new Folder(icloudRoot + "/MLB Templates/2023 MLB Full jerseys");
var exportFolder = new Folder(icloudRoot + "/MLB Jersey Numbers/MLB Jersey numbers 2023");

// --- TIMING SETTINGS (raise these if you still get errors) ---
// All times are in milliseconds: 1000 = 1 second.
var DOWNLOAD_TIMEOUT_MS     = 300000; // max wait for an iCloud template to download (5 min)
var OPEN_ATTEMPTS           = 7;      // how many times to try opening a template
var SAVE_ATTEMPTS           = 3;      // how many times to try saving the JPG
var RETRY_DELAY_MS          = 20000;   // wait between retries (5 sec)
var SETTLE_AFTER_OPEN_MS    = 1000;   // pause after a template opens, before editing (1 sec)
var PAUSE_BETWEEN_JERSEYS_MS = 2000;  // breather between jerseys (1.5 sec)
var PURGE_EVERY             = 10;     // clear Photoshop's memory caches every N jerseys (0 = never)

// PASTE DATA HERE: Wrap each copied spreadsheet line in single quotes, ending with a comma.
var lines = [
"2023/03/30	Andrew Vasquez	PHI	37	Road gray	2023/03/30 phillies37 Andrew Vasquez",
"2023/03/31	Cristian Pache	PHI	19	Road gray	2023/03/31 phillies19 Cristian Pache",
"2023/04/04	McKinley Moore	PHI	79	Road gray	2023/04/04 phillies79 McKinley Moore",
"2023/04/16	Luis Ortiz	PHI	56	Road gray	2023/04/16 phillies56 Luis Ortiz",
"2023/05/04	Jeff Hoffman	PHI	68	Home white	2023/05/04 phillies68 Jeff Hoffman",
"2023/05/16	Erich Uelmen	PHI	47	Road gray	2023/05/16 phillies47 Erich Uelmen",
"2023/05/23	Dylan Covey	PHI	54	Home white	2023/05/23 phillies54 Dylan Covey",
"2023/06/01	Drew Ellis	PHI	35	Road red	2023/06/01 phillies35 Drew Ellis",
"2023/07/14	Johan Rojas	PHI	18	Home white	2023/07/14 phillies18 Johan Rojas",
"2023/08/02	Michael Lorenzen	PHI	22	Road gray	2023/08/02 phillies22 Michael Lorenzen",
"2023/08/02	Rodolfo Castro	PHI	29	Road gray	2023/08/02 phillies29 Rodolfo Castro",
"2023/08/06	Weston Wilson	PHI	37	Home cream	2023/08/06 phillies37 Weston Wilson",
"2023/09/22	Orion Kerkering	PHI	50	Home white	2023/09/22 phillies50 Orion Kerkering",
];

// BACK-OF-JERSEY NAME OVERRIDES
// Left side  = player's full name exactly as it appears in your list.
// Right side = the text in quotes is what gets printed on the back of the jersey.
// Matching ignores capitalization, accents and extra spaces.
// Anyone NOT listed here falls back to "everything after the first space".
// To change what prints, edit the quoted text on the right. To add a player, copy a line.
var BACK_NAME_OVERRIDES = {
    // --- Multi-word last names (particles: De, Del, De La, De Los, Van, La, St., etc.) ---
    "Abel De Los Santos":       "DE LOS SANTOS",
    "Adrian Del Castillo":      "DEL CASTILLO",
    "Alejandro De Aza":         "DE AZA",
    "Alex De Goti":             "DE GOTI",
    "Angel De Jesus":           "DE JESUS",
    "Brett de Geus":            "DE GEUS",
    "Brian Van Belle":          "VAN BELLE",
    "Bryan De La Cruz":         "DE LA CRUZ",
    "Bryce Montes de Oca":      "MONTES DE OCA",
    "Chase De Jong":            "DE JONG",
    "Christian Montes De Oca":  "MONTES DE OCA",
    "Cole De Vries":            "DE VRIES",
    "Dane De La Rosa":          "DE LA ROSA",
    "Daniel Ponce de Leon":     "PONCE DE LEON",
    "Elly De La Cruz":          "DE LA CRUZ",
    "Enmanuel De Jesus":        "DE JESUS",
    "Enyel De Los Santos":      "DE LOS SANTOS",
    "Eury De La Rosa":          "DE LA ROSA",
    "Frank De Los Santos":      "DE LOS SANTOS",
    "Jasseel De La Cruz":       "DE LA CRUZ",
    "Joe La Sorsa":             "LA SORSA",
    "Joel De La Cruz":          "DE LA CRUZ",
    "Jorge De La Rosa":         "DE LA ROSA",
    "Jorge De Leon":            "DE LEON",
    "Jose De La Torre":         "DE LA TORRE",
    "Jose De Leon":             "DE LEON",
    "Jose De Paula":            "DE PAULA",
    "Justin De Fratus":         "DE FRATUS",
    "Locke St. John":           "ST. JOHN",
    "Luis De Los Santos":       "DE LOS SANTOS",
    "Matt den Dekker":          "DEN DEKKER",
    "Miguel Del Pozo":          "DEL POZO",
    "Rick Van Den Hurk":        "VAN DEN HURK",
    "Scott Van Slyke":          "VAN SLYKE",
    "Simeon Woods Richardson":  "WOODS RICHARDSON",
    "Tommy La Stella":          "LA STELLA",
    "Yerry De los Santos":      "DE LOS SANTOS",

    // --- Two-word FIRST names (default rule would grab part of the first name) ---
    "Chi Chi Gonzalez":         "GONZALEZ",
    "Hoy Jun Park":             "PARK",
    "Hyun Soo Kim":             "KIM",
    "Jean Carlos Mejia":        "MEJIA",
    "Ji Hwan Bae":              "BAE",
    "Ji Man Choi":              "CHOI",
    "John Ryan Murphy":         "MURPHY",
    "Jose Manuel Fernandez":    "FERNANDEZ",
    "Jose Miguel Fernandez":    "FERNANDEZ",
    "Juan Carlos Oviedo":       "OVIEDO",
    "Luis Alexander Basabe":    "BASABE",
    "Sugar Ray Marimon":        "MARIMON",

    // --- Middle initials (default rule would print "A. TAYLOR" etc.) ---
    "Diego A. Castillo":        "CASTILLO",
    "Jose A. Ferrer":           "FERRER",
    "Josh A. Smith":            "SMITH",
    "Josh D. Smith":            "SMITH",
    "Luis F. Castillo":         "CASTILLO",
    "Michael A. Taylor":        "TAYLOR",

    // --- Suffixes (Jr. / II / III / IV) ---
    "Albert Almora Jr.":        "ALMORA",
    "Bernardo Flores Jr.":      "FLORES JR.",
    "Bobby Witt Jr.":           "WITT JR.",
    "Brent Honeywell Jr.":      "HONEYWELL",
    "Carl Edwards Jr.":         "EDWARDS JR.",
    "DaShawn Keirsey Jr.":      "KEIRSEY JR.",
    "Daniel Lynch IV":          "LYNCH IV",
    "Delino DeShields Jr.":     "DESHIELDS JR.",
    "Duane Underwood Jr.":      "UNDERWOOD JR.",
    "Dwight Smith Jr.":         "SMITH JR.",
    "Eric Young Jr.":           "YOUNG JR.",
    "Fernando Tatis Jr.":       "TATIS JR.",
    "Ivan De Jesus Jr.":        "DE JESUS JR.",
    "Jackie Bradley Jr.":       "BRADLEY JR.",
    "Jazz Chisholm Jr.":        "CHISHOLM JR.",
    "John Mayberry Jr.":        "MAYBERRY",
    "LaMonte Wade Jr.":         "WADE JR.",
    "Lance McCullers Jr.":      "MCCULLERS",
    "Lourdes Gurriel Jr.":      "GURRIEL JR.",
    "Mark Leiter Jr.":          "LEITER",
    "Melvin Upton Jr.":         "UPTON JR.",
    "Michael Harris II":        "HARRIS II",
    "Mike Wright Jr.":          "WRIGHT",
    "Nacho Alvarez Jr.":        "ALVAREZ",
    "Nestor Cortes Jr.":        "CORTES",
    "Ralph Garza Jr.":          "GARZA JR.",
    "Richie Martin Jr.":        "MARTIN",
    "Rickie Weeks Jr.":         "WEEKS",
    "Robbie Ross Jr.":          "ROSS",
    "Robert Hassell III":       "HASSELL III",
    "Ronald Acuna Jr.":         "ACUNA JR.",
    "Sean Kazmar Jr.":          "KAZMAR",
    "Steve Lombardozzi Jr.":    "LOMBARDOZZI",
    "Steven Souza Jr.":         "SOUZA",
    "Tony Gwynn Jr.":           "GWYNN",
    "Troy Stokes Jr.":          "STOKES JR.",
    "Victor Mesa Jr.":          "MESA JR.",
    "Victor Scott II":          "SCOTT II",
    "Vladimir Guerrero Jr.":    "GUERRERO JR."
};

if (!exportFolder.exists) {
    exportFolder.create();
}

// --- PROGRESS LOG ---
// Every jersey that exports successfully is written to PROGRESS_FILE right away.
// If Photoshop errors or crashes partway through, just run the script again with
// the same list: anything already in the progress file is skipped.
// Jerseys that fail are written to ERRORS_FILE (with the reason) and the batch
// keeps going. When a run finishes with NO errors, the progress file is deleted
// so your next batch starts fresh.
var PROGRESS_FILE = Folder.desktop.fsName + "/jersey_numbers_progress.txt";
var ERRORS_FILE   = Folder.desktop.fsName + "/jersey_numbers_errors.txt";

var completedJerseys = loadJerseyProgress();
var doneCount = 0, skippedCount = 0, errorCount = 0;

for (var i = 0; i < lines.length; i++) {
    if (!lines[i] || lines[i].replace(/\s/g, "") === "") {
        continue;
    }

    // The pasted line itself (trimmed) identifies the jersey in the log files
    var progressKey = lines[i].replace(/^\s+|\s+$/g, "");
    if (completedJerseys[progressKey]) {
        $.writeln("Skipping (already done): " + progressKey);
        skippedCount++;
        continue;
    }

    var doc = null;
    try {

        // AUTO-CONVERT LOOSE SPACES TO TABS IF NO TABS DETECTED
        var rawLine = lines[i];
        if (rawLine.indexOf("\t") === -1) {
            rawLine = rawLine.replace(/^([^\s]+)\s+([^\s]+\s+[^\s]+)\s+([A-Z]{3})\s+(\d+)\s+(.+?)\s+((?:\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2})\s+.+)$/, "$1\t$2\t$3\t$4\t$5\t$6");
        }
    
        var columns = rawLine.split("\t"); 
        var playerName = columns[1];
        var teamAbbr   = columns[2];
        var jerseyNum  = columns[3];
        var jerseyName = columns[4];
        var saveName   = columns[5];
    
        // TYPE GUARD: Only attempt to replace text characters if the variable is defined cleanly
        if (typeof saveName !== "undefined" && saveName !== null) {
            // macOS can't store "/" inside a filename at the system level, but a ":"
            // in the system path is shown as "/" in Finder. So "2012/10/03 bluejays13"
            // is written as "2012:10:03 bluejays13" and Finder displays "2012/10/03 bluejays13".
            saveName = saveName.toString().replace(/\//g, ":");
        } else {
            saveName = "Emergency_Export_" + i;
        }
    
        // Uses the override list first, then falls back to everything after the first space
        var lastName = getBackName(playerName);
        var cleanLastName = stripAccents(lastName.toUpperCase());
    
        var psdFileName = teamAbbr + " " + jerseyName + ".psd";
        var psdFile = new File(sourceFolder + "/" + psdFileName);
    
        if (psdFile.exists) {
            var originalRulerUnits = app.preferences.rulerUnits;
            app.preferences.rulerUnits = Units.PIXELS;

            doc = app.open(psdFile);
        
            // CHECK FOR JACKIE ROBINSON DAY EXCEPTION
            var isJackieDay = false;
            if (jerseyName) {
                isJackieDay = (jerseyName.toUpperCase().indexOf("JACKIE ROBINSON DAY") !== -1);
            }
        
            if (isJackieDay) {
                $.writeln("Jackie Robinson Day template detected: Exporting " + psdFileName + " without edits.");
            } else {
                // Use unified search engine to gather layers safely
                var nameLayers = searchLayers(doc, "NAME", false);
                var backNumLayers = searchLayers(doc, "00", false);
            
                // 1. Process Name Layer (Preserving Visibility and Forcing Injection)
                if (nameLayers.length > 0) {
                    var nameLayer = nameLayers[0];
                    var originalVisibility = nameLayer.visible; 
                    doc.activeLayer = nameLayer;
                    changeTextViaActionManager(nameLayer, cleanLastName);
                    nameLayer.visible = originalVisibility; 
                }
            
                // 2. Process Back Numbers
                if (backNumLayers.length > 0) {
                    var backNumLayer = backNumLayers[0];
                    var originalBackVisibility = backNumLayer.visible;
                    doc.activeLayer = backNumLayer;
                    changeTextViaActionManager(backNumLayer, jerseyNum);
                    applyDirectNudge(jerseyNum);
                    backNumLayer.visible = originalBackVisibility;
                }
            
                // 3. Process Front / Sleeve Numbers
                var isPhilliesSleeveTemplate = (teamAbbr && teamAbbr.toUpperCase() === "PHI" && jerseyName && 
                    (jerseyName.toUpperCase().indexOf("HOME WHITE") !== -1 || jerseyName.toUpperCase().indexOf("ROAD GRAY") !== -1));

                if (isPhilliesSleeveTemplate) {
                    var philliesLayers = searchLayers(doc, "12", true);
                    for (var k = 0; k < philliesLayers.length; k++) {
                        var currentNumLayer = philliesLayers[k];
                        doc.activeLayer = currentNumLayer;
                        changeTextViaActionManager(currentNumLayer, jerseyNum);
                        applyDirectNudge(jerseyNum);
                    }
                } else {
                    var standardFrontLayers = searchLayers(doc, "12", false);
                    if (standardFrontLayers.length > 0) {
                        var frontNumLayer = standardFrontLayers[0];
                        if (frontNumLayer.visible) {
                            doc.activeLayer = frontNumLayer;
                            changeTextViaActionManager(frontNumLayer, jerseyNum);
                            applyDirectNudge(jerseyNum);
                        }
                    }
                }
            }
        
            // Final Document Rasterization Export
            var jpgFile = new File(exportFolder + "/" + saveName + ".jpg");
            var jpgOptions = new JPEGSaveOptions();
            jpgOptions.embedColorProfile = true;
            jpgOptions.formatOptions = FormatOptions.STANDARDBASELINE;
            jpgOptions.quality = 12; 
        
            doc.saveAs(jpgFile, jpgOptions, true, Extension.LOWERCASE);
            doc.close(SaveOptions.DONOTSAVECHANGES);

            app.preferences.rulerUnits = originalRulerUnits;

            // Record this jersey as finished so a re-run skips it
            markJerseyDone(progressKey);
            doneCount++;
        } else {
            logJerseyError(progressKey, "template not found: " + psdFileName);
            errorCount++;
            continue;
        }
    } catch (err) {
        // Log the failure, close the document without saving, and keep going
        logJerseyError(progressKey, (err && err.message) ? err.message : String(err));
        errorCount++;
        try { if (doc) doc.close(SaveOptions.DONOTSAVECHANGES); } catch (closeErr) {}
        try { if (typeof originalRulerUnits !== "undefined") app.preferences.rulerUnits = originalRulerUnits; } catch (unitErr) {}
    }
}

if (errorCount === 0) {
    var pf = new File(PROGRESS_FILE);
    if (pf.exists) pf.remove();
    alert("Batch processing complete!\n\n" + doneCount + " exported, " + skippedCount + " skipped (already done).\nProgress file cleared.");
} else {
    alert("Batch finished with " + errorCount + " error(s).\n\n" + doneCount + " exported, " + skippedCount + " skipped (already done).\n\nSee jersey_numbers_errors.txt on your Desktop.\nFix the problem and run the script again with the same list - finished jerseys will be skipped.");
}

// --- HELPER FUNCTIONS ---

// Reads the progress file into a lookup of finished jerseys
function loadJerseyProgress() {
    var done = {};
    var f = new File(PROGRESS_FILE);
    if (!f.exists) return done;
    f.encoding = "UTF-8";
    f.open("r");
    while (!f.eof) {
        var line = f.readln();
        if (line.length > 0) done[line] = true;
    }
    f.close();
    return done;
}

// Appends one finished jersey to the progress file
function markJerseyDone(key) {
    var f = new File(PROGRESS_FILE);
    f.encoding = "UTF-8";
    f.open("a");
    f.writeln(key);
    f.close();
}

// Appends a failed jersey and the reason to the errors file
function logJerseyError(key, reason) {
    var f = new File(ERRORS_FILE);
    f.encoding = "UTF-8";
    f.open("a");
    f.writeln(new Date().toLocaleString() + "\t" + key + "\t[" + reason + "]");
    f.close();
    $.writeln("ERROR: " + key + " [" + reason + "]");
}


function changeTextViaActionManager(layer, newString) {
    try {
        var targetID = stringIDToTypeID("textLayer");
        var propertyID = stringIDToTypeID("textKey");
        
        var actionRef = new ActionReference();
        actionRef.putProperty(stringIDToTypeID("property"), propertyID);
        actionRef.putEnumerated(targetID, stringIDToTypeID("ordinal"), stringIDToTypeID("targetEnum"));
        
        var layerDescriptor = executeActionGet(actionRef);
        if (layerDescriptor.hasKey(propertyID)) {
            var textKeyDescriptor = layerDescriptor.getObjectValue(propertyID);
            textKeyDescriptor.putString(stringIDToTypeID("textKey"), newString);
            
            var baseDescriptor = new ActionDescriptor();
            var targetRef = new ActionReference();
            targetRef.putEnumerated(targetID, stringIDToTypeID("ordinal"), stringIDToTypeID("targetEnum"));
            
            baseDescriptor.putReference(stringIDToTypeID("null"), targetRef);
            baseDescriptor.putObject(stringIDToTypeID("to"), targetID, textKeyDescriptor);
            
            executeAction(stringIDToTypeID("set"), baseDescriptor, DialogModes.NO);
        }
    } catch (e) {
        if (layer && layer.kind === LayerKind.TEXT) {
            layer.textItem.contents = newString;
        }
    }
}

function applyDirectNudge(numberStr) {
    try {
        var shiftAmount = 0;
        var num = parseInt(numberStr, 10);

        if (numberStr === "41") { 
            shiftAmount = -13; 
        } else if (numberStr === "4") {
            shiftAmount = -7;
        } else if (num >= 40 && num <= 49) { 
            shiftAmount = -7;
        } else if (numberStr.slice(-1) === "1") { 
            shiftAmount = -7; 
        }

        if (shiftAmount !== 0) {
            var descMove = new ActionDescriptor();
            var refLayer = new ActionReference();
            refLayer.putEnumerated(charIDToTypeID("Lyr "), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
            descMove.putReference(charIDToTypeID("null"), refLayer);
            
            var descOffset = new ActionDescriptor();
            descOffset.putUnitDouble(charIDToTypeID("Hrzn"), charIDToTypeID("#Pxl"), shiftAmount);
            descOffset.putUnitDouble(charIDToTypeID("Vrtc"), charIDToTypeID("#Pxl"), 0.0);
            
            descMove.putObject(charIDToTypeID("T   "), charIDToTypeID("Ofst"), descOffset);
            executeAction(charIDToTypeID("move"), descMove, DialogModes.NO);
        }
    } catch(e) {
        $.writeln("Nudge adjustment failed: " + e.message);
    }
}

function stripAccents(str) {
    if (!str) return "";
    var accents = "ÁÀÂÄÃÅÉÈÊËÍÌÎÏÓÒÔÖÕØÚÙÛÜÑÇÝ";
    var purer   = "AAAAAAEEEEIIIIOOOOOOUUUUNCY";
    var converted = "";
    for (var i = 0; i < str.length; i++) {
        var c = str.charAt(i);
        var index = accents.indexOf(c);
        if (index !== -1) { 
            converted += purer.charAt(index); 
        } else { 
            converted += c; 
        }
    }
    return converted;
}

// Normalizes a name for lookup: trims, collapses spaces, uppercases, strips accents
function normalizeNameKey(name) {
    if (!name) return "";
    var s = name.toString().replace(/^\s+|\s+$/g, "").replace(/\s+/g, " ");
    return stripAccents(s.toUpperCase());
}

// Normalized copy of the override table, built on first use so lookups ignore case/accents/spacing
var NORMALIZED_OVERRIDES = null;

// Returns the back-of-jersey text: override if listed, otherwise the default rule
function getBackName(fullName) {
    if (!NORMALIZED_OVERRIDES) {
        NORMALIZED_OVERRIDES = {};
        for (var k in BACK_NAME_OVERRIDES) {
            if (BACK_NAME_OVERRIDES.hasOwnProperty(k)) {
                NORMALIZED_OVERRIDES[normalizeNameKey(k)] = BACK_NAME_OVERRIDES[k];
            }
        }
    }
    var key = normalizeNameKey(fullName);
    if (NORMALIZED_OVERRIDES.hasOwnProperty(key)) {
        return NORMALIZED_OVERRIDES[key];
    }
    return parseLastName(fullName);
}

// NEW FUNCTION LOGIC: Captures everything directly following the very first blank space character
function parseLastName(fullName) {
    if (!fullName) return "";
    
    // Finds the index of the first space character
    var firstSpaceIdx = fullName.indexOf(" ");
    
    // If no space exists, fallback to using the original full text string
    if (firstSpaceIdx === -1) {
        return fullName;
    }
    
    // Slices out everything after that space and trims loose trailing edges
    return fullName.substring(firstSpaceIdx + 1).replace(/^\s+|\s+$/g, "");
}

function searchLayers(container, targetName, returnAllMatches) {
    var foundLayers = [];
    
    if (container.typename === "LayerSet" && !container.visible) {
        return foundLayers;
    }
    
    for (var m = 0; m < container.artLayers.length; m++) {
        var cleanLayerName = container.artLayers[m].name.replace(/\s/g, "").toUpperCase();
        if (cleanLayerName === targetName.toUpperCase()) { 
            foundLayers.push(container.artLayers[m]);
            if (!returnAllMatches) {
                return foundLayers;
            }
        }
    }
    
    for (var g = 0; g < container.layerSets.length; g++) {
        var childResults = searchLayers(container.layerSets[g], targetName, returnAllMatches);
if (childResults.length > 0) {
foundLayers = foundLayers.concat(childResults);
if (!returnAllMatches) 
{return foundLayers;}}}
return foundLayers;
}