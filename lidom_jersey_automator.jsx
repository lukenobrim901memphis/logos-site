// --- CONFIGURATION ---
var userHome = Folder.myDocuments.parent.fsName; 
var icloudRoot = userHome + "/Library/Mobile Documents/com~apple~CloudDocs/Sports/Jerseys/LIDOM";

var sourceFolder = new Folder(icloudRoot + "/LIDOM Templates/2026-27 LIDOM Full jerseys");
var exportFolder = new Folder(icloudRoot + "/LIDOM Jersey Numbers/LIDOM Jersey numbers 2026-27");

// PASTE DATA HERE: Wrap each copied spreadsheet line in single quotes, ending with a comma.
var lines = [
"10/25	Luis Liberato	AGU	51	Road yellow	águilas51 Luis Liberato",
"10/25	Yoelvin Silven	AGU	53	Road yellow	águilas53 Yoelvin Silven",
"10/25	Darlin Saladin	ESS	86	Road black	estrellas86 Darlin Saladin",
"10/25	Juan Santana	ESS	33	Road black	estrellas33 Juan Santana",
"10/25	Gregori Louis	GIG	64	Home white	gigantes64 Gregori Louis",
"10/25	Kelvin Cáceres	GIG	95	Home white	gigantes95 Kelvin Cáceres",
"10/25	Mauricio Estrella	ESC	48	Road red	leones48 Mauricio Estrella",
"10/28	Misael Tamarez	LCY	67	Home black	tigres67 Misael Tamarez",
"10/28	Erick Mejia	AGU	58	Home white alt	águilas58 Erick Mejia",
"10/28	José Leclerc	AGU	21	Home white alt	águilas21 José Leclerc",
"10/28	Abraham Almonte	AGU	86	Home white alt	águilas86 Abraham Almonte",
"10/28	Francys Peguero	AZU	45	Home black	toros45 Francys Peguero",
"10/28	José Devers	ESS	67	Road green	estrellas67 José Devers",
"10/29	Dylan File	AGU	34	Home white alt	águilas34 Dylan File",
"10/29	Rafael Montero	AGU	48	Home white alt	águilas48 Rafael Montero",
"10/29	Wilkin Ramos	AGU	71	Home white alt	águilas71 Wilkin Ramos",
"10/29	Rodolfo Martinez	AZU	59	Home black	toros59 Rodolfo Martinez",
"10/29	Sauryn Lao	ESC	86	Road red	leones86 Sauryn Lao",
"10/29	Darlin Manuel Saladin	ESS	86	Home white green hat	estrellas86 Darlin Manuel Saladin",
"10/29	Antonio Santos	GIG	43	Home white	gigantes43 Antonio Santos",
"10/29	Luis Velasquez	GIG	96	Home white	gigantes96 Luis Velasquez",
"10/30	Sadrac Franco	AGU	90	Road black	águilas90 Sadrac Franco",
"10/30	Carlos Rodriguez	AZU	9	Road gray	toros9 Carlos Rodriguez",
"10/30	Justin Gonzales	AZU	56	Road gray	toros56 Justin Gonzales",
"10/30	Sauryn Lao	ESC	39	Road red	leones39 Sauryn Lao",
"10/30	Edgar Quero	ESS	26	Road black	estrellas26 Edgar Quero",
"10/30	Darlin Manuel Saladin	ESS	59	Road black	estrellas59 Darlin Manuel Saladin",
"10/30	Domingo Tapia	ESS	60	Road black	estrellas60 Domingo Tapia",
"10/30	Tyler Thomas	GIG	70	Home white	gigantes70 Tyler Thomas",
"10/30	Jake Eder	GIG	87	Home white	gigantes87 Jake Eder",
"10/30	Richard Guasch	GIG	93	Home white	gigantes93 Richard Guasch",
"10/30	Cam Robinson	LCY	60	Road blue alt	tigres60 Cam Robinson",
"10/31	Frederick Bencosme	AGU	82	Home white	águilas82 Frederick Bencosme",
"10/31	Jared Oliva	AZU	4	Home white	toros4 Jared Oliva",
"10/31	Jaime Barria	ESS	73	Road green	estrellas73 Jaime Barria",
"10/31	Gilberto Jimenez	GIG	81	Road red	gigantes81 Gilberto Jimenez",
"10/31	Brent Honeywell	GIG	85	Road red	gigantes85 Brent Honeywell",
"10/31	Andretty Cordero	LCY	24	Home white	tigres24 Andretty Cordero",
];

if (!exportFolder.exists) {
    exportFolder.create();
}

for (var i = 0; i < lines.length; i++) {
    if (lines[i].replace(/\s/g, "") === "") {
        continue;
    }
    
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
        saveName = saveName.toString().replace(/\//g, "-");
    } else {
        saveName = "Emergency_Export_" + i;
    }
    
    // Uses the new custom logic to grab everything after the first space
    var lastName = parseLastName(playerName); 
    var cleanLastName = stripAccents(lastName.toUpperCase());
    
    var psdFileName = teamAbbr + " " + jerseyName + ".psd";
    var psdFile = new File(sourceFolder + "/" + psdFileName);
    
    if (psdFile.exists) {
        var originalRulerUnits = app.preferences.rulerUnits;
        app.preferences.rulerUnits = Units.PIXELS;

        var doc = app.open(psdFile);
        
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
        jpgOptions.quality = 10; 
        
        doc.saveAs(jpgFile, jpgOptions, true, Extension.LOWERCASE);
        doc.close(SaveOptions.DONOTSAVECHANGES);

        app.preferences.rulerUnits = originalRulerUnits;
    } else {
        $.writeln("Missing file skipped: " + psdFileName);
    }
}

alert("Batch processing complete!");

// --- HELPER FUNCTIONS ---

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