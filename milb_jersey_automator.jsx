// --- CONFIGURATION ---
var userHome = Folder.myDocuments.parent.fsName; 
var icloudRoot = userHome + "/Library/Mobile Documents/com~apple~CloudDocs/Sports/Jerseys/MiLB";

var sourceFolder = new Folder(icloudRoot + "/2026 MiLB Full jerseys");
var exportFolder = new Folder(icloudRoot + "/MiLB Jersey numbers 2026");

// Paste your raw data between the multi-line quotes below
var lines = [
"6/10	Jake Woodford	NVL	40	Home powder affiliate	sounds40 Jake Woodford"
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
                // Phillies rule: find and edit ALL layers named "12" regardless of visibility
                var philliesLayers = searchLayers(doc, "12", true);
                for (var k = 0; k < philliesLayers.length; k++) {
                    var currentNumLayer = philliesLayers[k];
                    doc.activeLayer = currentNumLayer;
                    changeTextViaActionManager(currentNumLayer, jerseyNum);
                    applyDirectNudge(jerseyNum);
                }
            } else {
                // Normal processing: find layers named "12" but only edit if they are visible
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

function parseLastName(fullName) {
    if (!fullName) return "";
    var parts = fullName.split(/\s+/);
    if (parts.length <= 1) {
        return fullName;
    }
    var lastIdx = parts.length - 1;
    var lastWord = parts[lastIdx];
    var lastWordUpper = lastWord.toUpperCase().replace(/[^A-Z]/g, ""); 
    var suffixes = { "JR": true, "SR": true, "II": true, "III": true, "IV": true, "V": true };
    if (suffixes[lastWordUpper] && parts.length > 2) {
        return parts[lastIdx - 1] + " " + lastWord;
    }
    return lastWord;
}

// UNIFIED LAYER ENGINE: Replaces both old lookup routines to prevent compilation errors
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
            if (!returnAllMatches) {
                return foundLayers;
            }
        }
    }

    return foundLayers;
}