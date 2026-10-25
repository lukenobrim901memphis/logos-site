// --- CONFIGURATION ---
var userHome = Folder.myDocuments.parent.fsName; 
var icloudRoot = userHome + "/Library/Mobile Documents/com~apple~CloudDocs/Sports/Jerseys/MLB";

var sourceFolder = new Folder(icloudRoot + "/MLB Templates/2020 MLB Full jerseys");
var exportFolder = new Folder(icloudRoot + "/MLB Jersey Numbers/MLB Jersey numbers 2020");

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
"2020/07/23	Jon Jay	ARI	9	Road gray Black Lives Matter patch United For Change patch	2020/07/23 dbacks9 Jon Jay",
"2020/07/23	Josh Rojas	ARI	10	Road gray Black Lives Matter patch United For Change patch	2020/07/23 dbacks10 Josh Rojas",
"2020/07/23	Terrance Gore	LAD	27	Home white Black Lives Matter patch United For Change patch	2020/07/23 dodgers27 Terrance Gore",
"2020/07/23	Jake McGee	LAD	41	Home white Black Lives Matter patch United For Change patch	2020/07/23 dodgers41 Jake McGee",
"2020/07/23	Brusdar Graterol	LAD	48	Home white Black Lives Matter patch United For Change patch	2020/07/23 dodgers48 Brusdar Graterol",
"2020/07/23	Mookie Betts	LAD	50	Home white Black Lives Matter patch United For Change patch	2020/07/23 dodgers50 Mookie Betts",
"2020/07/23	Chris Iannetta	NYY	22	Road gray Black Lives Matter patch United For Change patch Hank Steinbrenner HGS memorial patch	2020/07/23 yankees22 Chris Iannetta",
"2020/07/23	Luis Avilan	NYY	70	Road gray Black Lives Matter patch United For Change patch Hank Steinbrenner HGS memorial patch	2020/07/23 yankees70 Luis Avilan",
"2020/07/23	Thairo Estrada	NYY	71	Road gray Black Lives Matter patch United For Change patch Hank Steinbrenner HGS memorial patch	2020/07/23 yankees71 Thairo Estrada",
"2020/07/23	Mauricio Dubon	SFG	1	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants1 Mauricio Dubon",
"2020/07/23	Hunter Pence	SFG	8	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants8 Hunter Pence",
"2020/07/23	Alex Dickerson	SFG	12	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants12 Alex Dickerson",
"2020/07/23	Austin Slater	SFG	13	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants13 Austin Slater",
"2020/07/23	Tyler Anderson	SFG	31	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants31 Tyler Anderson",
"2020/07/23	Darin Ruf	SFG	33	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants33 Darin Ruf",
"2020/07/23	Rico Garcia	SFG	39	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants39 Rico Garcia",
"2020/07/23	Wilmer Flores	SFG	41	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants41 Wilmer Flores",
"2020/07/23	Tyler Heineman	SFG	43	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants43 Tyler Heineman",
"2020/07/23	Rob Brantly	SFG	61	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants61 Rob Brantly",
"2020/07/23	Joe McCarthy	SFG	70	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants70 Joe McCarthy",
"2020/07/23	Caleb Baragar	SFG	73	Road gray Black Lives Matter patch United For Change patch 20 at 24 patch	2020/07/23 giants73 Caleb Baragar",
"2020/07/23	Emilio Bonifacio	WSN	27	Home white Championship 2019 World Series champions patch Black Lives Matter patch United For Change patch	2020/07/23 nationals27 Emilio Bonifacio",
"2020/07/23	Sam Freeman	WSN	39	Home white Championship 2019 World Series champions patch Black Lives Matter patch United For Change patch	2020/07/23 nationals39 Sam Freeman",
"2020/07/23	Kyle Finnegan	WSN	67	Home white Championship 2019 World Series champions patch Black Lives Matter patch United For Change patch	2020/07/23 nationals67 Kyle Finnegan",
"2020/07/24	Taylor Widener	ARI	57	Road gray Black Lives Matter patch United For Change patch	2020/07/24 dbacks57 Taylor Widener",
"2020/07/24	Matt Adams	ATL	18	Road navy Black Lives Matter patch United For Change patch	2020/07/24 braves18 Matt Adams",
"2020/07/24	Josh Tomlin	ATL	38	Road navy Black Lives Matter patch United For Change patch	2020/07/24 braves38 Josh Tomlin",
"2020/07/24	Jhoulys Chacin	ATL	48	Road navy Black Lives Matter patch United For Change patch	2020/07/24 braves48 Jhoulys Chacin",
"2020/07/24	William Contreras	ATL	60	Road navy Black Lives Matter patch United For Change patch	2020/07/24 braves60 William Contreras",
"2020/07/24	Tyler Matzek	ATL	68	Road navy Black Lives Matter patch United For Change patch	2020/07/24 braves68 Tyler Matzek",
"2020/07/24	Andrew Velazquez	BAL	13	Road black O's hat Black Lives Matter patch United For Change patch	2020/07/24 orioles13 Andrew Velazquez",
"2020/07/24	Wade LeBlanc	BAL	23	Road black O's hat Black Lives Matter patch United For Change patch	2020/07/24 orioles23 Wade LeBlanc",
"2020/07/24	Cole Sulser	BAL	54	Road black O's hat Black Lives Matter patch United For Change patch	2020/07/24 orioles54 Cole Sulser",
"2020/07/24	Tommy Milone	BAL	69	Road black O's hat Black Lives Matter patch United For Change patch	2020/07/24 orioles69 Tommy Milone",
"2020/07/24	Travis Lakins	BAL	70	Road black O's hat Black Lives Matter patch United For Change patch	2020/07/24 orioles70 Travis Lakins",
"2020/07/24	Pat Valaika	BAL	74	Road black O's hat Black Lives Matter patch United For Change patch	2020/07/24 orioles74 Pat Valaika",
"2020/07/24	Kevin Pillar	BOS	5	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox5 Kevin Pillar",
"2020/07/24	Jonathan Lucroy	BOS	12	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox12 Jonathan Lucroy",
"2020/07/24	Tzu-Wei Lin	BOS	30	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox30 Tzu-Wei Lin",
"2020/07/24	Austin Brice	BOS	31	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox31 Austin Brice",
"2020/07/24	Josh Osich	BOS	35	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox35 Josh Osich",
"2020/07/24	Jonathan Arauz	BOS	36	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox36 Jonathan Arauz",
"2020/07/24	Dylan Covey	BOS	46	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox46 Dylan Covey",
"2020/07/24	Colten Brewer	BOS	48	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox48 Colten Brewer",
"2020/07/24	Matt Hall	BOS	56	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox56 Matt Hall",
"2020/07/24	Jeffrey Springs	BOS	59	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox59 Jeffrey Springs",
"2020/07/24	Phillips Valdez	BOS	71	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox71 Phillips Valdez",
"2020/07/24	Alex Verdugo	BOS	99	Home white Black Lives Matter patch United For Change patch	2020/07/24 redsox99 Alex Verdugo",
"2020/07/24	Josh Phegley	CHC	4	Home white Black Lives Matter patch United For Change patch	2020/07/24 cubs4 Josh Phegley",
"2020/07/24	Jason Kipnis	CHC	27	Home white Black Lives Matter patch United For Change patch	2020/07/24 cubs27 Jason Kipnis",
"2020/07/24	Craig Kimbrel	CHC	46	Home white Black Lives Matter patch United For Change patch	2020/07/24 cubs46 Craig Kimbrel",
"2020/07/24	Rex Brothers	CHC	48	Home white Black Lives Matter patch United For Change patch	2020/07/24 cubs48 Rex Brothers",
"2020/07/24	Nicky Delmonico	CHW	26	Home black Black Lives Matter patch United For Change patch Ed Farmer FARMIO memorial patch	2020/07/24 whitesox26 Nicky Delmonico",
"2020/07/24	Cheslor Cuthbert	CHW	36	Home black Black Lives Matter patch United For Change patch Ed Farmer FARMIO memorial patch	2020/07/24 whitesox36 Cheslor Cuthbert",
"2020/07/24	Jimmy Lambert	CHW	58	Home black Black Lives Matter patch United For Change patch Ed Farmer FARMIO memorial patch	2020/07/24 whitesox58 Jimmy Lambert",
"2020/07/24	Codi Heuer	CHW	65	Home black Black Lives Matter patch United For Change patch Ed Farmer FARMIO memorial patch	2020/07/24 whitesox65 Codi Heuer",
"2020/07/24	Brooks Raley	CIN	43	Home white Black Lives Matter patch United For Change patch	2020/07/24 reds43 Brooks Raley",
"2020/07/24	Pedro Strop	CIN	46	Home white Black Lives Matter patch United For Change patch	2020/07/24 reds46 Pedro Strop",
"2020/07/24	Nate Jones	CIN	57	Home white Black Lives Matter patch United For Change patch	2020/07/24 reds57 Nate Jones",
"2020/07/24	Matt Davidson	CIN	64	Home white Black Lives Matter patch United For Change patch	2020/07/24 reds64 Matt Davidson",
"2020/07/24	Daniel Johnson	CLE	23	Home navy red brim hat Black Lives Matter patch United For Change patch	2020/07/24 indians23 Daniel Johnson",
"2020/07/24	Domingo Santana	CLE	24	Home navy red brim hat Black Lives Matter patch United For Change patch	2020/07/24 indians24 Domingo Santana",
"2020/07/24	Christian Arroyo	CLE	26	Home navy red brim hat Black Lives Matter patch United For Change patch	2020/07/24 indians26 Christian Arroyo",
"2020/07/24	Cam Hill	CLE	27	Home navy red brim hat Black Lives Matter patch United For Change patch	2020/07/24 indians27 Cam Hill",
"2020/07/24	Dominic Leone	CLE	53	Home navy red brim hat Black Lives Matter patch United For Change patch	2020/07/24 indians53 Dominic Leone",
"2020/07/24	James Karinchak	CLE	99	Home navy red brim hat Black Lives Matter patch United For Change patch	2020/07/24 indians99 James Karinchak",
"2020/07/24	Drew Butera	COL	6	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies6 Drew Butera",
"2020/07/24	Chris Owings	COL	12	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies12 Chris Owings",
"2020/07/24	Sam Hilliard	COL	22	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies22 Sam Hilliard",
"2020/07/24	Matt Kemp	COL	25	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies25 Matt Kemp",
"2020/07/24	Elias Diaz	COL	35	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies35 Elias Diaz",
"2020/07/24	Tyler Kinley	COL	40	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies40 Tyler Kinley",
"2020/07/24	Daniel Bard	COL	52	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies52 Daniel Bard",
"2020/07/24	Ashton Goudeau	COL	56	Road purple Black Lives Matter patch United For Change patch	2020/07/24 rockies56 Ashton Goudeau",
"2020/07/24	Jordy Mercer	DET	9	Road gray Black Lives Matter patch United For Change patch Al Kaline 6 memorial patch	2020/07/24 tigers9 Jordy Mercer",
"2020/07/24	Kyle Funkhouser	DET	36	Road gray Black Lives Matter patch United For Change patch Al Kaline 6 memorial patch	2020/07/24 tigers36 Kyle Funkhouser",
"2020/07/24	Beau Burrows	DET	37	Road gray Black Lives Matter patch United For Change patch Al Kaline 6 memorial patch	2020/07/24 tigers37 Beau Burrows",
"2020/07/24	Dario Agrazal	DET	72	Road gray Black Lives Matter patch United For Change patch Al Kaline 6 memorial patch	2020/07/24 tigers72 Dario Agrazal",
"2020/07/24	Taylor Jones	HOU	28	Home white Black Lives Matter patch United For Change patch	2020/07/24 astros28 Taylor Jones",
"2020/07/24	Abraham Toro	HOU	31	Home white Black Lives Matter patch United For Change patch	2020/07/24 astros31 Abraham Toro",
"2020/07/24	Cristian Javier	HOU	53	Home white Black Lives Matter patch United For Change patch	2020/07/24 astros53 Cristian Javier",
"2020/07/24	Enoli Paredes	HOU	60	Home white Black Lives Matter patch United For Change patch	2020/07/24 astros60 Enoli Paredes",
"2020/07/24	Blake Taylor	HOU	62	Home white Black Lives Matter patch United For Change patch	2020/07/24 astros62 Blake Taylor",
"2020/07/24	Oscar Hernandez	KCR	18	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals18 Oscar Hernandez",
"2020/07/24	Franchy Cordero	KCR	19	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals19 Franchy Cordero",
"2020/07/24	Greg Holland	KCR	35	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals35 Greg Holland",
"2020/07/24	Trevor Rosenthal	KCR	40	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals40 Trevor Rosenthal",
"2020/07/24	Brady Singer	KCR	51	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals51 Brady Singer",
"2020/07/24	Tyler Zuber	KCR	53	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals53 Tyler Zuber",
"2020/07/24	Ronald Bolanos	KCR	54	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals54 Ronald Bolanos",
"2020/07/24	Foster Griffin	KCR	60	Road gray Black Lives Matter patch United For Change patch David Glass DG memorial patch	2020/07/24 royals60 Foster Griffin",
"2020/07/24	Justin Upton	LAA	10	Road gray Black Lives Matter patch United For Change patch	2020/07/24 angels10 Justin Upton",
"2020/07/24	Jacob Barnes	LAA	40	Road gray Black Lives Matter patch United For Change patch	2020/07/24 angels40 Jacob Barnes",
"2020/07/24	Ryan Buchter	LAA	46	Road gray Black Lives Matter patch United For Change patch	2020/07/24 angels46 Ryan Buchter",
"2020/07/24	Mike Mayers	LAA	60	Road gray Black Lives Matter patch United For Change patch	2020/07/24 angels60 Mike Mayers",
"2020/07/24	Hoby Milner	LAA	61	Road gray Black Lives Matter patch United For Change patch	2020/07/24 angels61 Hoby Milner",
"2020/07/24	Sean Rodriguez	MIA	13	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins13 Sean Rodriguez",
"2020/07/24	Brandon Kintzler	MIA	27	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins27 Brandon Kintzler",
"2020/07/24	Brad Boxberger	MIA	33	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins33 Brad Boxberger",
"2020/07/24	Stephen Tarpley	MIA	37	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins37 Stephen Tarpley",
"2020/07/24	Sterling Sharp	MIA	56	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins56 Sterling Sharp",
"2020/07/24	Nick Neidert	MIA	59	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins59 Nick Neidert",
"2020/07/24	Jordan Holloway	MIA	78	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins78 Jordan Holloway",
"2020/07/24	Alex Vesia	MIA	96	Road black Black Lives Matter patch United For Change patch	2020/07/24 marlins96 Alex Vesia",
"2020/07/24	Brock Holt	MIL	11	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers11 Brock Holt",
"2020/07/24	Logan Morrison	MIL	21	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers21 Logan Morrison",
"2020/07/24	Bobby Wahl	MIL	31	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers31 Bobby Wahl",
"2020/07/24	Mike Morin	MIL	47	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers47 Mike Morin",
"2020/07/24	Justin Grimm	MIL	52	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers52 Justin Grimm",
"2020/07/24	J.P. Feyereisen	MIL	54	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers54 J.P. Feyereisen",
"2020/07/24	Eric Yardley	MIL	57	Road navy Black Lives Matter patch United For Change patch 50th season patch	2020/07/24 brewers57 Eric Yardley",
"2020/07/24	Mitch Garver	MIN	8	Road gray Ryan Costello RC memorial patch Black Lives Matter patch United For Change patch 60th season patch	2020/07/24 twins8 Mitch Garver",
"2020/07/24	Kenta Maeda	MIN	18	Road gray Ryan Costello RC memorial patch Black Lives Matter patch United For Change patch 60th season patch	2020/07/24 twins18 Kenta Maeda",
"2020/07/24	Matt Wisler	MIN	37	Road gray Ryan Costello RC memorial patch Black Lives Matter patch United For Change patch 60th season patch	2020/07/24 twins37 Matt Wisler",
"2020/07/24	Aaron Whitefield	MIN	58	Road gray Ryan Costello RC memorial patch Black Lives Matter patch United For Change patch 60th season patch	2020/07/24 twins58 Aaron Whitefield",
"2020/07/24	Dominic Smith	NYM	2	Home white Black Lives Matter patch United For Change patch	2020/07/24 mets2 Dominic Smith",
"2020/07/24	Eduardo Nunez	NYM	12	Home white Black Lives Matter patch United For Change patch	2020/07/24 mets12 Eduardo Nunez",
"2020/07/24	Chasen Shreve	NYM	47	Home white Black Lives Matter patch United For Change patch	2020/07/24 mets47 Chasen Shreve",
"2020/07/24	Andres Gimenez	NYM	60	Home white Black Lives Matter patch United For Change patch	2020/07/24 mets60 Andres Gimenez",
"2020/07/24	Hunter Strickland	NYM	71	Home white Black Lives Matter patch United For Change patch	2020/07/24 mets71 Hunter Strickland",
"2020/07/24	Franklin Barreto	OAK	4	Home white Black Lives Matter patch United For Change patch	2020/07/24 athletics4 Franklin Barreto",
"2020/07/24	Vimael Machin	OAK	39	Home white Black Lives Matter patch United For Change patch	2020/07/24 athletics39 Vimael Machin",
"2020/07/24	Burch Smith	OAK	46	Home white Black Lives Matter patch United For Change patch	2020/07/24 athletics46 Burch Smith",
"2020/07/24	Jordan Weems	OAK	70	Home white Black Lives Matter patch United For Change patch	2020/07/24 athletics70 Jordan Weems",
"2020/07/24	Phil Gosselin	PHI	8	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies8 Phil Gosselin",
"2020/07/24	Neil Walker	PHI	12	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies12 Neil Walker",
"2020/07/24	Kyle Garlick	PHI	23	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies23 Kyle Garlick",
"2020/07/24	Reggie McClain	PHI	39	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies39 Reggie McClain",
"2020/07/24	Deolis Guerra	PHI	57	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies57 Deolis Guerra",
"2020/07/24	Ramon Rosso	PHI	60	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies60 Ramon Rosso",
"2020/07/24	Trevor Kelley	PHI	67	Home white Black Lives Matter patch United For Change patch	2020/07/24 phillies67 Trevor Kelley",
"2020/07/24	Jarrod Dyson	PIT	6	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates6 Jarrod Dyson",
"2020/07/24	John Ryan Murphy	PIT	18	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates18 John Ryan Murphy",
"2020/07/24	Derek Holland	PIT	45	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates45 Derek Holland",
"2020/07/24	Michael Feliz	PIT	49	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates49 Michael Feliz",
"2020/07/24	Robbie Erlin	PIT	56	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates56 Robbie Erlin",
"2020/07/24	Phillip Evans	PIT	64	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates64 Phillip Evans",
"2020/07/24	JT Brubaker	PIT	65	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates65 JT Brubaker",
"2020/07/24	Nik Turley	PIT	71	Road black Black Lives Matter patch United For Change patch	2020/07/24 pirates71 Nik Turley",
"2020/07/24	Jorge Mateo	SDP	3	Home white Black Lives Matter patch United For Change patch	2020/07/24 padres3 Jorge Mateo",
"2020/07/24	Emilio Pagan	SDP	14	Home white Black Lives Matter patch United For Change patch	2020/07/24 padres14 Emilio Pagan",
"2020/07/24	Edward Olivares	SDP	24	Home white Black Lives Matter patch United For Change patch	2020/07/24 padres24 Edward Olivares",
"2020/07/24	Tim Hill	SDP	25	Home white Black Lives Matter patch United For Change patch	2020/07/24 padres25 Tim Hill",
"2020/07/24	Jose Marmolejos	SEA	26	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners26 Jose Marmolejos",
"2020/07/24	Nestor Cortes	SEA	30	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners30 Nestor Cortes",
"2020/07/24	Bryan Shaw	SEA	36	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners36 Bryan Shaw",
"2020/07/24	Anthony Misiewicz	SEA	38	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners38 Anthony Misiewicz",
"2020/07/24	Taylor Williams	SEA	47	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners47 Taylor Williams",
"2020/07/24	Nick Margevicius	SEA	52	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners52 Nick Margevicius",
"2020/07/24	Joe Hudson	SEA	57	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners57 Joe Hudson",
"2020/07/24	Taijuan Walker	SEA	99	Road navy Black Lives Matter patch United For Change patch	2020/07/24 mariners99 Taijuan Walker",
"2020/07/24	Austin Dean	STL	0	Home white Black Lives Matter patch United For Change patch	2020/07/24 cardinals0 Austin Dean",
"2020/07/24	Kodi Whitley	STL	38	Home white Black Lives Matter patch United For Change patch	2020/07/24 cardinals38 Kodi Whitley",
"2020/07/24	Manuel Margot	TBR	13	Home white Black Lives Matter patch United For Change patch	2020/07/24 rays13 Manuel Margot",
"2020/07/24	Aaron Loup	TBR	15	Home white Black Lives Matter patch United For Change patch	2020/07/24 rays15 Aaron Loup",
"2020/07/24	Pete Fairbanks	TBR	29	Home white Black Lives Matter patch United For Change patch	2020/07/24 rays29 Pete Fairbanks",
"2020/07/24	Kevan Smith	TBR	44	Home white Black Lives Matter patch United For Change patch	2020/07/24 rays44 Kevan Smith",
"2020/07/24	Ryan Thompson	TBR	81	Home white Black Lives Matter patch United For Change patch	2020/07/24 rays81 Ryan Thompson",
"2020/07/24	Rob Refsnyder	TEX	14	Home white blue hat Black Lives Matter patch United For Change patch Globe Life Field inaugural season patch	2020/07/24 rangers14 Rob Refsnyder",
"2020/07/24	Leody Taveras	TEX	65	Home white blue hat Black Lives Matter patch United For Change patch Globe Life Field inaugural season patch	2020/07/24 rangers65 Leody Taveras",
"2020/07/24	Joe Panik	TOR	2	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays2 Joe Panik",
"2020/07/24	Santiago Espinal	TOR	5	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays5 Santiago Espinal",
"2020/07/24	Thomas Hatch	TOR	31	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays31 Thomas Hatch",
"2020/07/24	A.J. Cole	TOR	36	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays36 A.J. Cole",
"2020/07/24	Rafael Dolis	TOR	41	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays41 Rafael Dolis",
"2020/07/24	Brian Moran	TOR	48	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays48 Brian Moran",
"2020/07/24	Anthony Bass	TOR	52	Road gray Black Lives Matter patch United For Change patch Tony Fernandez 1 memorial patch	2020/07/24 bluejays52 Anthony Bass",
"2020/07/25	Jake Cronenworth	SDP	9	Home white	2020/07/25 padres9 Jake Cronenworth",
"2020/07/26	Zack Godley	BOS	68	Home white	2020/07/26 redsox68 Zack Godley",
"2020/07/26	Tyler Stephenson	CIN	37	Home red	2020/07/26 reds37 Tyler Stephenson",
"2020/07/26	Tejay Antone	CIN	70	Home red	2020/07/26 reds70 Tejay Antone",
"2020/07/26	Carson Fulmer	DET	60	Road gray Al Kaline 6 memorial patch	2020/07/26 tigers60 Carson Fulmer",
"2020/07/26	Brandon Bailey	HOU	63	Home navy	2020/07/26 astros63 Brandon Bailey",
"2020/07/26	Nick Nelson	NYY	79	Road gray Hank Steinbrenner HGS memorial patch	2020/07/26 yankees79 Nick Nelson",
"2020/07/26	Brooks Kriske	NYY	82	Road gray Hank Steinbrenner HGS memorial patch	2020/07/26 yankees82 Brooks Kriske",
"2020/07/27	Ryan Goins	CHW	18	Road gray Ed Farmer FARMIO memorial patch	2020/07/27 whitesox18 Ryan Goins",
"2020/07/27	Anthony Castro	DET	38	Home white Al Kaline 6 memorial patch	2020/07/27 tigers38 Anthony Castro",
"2020/07/27	Nivaldo Rodriguez	HOU	68	Home white	2020/07/27 astros68 Nivaldo Rodriguez",
"2020/07/27	Josh Harrison	WSN	5	Home white Championship 2019 World Series champions patch	2020/07/27 nationals5 Josh Harrison",
"2020/07/28	Beau Taylor	CLE	46	Home red	2020/07/28 indians46 Beau Taylor",
"2020/07/28	Andre Scrubb	HOU	70	Home white	2020/07/28 astros70 Andre Scrubb",
"2020/07/28	Nick Heath	KCR	0	Road gray David Glass DG memorial patch	2020/07/28 royals0 Nick Heath",
"2020/07/28	David Peterson	NYM	77	Road royal	2020/07/28 mets77 David Peterson",
"2020/07/28	Miguel Del Pozo	PIT	63	Home black	2020/07/28 pirates63 Miguel Del Pozo",
"2020/07/28	Joseph Odom	SEA	54	Road navy	2020/07/28 mariners54 Joseph Odom",
"2020/07/28	Chadwick Tromp	SFG	14	Home cream 20 at 24 patch	2020/07/28 giants14 Chadwick Tromp",
"2020/07/29	Scott Schebler	ATL	45	Home white	2020/07/29 braves45 Scott Schebler",
"2020/07/29	Chris Mazza	BOS	22	Road navy	2020/07/29 redsox22 Chris Mazza",
"2020/07/29	Matt Foster	CHW	63	Road black Ed Farmer FARMIO memorial patch	2020/07/29 whitesox63 Matt Foster",
"2020/07/29	Ryan Cordell	NYM	18	Home white	2020/07/29 mets18 Ryan Cordell",
"2020/07/29	Jake Woodford	STL	40	Road gray	2020/07/29 cardinals40 Jake Woodford",
"2020/07/29	Nate Pearson	TOR	24	Home white Tony Fernandez 1 memorial patch	2020/07/29 bluejays24 Nate Pearson",
"2020/07/30	Daulton Varsho	ARI	12	Home white sand accents	2020/07/30 dbacks12 Daulton Varsho",
"2020/07/30	Colin Rea	CHC	20	Home white	2020/07/30 cubs20 Colin Rea",
"2020/07/30	Brian Dozier	NYM	15	Home white	2020/07/30 mets15 Brian Dozier",
"2020/07/31	Thomas Eshelman	BAL	73	Home black	2020/07/31 orioles73 Thomas Eshelman",
"2020/07/31	Nick Madrigal	CHW	1	Road gray Ed Farmer FARMIO memorial patch	2020/07/31 whitesox1 Nick Madrigal",
"2020/07/31	Kris Bubic	KCR	50	Home white David Glass DG memorial patch	2020/07/31 royals50 Kris Bubic",
"2020/07/31	Kyle Keller	LAA	68	Home red	2020/07/31 angels68 Kyle Keller",
"2020/07/31	Victor Gonzalez	LAD	81	Road gray Dodgers	2020/07/31 dodgers81 Victor Gonzalez",
"2020/07/31	Greg Bird	TEX	20	Road royal Globe Life Field inaugural season patch	2020/07/31 rangers20 Greg Bird",
"2020/07/31	Jimmy Herget	TEX	64	Road royal Globe Life Field inaugural season patch	2020/07/31 rangers64 Jimmy Herget",
"2020/08/01	Andrew Young	ARI	14	Home black	2020/08/01 dbacks14 Andrew Young",
"2020/08/01	Chris Rusin	ATL	52	Home white	2020/08/01 braves52 Chris Rusin",
"2020/08/01	Bryan Holaday	BAL	36	Home orange	2020/08/01 orioles36 Bryan Holaday",
"2020/08/01	Yermin Mercedes	CHW	49	Road black Ed Farmer FARMIO memorial patch	2020/08/01 whitesox49 Yermin Mercedes",
"2020/08/01	Carlos Sanabria	HOU	71	Road orange	2020/08/01 astros71 Carlos Sanabria",
"2020/08/01	Mitch White	LAD	66	Road gray Dodgers	2020/08/01 dodgers66 Mitch White",
"2020/08/01	Franklyn Kilome	NYM	66	Road gray	2020/08/01 mets66 Franklyn Kilome",
"2020/08/02	Justin Steele	CHC	35	Home white	2020/08/02 cubs35 Justin Steele",
"2020/08/02	Humberto Castellanos	HOU	72	Road gray	2020/08/02 astros72 Humberto Castellanos",
"2020/08/02	Jared Hughes	NYM	35	Road royal	2020/08/02 mets35 Jared Hughes",
"2020/08/02	Sam Howard	PIT	54	Road gray	2020/08/02 pirates54 Sam Howard",
"2020/08/02	Cody Ponce	PIT	60	Road gray	2020/08/02 pirates60 Cody Ponce",
"2020/08/02	Jerad Eickhoff	SDP	45	Road brown	2020/08/02 padres45 Jerad Eickhoff",
"2020/08/02	Andrew Triggs	SFG	66	Home cream 20 at 24 patch	2020/08/02 giants66 Andrew Triggs",
"2020/08/02	Anderson Tejeda	TEX	71	Road gray Globe Life Field inaugural season patch	2020/08/02 rangers71 Anderson Tejeda",
"2020/08/03	Mark Mathias	MIL	13	Home cream 50th season patch	2020/08/03 brewers13 Mark Mathias",
"2020/08/03	Caleb Thielbar	MIN	72	Home white 60th season patch	2020/08/03 twins72 Caleb Thielbar",
"2020/08/03	Ali Sanchez	NYM	70	Road gray	2020/08/03 mets70 Ali Sanchez",
"2020/08/03	Abraham Almonte	SDP	16	Home white	2020/08/03 padres16 Abraham Almonte",
"2020/08/04	Huascar Ynoa	ATL	66	Home white	2020/08/04 braves66 Huascar Ynoa",
"2020/08/04	Brady Lail	CHW	67	Road black Ed Farmer FARMIO memorial patch	2020/08/04 whitesox67 Brady Lail",
"2020/08/04	Jo Adell	LAA	59	Road gray	2020/08/04 angels59 Jo Adell",
"2020/08/04	Monte Harrison	MIA	4	Road gray	2020/08/04 marlins4 Monte Harrison",
"2020/08/04	Matt Joyce	MIA	7	Road gray	2020/08/04 marlins7 Matt Joyce",
"2020/08/04	Logan Forsythe	MIA	11	Road gray	2020/08/04 marlins11 Logan Forsythe",
"2020/08/04	Richard Bleier	MIA	35	Road gray	2020/08/04 marlins35 Richard Bleier",
"2020/08/04	Ryan Lavarnway	MIA	36	Road gray	2020/08/04 marlins36 Ryan Lavarnway",
"2020/08/04	James Hoyt	MIA	39	Road gray	2020/08/04 marlins39 James Hoyt",
"2020/08/04	Nick Vincent	MIA	44	Road gray	2020/08/04 marlins44 Nick Vincent",
"2020/08/04	Mike Morin	MIA	48	Road gray	2020/08/04 marlins48 Mike Morin",
"2020/08/04	Justin Shafer	MIA	51	Road gray	2020/08/04 marlins51 Justin Shafer",
"2020/08/04	Josh D. Smith	MIA	54	Road gray	2020/08/04 marlins54 Josh D. Smith",
"2020/08/04	Josh A. Smith	MIA	58	Road gray	2020/08/04 marlins58 Josh A. Smith",
"2020/08/04	Brian Moran	MIA	60	Road gray	2020/08/04 marlins60 Brian Moran",
"2020/08/04	Eddy Alvarez	MIA	65	Road gray	2020/08/04 marlins65 Eddy Alvarez",
"2020/08/04	Daniel Castano	MIA	72	Road gray	2020/08/04 marlins72 Daniel Castano",
"2020/08/04	Billy Hamilton	NYM	21	Road gray	2020/08/04 mets21 Billy Hamilton",
"2020/08/04	James Kaprielian	OAK	56	Home kelly green	2020/08/04 athletics56 James Kaprielian",
"2020/08/04	Luis Patino	SDP	62	Home white	2020/08/04 padres62 Luis Patino",
"2020/08/04	Joey Gerber	SEA	59	Home white	2020/08/04 mariners59 Joey Gerber",
"2020/08/04	Brian O'Grady	TBR	31	Home white	2020/08/04 rays31 Brian O'Grady",
"2020/08/05	Zack McKinstry	LAD	8	Road gray Dodgers	2020/08/05 dodgers8 Zack McKinstry",
"2020/08/06	Nick Tropeano	NYY	35	Road gray Hank Steinbrenner HGS memorial patch	2020/08/06 yankees35 Nick Tropeano",
"2020/08/07	Ryan Castellani	COL	60	Road gray	2020/08/07 rockies60 Ryan Castellani",
"2020/08/07	Humberto Mejia	MIA	77	Road black	2020/08/07 marlins77 Humberto Mejia",
"2020/08/07	Sean Gilmartin	TBR	85	Home white	2020/08/07 rays85 Sean Gilmartin",
"2020/08/08	Keegan Akin	BAL	45	Road orange	2020/08/08 orioles45 Keegan Akin",
"2020/08/08	Drew Anderson	CHW	53	Home white Ed Farmer FARMIO memorial patch	2020/08/08 whitesox53 Drew Anderson",
"2020/08/08	Zack Burdi	CHW	62	Home white Ed Farmer FARMIO memorial patch	2020/08/08 whitesox62 Zack Burdi",
"2020/08/08	Pat Venditte	MIA	46	Road black	2020/08/08 marlins46 Pat Venditte",
"2020/08/08	Erik Kratz	NYY	38	Road gray Hank Steinbrenner HGS memorial patch	2020/08/08 yankees38 Erik Kratz",
"2020/08/08	Albert Abreu	NYY	84	Road gray Hank Steinbrenner HGS memorial patch	2020/08/08 yankees84 Albert Abreu",
"2020/08/08	Nick Mears	PIT	70	Home black	2020/08/08 pirates70 Nick Mears",
"2020/08/09	Robbie Erlin	ATL	49	Road gray	2020/08/09 braves49 Robbie Erlin",
"2020/08/09	Cory Gearrin	MIN	38	Road navy 60th season patch	2020/08/09 twins38 Cory Gearrin",
"2020/08/09	Spencer Howard	PHI	48	Home powder	2020/08/09 phillies48 Spencer Howard",
"2020/08/09	Jarlin Garcia	SFG	76	Road gray 20 at 24 patch	2020/08/09 giants76 Jarlin Garcia",
"2020/08/09	John Curtiss	TBR	84	Home powder throwback hat	2020/08/09 rays84 John Curtiss",
"2020/08/10	Jeremy Beasley	ARI	59	Road gray	2020/08/10 dbacks59 Jeremy Beasley",
"2020/08/11	Robert Stock	BOS	79	Home white	2020/08/11 redsox79 Robert Stock",
"2020/08/11	Brooks Raley	HOU	58	Home white	2020/08/11 astros58 Brooks Raley",
"2020/08/11	Connor Brogdon	PHI	75	Home white	2020/08/11 phillies75 Connor Brogdon",
"2020/08/11	Derek Dietrich	TEX	32	Home white red hat Globe Life Field inaugural season patch	2020/08/11 rangers32 Derek Dietrich",
"2020/08/11	Wes Benjamin	TEX	75	Home white red hat Globe Life Field inaugural season patch	2020/08/11 rangers75 Wes Benjamin",
"2020/08/12	Jeison Guzman	KCR	75	Road gray David Glass DG memorial patch	2020/08/12 royals75 Jeison Guzman",
"2020/08/12	Trevor Cahill	SFG	53	Road gray 20 at 24 patch	2020/08/12 giants53 Trevor Cahill",
"2020/08/13	Kyle Hart	BOS	81	Home white	2020/08/13 redsox81 Kyle Hart",
"2020/08/13	Drew Rasmussen	MIL	43	Road navy 50th season patch	2020/08/13 brewers43 Drew Rasmussen",
"2020/08/13	Angel Perdomo	MIL	47	Road navy 50th season patch	2020/08/13 brewers47 Angel Perdomo",
"2020/08/13	Andrew Knapp	PHI	7	Home powder	2020/08/13 phillies7 Andrew Knapp",
"2020/08/13	Alec Bohm	PHI	28	Home powder	2020/08/13 phillies28 Alec Bohm",
"2020/08/13	Brad Miller	STL	15	Road gray	2020/08/13 cardinals15 Brad Miller",
"2020/08/13	Max Schrock	STL	55	Road gray	2020/08/13 cardinals55 Max Schrock",
"2020/08/13	Roel Ramirez	STL	77	Road gray	2020/08/13 cardinals77 Roel Ramirez",
"2020/08/13	Seth Romero	WSN	96	Road gray 2019 World Series champions patch	2020/08/13 nationals96 Seth Romero",
"2020/08/14	Tyler Thornburg	CIN	48	Home white	2020/08/14 reds48 Tyler Thornburg",
"2020/08/14	JoJo Romero	PHI	79	Home white	2020/08/14 phillies79 JoJo Romero",
"2020/08/14	Brady Lail	SEA	62	Road navy	2020/08/14 mariners62 Brady Lail",
"2020/08/14	Juan Nicasio	TEX	40	Road royal Globe Life Field inaugural season patch	2020/08/14 rangers40 Juan Nicasio",
"2020/08/14	Luis Garcia	WSN	62	Road gray 2019 World Series champions patch	2020/08/14 nationals62 Luis Garcia",
"2020/08/14	Dakota Bacus	WSN	71	Road gray 2019 World Series champions patch	2020/08/14 nationals71 Dakota Bacus",
"2020/08/15	Jorge Lopez	BAL	48	Home orange	2020/08/15 orioles48 Jorge Lopez",
"2020/08/15	Bernardo Flores	CHW	67	Home black Ed Farmer FARMIO memorial patch	2020/08/15 whitesox67 Bernardo Flores",
"2020/08/15	Scott Blewett	KCR	64	Road gray David Glass DG memorial patch	2020/08/15 royals64 Scott Blewett",
"2020/08/15	Anthony Bemboom	LAA	12	Home white	2020/08/15 angels12 Anthony Bemboom",
"2020/08/15	Keibert Ruiz	LAD	25	Road gray Los Angeles	2020/08/15 dodgers25 Keibert Ruiz",
"2020/08/15	Lewin Diaz	MIA	68	Home black	2020/08/15 marlins68 Lewin Diaz",
"2020/08/15	Ildemaro Vargas	MIN	4	Home navy 60th season patch	2020/08/15 twins4 Ildemaro Vargas",
"2020/08/15	Ljay Newsome	SEA	74	Road gray	2020/08/15 mariners74 Ljay Newsome",
"2020/08/15	Dylan Carlson	STL	3	Road gray	2020/08/15 cardinals3 Dylan Carlson",
"2020/08/15	John Nogowski	STL	34	Road gray	2020/08/15 cardinals34 John Nogowski",
"2020/08/15	Seth Elledge	STL	61	Road gray	2020/08/15 cardinals61 Seth Elledge",
"2020/08/15	Ricardo Sanchez	STL	64	Road gray	2020/08/15 cardinals64 Ricardo Sanchez",
"2020/08/15	Rob Kaminsky	STL	67	Road gray	2020/08/15 cardinals67 Rob Kaminsky",
"2020/08/16	Jason Adam	CHC	60	Home white Negro Leagues Centennial	2020/08/16 cubs60 Jason Adam",
"2020/08/17	Tyson Miller	CHC	72	Home white	2020/08/17 cubs72 Tyson Miller",
"2020/08/17	Luis Gonzalez	CHW	37	Home white Ed Farmer FARMIO memorial patch	2020/08/17 whitesox37 Luis Gonzalez",
"2020/08/17	Casey Mize	DET	12	Road gray Al Kaline 6 memorial patch	2020/08/17 tigers12 Casey Mize",
"2020/08/17	Isaac Paredes	DET	19	Road gray Al Kaline 6 memorial patch	2020/08/17 tigers19 Isaac Paredes",
"2020/08/17	Andrew Knapp	PHI	5	Road gray	2020/08/17 phillies5 Andrew Knapp",
"2020/08/17	Tyler Bashlor	PIT	67	Home white Negro Leagues Centennial patch	2020/08/17 pirates67 Tyler Bashlor",
"2020/08/17	Nabil Crismatt	STL	74	Road gray	2020/08/17 cardinals74 Nabil Crismatt",
"2020/08/17	Ryan Meisinger	STL	84	Road gray	2020/08/17 cardinals84 Ryan Meisinger",
"2020/08/18	Cristian Pache	ATL	14	Home white	2020/08/18 braves14 Cristian Pache",
"2020/08/18	Ramon Urias	BAL	87	Home white	2020/08/18 orioles87 Ramon Urias",
"2020/08/18	Hernan Perez	CHC	41	Home white	2020/08/18 cubs41 Hernan Perez",
"2020/08/18	Tarik Skubal	DET	29	Road gray Al Kaline 6 memorial patch	2020/08/18 tigers29 Tarik Skubal",
"2020/08/18	Brett Eibner	MIA	52	Home white	2020/08/18 marlins52 Brett Eibner",
"2020/08/18	Brandon Leibrandt	MIA	86	Home white	2020/08/18 marlins86 Brandon Leibrandt",
"2020/08/18	Brandon Waddell	PIT	68	Home white Negro Leagues Centennial patch	2020/08/18 pirates68 Brandon Waddell",
"2020/08/18	Jesus Cruz	STL	86	Road gray	2020/08/18 cardinals86 Jesus Cruz",
"2020/08/18	Luis Garcia	TEX	45	Home white blue hat Globe Life Field inaugural season patch	2020/08/18 rangers45 Luis Garcia",
"2020/08/19	Matt Grace	ARI	33	Road red snake hat	2020/08/19 dbacks33 Matt Grace",
"2020/08/19	Christian Arroyo	BOS	39	Home white	2020/08/19 redsox39 Christian Arroyo",
"2020/08/19	Dane Dunning	CHW	51	Home white Ed Farmer FARMIO memorial patch	2020/08/19 whitesox51 Dane Dunning",
"2020/08/19	Robel Garcia	CIN	35	Road red	2020/08/19 reds35 Robel Garcia",
"2020/08/19	Jorge Bonifacio	DET	57	Road gray Al Kaline 6 memorial patch	2020/08/19 tigers57 Jorge Bonifacio",
"2020/08/19	Matt Harvey	KCR	33	Home powder David Glass DG memorial patch	2020/08/19 royals33 Matt Harvey",
"2020/08/19	Sam Haggerty	SEA	28	Home navy	2020/08/19 mariners28 Sam Haggerty",
"2020/08/19	Johan Oviedo	STL	59	Road gray	2020/08/19 cardinals59 Johan Oviedo",
"2020/08/19	Julian Merryweather	TOR	67	Road powder Tony Fernandez 1 memorial patch	2020/08/19 bluejays67 Julian Merryweather",
"2020/08/20	Cionel Perez	HOU	52	Road gray	2020/08/20 astros52 Cionel Perez",
"2020/08/20	Ryan Jeffers	MIN	39	Home red 60th season patch	2020/08/20 twins39 Ryan Jeffers",
"2020/08/20	Miguel Yajure	NYY	89	Home white Hank Steinbrenner HGS memorial patch	2020/08/20 yankees89 Miguel Yajure",
"2020/08/20	Joey Bart	SFG	21	Home cream 20 at 24 patch	2020/08/20 giants21 Joey Bart",
"2020/08/20	Yadiel Rivera	TEX	33	Road gray Globe Life Field inaugural season patch	2020/08/20 rangers33 Yadiel Rivera",
"2020/08/20	Kyle Cody	TEX	73	Road gray Globe Life Field inaugural season patch	2020/08/20 rangers73 Kyle Cody",
"2020/08/21	Jesus Sanchez	MIA	76	Road gray	2020/08/21 marlins76 Jesus Sanchez",
"2020/08/21	David Hale	PHI	41	Road gray	2020/08/21 phillies41 David Hale",
"2020/08/21	Heath Hembree	PHI	43	Road gray	2020/08/21 phillies43 Heath Hembree",
"2020/08/21	Brandon Workman	PHI	44	Road gray	2020/08/21 phillies44 Brandon Workman",
"2020/08/21	Aaron Fletcher	SEA	81	Home teal	2020/08/21 mariners81 Aaron Fletcher",
"2020/08/22	Mason Williams	BAL	38	Home orange	2020/08/22 orioles38 Mason Williams",
"2020/08/22	Triston McKenzie	CLE	26	Home red	2020/08/22 indians26 Triston McKenzie",
"2020/08/22	Jesus Tinoco	MIA	41	Road gray	2020/08/22 marlins41 Jesus Tinoco",
"2020/08/22	Sixto Sanchez	MIA	73	Road gray	2020/08/22 marlins73 Sixto Sanchez",
"2020/08/22	Jace Peterson	MIL	14	Road gray 50th season patch	2020/08/22 brewers14 Jace Peterson",
"2020/08/22	Danny Coulombe	MIN	53	Road gray 60th season patch	2020/08/22 twins53 Danny Coulombe",
"2020/08/22	Wil Crowe	WSN	57	Home white Championship 2019 World Series champions patch	2020/08/22 nationals57 Wil Crowe",
"2020/08/23	Ian Miller	CHC	6	Home white	2020/08/23 cubs6 Ian Miller",
"2020/08/23	Chase De Jong	HOU	69	Road orange	2020/08/23 astros69 Chase De Jong",
"2020/08/23	Brian Navarreto	MIA	87	Road gray	2020/08/23 marlins87 Brian Navarreto",
"2020/08/23	Nick Tropeano	PIT	72	Home white	2020/08/23 pirates72 Nick Tropeano",
"2020/08/23	Edgar Garcia	TBR	58	Home powder throwback hat	2020/08/23 rays58 Edgar Garcia",
"2020/08/23	Josh Fleming	TBR	61	Home powder throwback hat	2020/08/23 rays61 Josh Fleming",
"2020/08/24	Riley Smith	ARI	46	Home white sand accents	2020/08/24 dbacks46 Riley Smith",
"2020/08/24	Jonah Heim	OAK	37	Road green	2020/08/24 athletics37 Jonah Heim",
"2020/08/24	Travis Bergen	TOR	79	Road royal Tony Fernandez 1 memorial patch	2020/08/24 bluejays79 Travis Bergen",
"2020/08/24	Ben Braymer	WSN	70	Home navy 2019 World Series champions patch	2020/08/24 nationals70 Ben Braymer",
"2020/08/25	Ian Anderson	ATL	48	Home red	2020/08/25 braves48 Ian Anderson",
"2020/08/25	Jesse Biddle	CIN	53	Road gray	2020/08/25 reds53 Jesse Biddle",
"2020/08/25	Trevor Rogers	MIA	95	Road black	2020/08/25 marlins95 Trevor Rogers",
"2020/08/25	Patrick Mazeika	NYM	76	Home royal	2020/08/25 mets76 Patrick Mazeika",
"2020/08/25	Juan Lagares	NYM	87	Home royal	2020/08/25 mets87 Juan Lagares",
"2020/08/26	Mark Payton	CIN	34	Road red	2020/08/26 reds34 Mark Payton",
"2020/08/26	Jose Garcia	CIN	38	Road red	2020/08/26 reds38 Jose Garcia",
"2020/08/26	Juan Lagares	NYM	15	Home white	2020/08/26 mets15 Juan Lagares",
"2020/08/26	Ryan Sherriff	TBR	71	Home navy	2020/08/26 rays71 Ryan Sherriff",
"2020/08/27	Cesar Valdez	BAL	62	Road black Jackie Robinson Day	2020/08/27 orioles62 Cesar Valdez",
"2020/08/27	Gavin Lux	LAD	9	Road gray Dodgers Until There's a Cure patch	2020/08/27 dodgers9 Gavin Lux",
"2020/08/27	Will Craig	PIT	31	Road black	2020/08/27 pirates31 Will Craig",
"2020/08/27	Luis Alexander Basabe	SFG	61	Home black black hat Until There's a Cure patch 20 at 24 patch	2020/08/27 giants61 Luis Alexander Basabe",
"2020/08/27	Daniel Vogelbach	TOR	20	Home royal Jackie Robinson Day	2020/08/27 bluejays20 Daniel Vogelbach",
"2020/08/28	Jarrod Dyson	CHW	32	Home black Jackie Robinson Day	2020/08/28 whitesox32 Jarrod Dyson",
"2020/08/28	Jose Quijada	LAA	65	Home red Jackie Robinson Day	2020/08/28 angels65 Jose Quijada",
"2020/08/28	Juan Minaya	MIN	49	Road gray 60th season patch	2020/08/28 twins49 Juan Minaya",
"2020/08/28	Jordy Mercer	NYY	22	Home white Hank Steinbrenner HGS memorial patch	2020/08/28 yankees22 Jordy Mercer",
"2020/08/28	Estevan Florial	NYY	90	Home white Hank Steinbrenner HGS memorial patch	2020/08/28 yankees90 Estevan Florial",
"2020/08/28	Taijuan Walker	TOR	00	Home royal Jackie Robinson Day	2020/08/28 bluejays00 Taijuan Walker",
"2020/08/29	Luis Garcia	HOU	77	Home orange Jackie Robinson Day	2020/08/29 astros77 Luis Garcia",
"2020/08/29	Tommy La Stella	OAK	3	Road gray Jackie Robinson Day	2020/08/29 athletics3 Tommy La Stella",
"2020/08/29	Carson Fulmer	PIT	56	Road black Jackie Robinson Day	2020/08/29 pirates56 Carson Fulmer",
"2020/08/29	Brock Holt	WSN	27	Road navy Jackie Robinson Day	2020/08/29 nationals27 Brock Holt",
"2020/08/30	Tommy Milone	ATL	53	Road gray Jackie Robinson Day	2020/08/30 braves53 Tommy Milone",
"2020/08/30	Bobby Dalbec	BOS	29	Home red Jackie Robinson Day	2020/08/30 redsox29 Bobby Dalbec",
"2020/08/30	Carlos Hernandez	KCR	71	Road royal David Glass DG memorial patch	2020/08/30 royals71 Carlos Hernandez",
"2020/08/30	Ariel Jurado	NYM	49	Road gray	2020/08/30 mets49 Ariel Jurado",
"2020/08/30	Deivi Garcia	NYY	83	Home white Hank Steinbrenner HGS memorial patch	2020/08/30 yankees83 Deivi Garcia",
"2020/08/30	Trevor Rosenthal	SDP	47	Road sand Jackie Robinson Day	2020/08/30 padres47 Trevor Rosenthal",
"2020/08/30	Seth Frankoff	SEA	60	Road gray Jackie Robinson Day	2020/08/30 mariners60 Seth Frankoff",
"2020/08/31	Yairo Munoz	BOS	60	Home white	2020/08/31 redsox60 Yairo Munoz",
"2020/08/31	Mike Kickham	BOS	74	Home white	2020/08/31 redsox74 Mike Kickham",
"2020/08/31	Robinson Leyer	BOS	77	Home white	2020/08/31 redsox77 Robinson Leyer",
"2020/08/31	Austin Hedges	CLE	17	Road navy	2020/08/31 indians17 Austin Hedges",
"2020/08/31	Josh Naylor	CLE	31	Road navy	2020/08/31 indians31 Josh Naylor",
"2020/08/31	Cal Quantrill	CLE	38	Road navy	2020/08/31 indians38 Cal Quantrill",
"2020/08/31	Ryan Castellani	COL	38	Home purple	2020/08/31 rockies38 Ryan Castellani",
"2020/08/31	Antonio Santos	COL	46	Home purple	2020/08/31 rockies46 Antonio Santos",
"2020/08/31	Mychal Givens	COL	60	Home purple	2020/08/31 rockies60 Mychal Givens",
"2020/08/31	Jahmai Jones	LAA	9	Home white	2020/08/31 angels9 Jahmai Jones",
"2020/08/31	Jose Briceno	LAA	19	Home white	2020/08/31 angels19 Jose Briceno",
"2020/08/31	Trey Supak	MIL	45	Home cream 50th season patch	2020/08/31 brewers45 Trey Supak",
"2020/08/31	Justin Topa	MIL	56	Home cream 50th season patch	2020/08/31 brewers56 Justin Topa",
"2020/08/31	Jason Castro	SDP	11	Road sand	2020/08/31 padres11 Jason Castro",
"2020/08/31	Mitch Moreland	SDP	18	Road sand	2020/08/31 padres18 Mitch Moreland",
"2020/08/31	Austin Nola	SDP	22	Road sand	2020/08/31 padres22 Austin Nola",
"2020/08/31	Austin Adams	SDP	54	Road sand	2020/08/31 padres54 Austin Adams",
"2020/08/31	Cody Reed	TBR	21	Road navy	2020/08/31 rays21 Cody Reed",
"2020/09/01	Joe Mantiply	ARI	36	Road gray	2020/09/01 dbacks36 Joe Mantiply",
"2020/09/01	Artie Lewicki	ARI	54	Road gray	2020/09/01 dbacks54 Artie Lewicki",
"2020/09/01	Keury Mella	ARI	64	Road gray	2020/09/01 dbacks64 Keury Mella",
"2020/09/01	Dilson Herrera	BAL	2	Home white	2020/09/01 orioles2 Dilson Herrera",
"2020/09/01	Cameron Maybin	CHC	15	Road gray	2020/09/01 cubs15 Cameron Maybin",
"2020/09/01	Josh Osich	CHC	37	Road gray	2020/09/01 cubs37 Josh Osich",
"2020/09/01	Jose Martinez	CHC	53	Road gray	2020/09/01 cubs53 Jose Martinez",
"2020/09/01	Brian Goodwin	CIN	17	Home white	2020/09/01 reds17 Brian Goodwin",
"2020/09/01	Archie Bradley	CIN	23	Home white	2020/09/01 reds23 Archie Bradley",
"2020/09/01	Kevin Pillar	COL	11	Home white	2020/09/01 rockies11 Kevin Pillar",
"2020/09/01	Starling Marte	MIA	6	Home white	2020/09/01 marlins6 Starling Marte",
"2020/09/01	Jazz Chisholm	MIA	70	Home white	2020/09/01 marlins70 Jazz Chisholm",
"2020/09/01	Phil Bickford	MIL	32	Home cream 50th season patch	2020/09/01 brewers32 Phil Bickford",
"2020/09/01	David Phelps	PHI	31	Home white	2020/09/01 phillies31 David Phelps",
"2020/09/01	Anthony Alford	PIT	6	Home white	2020/09/01 pirates6 Anthony Alford",
"2020/09/01	Ke'Bryan Hayes	PIT	13	Home white	2020/09/01 pirates13 Ke'Bryan Hayes",
"2020/09/01	Daniel Robertson	SFG	2	Road gray 20 at 24 patch	2020/09/01 giants2 Daniel Robertson",
"2020/09/01	Eli White	TEX	76	Road gray Globe Life Field inaugural season patch	2020/09/01 rangers76 Eli White",
"2020/09/01	Jonathan Villar	TOR	30	Road powder Tony Fernandez 1 memorial patch	2020/09/01 bluejays30 Jonathan Villar",
"2020/09/01	Robbie Ray	TOR	38	Road powder Tony Fernandez 1 memorial patch	2020/09/01 bluejays38 Robbie Ray",
"2020/09/01	Ross Stripling	TOR	48	Road powder Tony Fernandez 1 memorial patch	2020/09/01 bluejays48 Ross Stripling",
"2020/09/02	Andrew Triggs	BOS	61	Home white	2020/09/02 redsox61 Andrew Triggs",
"2020/09/02	Derek Hill	DET	54	Road gray Al Kaline 6 memorial patch	2020/09/02 tigers54 Derek Hill",
"2020/09/02	Franklin Barreto	LAA	8	Home red	2020/09/02 angels8 Franklin Barreto",
"2020/09/02	Robinson Chirinos	NYM	26	Road gray	2020/09/02 mets26 Robinson Chirinos",
"2020/09/02	Todd Frazier	NYM	33	Road gray	2020/09/02 mets33 Todd Frazier",
"2020/09/02	Miguel Castro	NYM	50	Road gray	2020/09/02 mets50 Miguel Castro",
"2020/09/02	Greg Allen	SDP	24	Road sand	2020/09/02 padres24 Greg Allen",
"2020/09/02	Mike Clevinger	SDP	52	Road sand	2020/09/02 padres52 Mike Clevinger",
"2020/09/02	Dan Altavilla	SDP	57	Road sand	2020/09/02 padres57 Dan Altavilla",
"2020/09/03	Travis Bergen	ARI	47	Road gray	2020/09/03 dbacks47 Travis Bergen",
"2020/09/03	Edward Olivares	KCR	14	Home white David Glass DG memorial patch	2020/09/03 royals14 Edward Olivares",
"2020/09/03	Walker Lockett	SEA	73	Home teal	2020/09/03 mariners73 Walker Lockett",
"2020/09/04	Patrick Weigel	ATL	65	Home red	2020/09/04 braves65 Patrick Weigel",
"2020/09/04	Sergio Alcantara	DET	40	Road gray Al Kaline 6 memorial patch	2020/09/04 tigers40 Sergio Alcantara",
"2020/09/04	Daniel Vogelbach	MIL	21	Road navy 50th season patch	2020/09/04 brewers21 Daniel Vogelbach",
"2020/09/04	Brent Rooker	MIN	50	Home navy 60th season patch	2020/09/04 twins50 Brent Rooker",
"2020/09/04	Erasmo Ramirez	NYM	43	Home white Tom Seaver 41 memorial patch	2020/09/04 mets43 Erasmo Ramirez",
"2020/09/04	Clarke Schmidt	NYY	86	Road gray Hank Steinbrenner HGS memorial patch	2020/09/04 yankees86 Clarke Schmidt",
"2020/09/04	Mike Minor	OAK	23	Home kelly green	2020/09/04 athletics23 Mike Minor",
"2020/09/04	Luis Campusano	SDP	21	Road brown	2020/09/04 padres21 Luis Campusano",
"2020/09/04	Luis Torrens	SEA	22	Home teal	2020/09/04 mariners22 Luis Torrens",
"2020/09/04	Ty France	SEA	23	Home teal	2020/09/04 mariners23 Ty France",
"2020/09/04	Brett Phillips	TBR	14	Home navy	2020/09/04 rays14 Brett Phillips",
"2020/09/04	John King	TEX	79	Road royal Globe Life Field inaugural season patch	2020/09/04 rangers79 John King",
"2020/09/05	Alex McRae	CHW	64	Road black Childhood Cancer Awareness patch Ed Farmer FARMIO memorial patch	2020/09/05 whitesox64 Alex McRae",
"2020/09/05	Todd Frazier	NYM	21	Home white Childhood Cancer Awareness patch Tom Seaver 41 memorial patch	2020/09/05 mets21 Todd Frazier",
"2020/09/05	Phillip Ervin	SEA	20	Home white Childhood Cancer Awareness patch	2020/09/05 mariners20 Phillip Ervin",
"2020/09/05	Caleb Joseph	TOR	7	Road gray Childhood Cancer Awareness patch Tony Fernandez 1 memorial patch	2020/09/05 bluejays7 Caleb Joseph",
"2020/09/06	Wyatt Mathisen	ARI	27	Road red snake hat	2020/09/06 dbacks27 Wyatt Mathisen",
"2020/09/06	Dean Kremer	BAL	64	Home black O's hat Cal Ripken 2131 25th anniversary patch	2020/09/06 orioles64 Dean Kremer",
"2020/09/06	Matt Dermody	CHC	45	Home white	2020/09/06 cubs45 Matt Dermody",
"2020/09/06	Mauricio Llovera	PHI	63	Road gray	2020/09/06 phillies63 Mauricio Llovera",
"2020/09/06	Taylor Williams	SDP	45	Road sand	2020/09/06 padres45 Taylor Williams",
"2020/09/07	Ildemaro Vargas	CHC	16	Home white	2020/09/07 cubs16 Ildemaro Vargas",
"2020/09/07	Jorge Ona	SDP	63	Home white	2020/09/07 padres63 Jorge Ona",
"2020/09/07	Casey Sadler	SEA	37	Home navy	2020/09/07 mariners37 Casey Sadler",
"2020/09/08	Carson Fulmer	BAL	60	Road gray	2020/09/08 orioles60 Carson Fulmer",
"2020/09/08	Deivy Grullon	BOS	73	Road gray	2020/09/08 redsox73 Deivy Grullon",
"2020/09/08	Billy Hamilton	CHC	6	Home white	2020/09/08 cubs6 Billy Hamilton",
"2020/09/08	Matt Reynolds	KCR	46	Road gray David Glass DG memorial patch	2020/09/08 royals46 Matt Reynolds",
"2020/09/08	Garrett Cleavinger	PHI	66	Home cream	2020/09/08 phillies66 Garrett Cleavinger",
"2020/09/09	Josh VanMeter	ARI	19	Home red black hat Roberto Clemente Day patch	2020/09/09 dbacks19 Josh VanMeter",
"2020/09/09	Kyle Nelson	CLE	63	Home red Roberto Clemente Day patch	2020/09/09 indians63 Kyle Nelson",
"2020/09/09	Daz Cameron	DET	41	Home white Roberto Clemente Day patch Al Kaline 6 memorial patch	2020/09/09 tigers41 Daz Cameron",
"2020/09/09	Jimmy Yacabonis	SEA	47	Road navy Roberto Clemente Day patch	2020/09/09 mariners47 Jimmy Yacabonis",
"2020/09/10	Pavin Smith	ARI	26	Home white sand accents	2020/09/10 dbacks26 Pavin Smith",
"2020/09/10	Drew Smyly	SFG	18	Road gray 20 at 24 patch	2020/09/10 giants18 Drew Smyly",
"2020/09/10	Justin Smoak	SFG	46	Road gray 20 at 24 patch	2020/09/10 giants46 Justin Smoak",
"2020/09/10	Sam Huff	TEX	74	Home white blue hat Globe Life Field inaugural season patch	2020/09/10 rangers74 Sam Huff",
"2020/09/10	Yadiel Hernandez	WSN	29	Home white Championship Roberto Clemente Day patch 2019 World Series champions patch	2020/09/10 nationals29 Yadiel Hernandez",
"2020/09/11	Caleb Smith	ARI	31	Home white teal accents	2020/09/11 dbacks31 Caleb Smith",
"2020/09/11	Domingo Tapia	BOS	66	Road gray	2020/09/11 redsox66 Domingo Tapia",
"2020/09/11	Johan Quezada	MIA	77	Home black	2020/09/11 marlins77 Johan Quezada",
"2020/09/11	Ronald Torreyes	PHI	74	Road gray	2020/09/11 phillies74 Ronald Torreyes",
"2020/09/11	Austin Davis	PIT	75	Road gray	2020/09/11 pirates75 Austin Davis",
"2020/09/11	Alejandro Kirk	TOR	85	Home white white panel hat Tony Fernandez 1 memorial patch	2020/09/11 bluejays85 Alejandro Kirk",
"2020/09/12	Daulton Jefferies	OAK	66	Road green	2020/09/12 athletics66 Daulton Jefferies",
"2020/09/12	Sherten Apostel	TEX	82	Home red TX hat Globe Life Field inaugural season patch	2020/09/12 rangers82 Sherten Apostel",
"2020/09/12	Jonathan Villar	TOR	20	Home royal Tony Fernandez 1 memorial patch	2020/09/12 bluejays20 Jonathan Villar",
"2020/09/13	Jonathan Stiever	CHW	53	Home white Ed Farmer FARMIO memorial patch	2020/09/13 whitesox53 Jonathan Stiever",
"2020/09/13	Braxton Garrett	MIA	94	Home black	2020/09/13 marlins94 Braxton Garrett",
"2020/09/13	Nate Orf	OAK	45	Road gray	2020/09/13 athletics45 Nate Orf",
"2020/09/13	Rafael Marchan	PHI	13	Road gray	2020/09/13 phillies13 Rafael Marchan",
"2020/09/14	Travis Blankenhorn	MIN	74	Road gray 60th season patch	2020/09/14 twins74 Travis Blankenhorn",
"2020/09/14	Jake Lamb	OAK	4	Road kelly green	2020/09/14 athletics4 Jake Lamb",
"2020/09/15	Jasseel De La Cruz	ATL	69	Road navy	2020/09/15 braves69 Jasseel De La Cruz",
"2020/09/15	Tanner Houck	BOS	89	Road navy	2020/09/15 redsox89 Tanner Houck",
"2020/09/15	Eric Haase	DET	13	Home white Al Kaline 6 memorial patch	2020/09/15 tigers13 Eric Haase",
"2020/09/15	Blake Cederlind	PIT	62	Road black	2020/09/15 pirates62 Blake Cederlind",
"2020/09/15	Demarcus Evans	TEX	67	Road gray Globe Life Field inaugural season patch	2020/09/15 rangers67 Demarcus Evans",
"2020/09/16	Zach McKinstry	LAD	8	Road gray Dodgers	2020/09/16 dodgers8 Zach McKinstry",
"2020/09/16	Mickey Moniak	PHI	16	Home white	2020/09/16 phillies16 Mickey Moniak",
"2020/09/17	Bruce Zimmermann	BAL	85	Home orange	2020/09/17 orioles85 Bruce Zimmermann",
"2020/09/18	Garrett Crochet	CHW	45	Road gray Ed Farmer FARMIO memorial patch	2020/09/18 whitesox45 Garrett Crochet",
"2020/09/18	Patrick Murphy	TOR	66	Road powder Tony Fernandez 1 memorial patch	2020/09/18 bluejays66 Patrick Murphy",
"2020/09/19	Cesar Puello	BOS	75	Home white	2020/09/19 redsox75 Cesar Puello",
"2020/09/19	Andrew Chafin	CHC	39	Home white	2020/09/19 cubs39 Andrew Chafin",
"2020/09/19	AJ Ramos	COL	51	Home black	2020/09/19 rockies51 AJ Ramos",
"2020/09/21	Guillermo Heredia	NYM	15	Home white Tom Seaver 41 memorial patch	2020/09/21 mets15 Guillermo Heredia",
"2020/09/21	Jared Oliva	PIT	76	Home white	2020/09/21 pirates76 Jared Oliva",
"2020/09/21	Paolo Espino	WSN	52	Home navy 2019 World Series champions patch	2020/09/21 nationals52 Paolo Espino",
"2020/09/22	Nick Pivetta	BOS	37	Home white	2020/09/22 redsox37 Nick Pivetta",
"2020/09/22	Brandon Dixon	DET	9	Road gray Al Kaline 6 memorial patch	2020/09/22 tigers9 Brandon Dixon",
"2020/09/22	Elliot Soto	LAA	7	Road gray	2020/09/22 angels7 Elliot Soto",
"2020/09/22	Tyler Lyons	NYY	58	Road gray Hank Steinbrenner HGS memorial patch	2020/09/22 yankees58 Tyler Lyons",
"2020/09/23	Tommy Doyle	COL	59	Road gray	2020/09/23 rockies59 Tommy Doyle",
"2020/09/24	Andrew Romine	TEX	6	Home white blue hat Globe Life Field inaugural season patch	2020/09/24 rangers6 Andrew Romine",
"2020/09/25	Patrick Wisdom	CHC	59	Road royal	2020/09/25 cubs59 Patrick Wisdom",
"2020/09/25	Edwar Colina	MIN	86	Home red 60th season patch	2020/09/25 twins86 Edwar Colina",
"2020/09/26	Tucker Davidson	ATL	64	Home white	2020/09/26 braves64 Tucker Davidson",
"2020/09/27	Pablo Sandoval	ATL	18	Home red	2020/09/27 braves18 Pablo Sandoval",
"2020/09/27	Brailyn Marquez	CHC	61	Road royal	2020/09/27 cubs61 Brailyn Marquez",
"2020/09/27	Andrew Susac	PIT	80	Road black	2020/09/27 pirates80 Andrew Susac",
"2020/09/29	Chas McCormick	HOU	20	Road orange	2020/09/29 astros20 Chas McCormick",
"2020/09/29	Alex Kirilloff	MIN	76	Home white 60th season patch	2020/09/29 twins76 Alex Kirilloff",
"2020/09/29	Shane McClanahan	TBR	62	Home navy	2020/09/29 rays62 Shane McClanahan",
"2020/10/01	Ryan Weathers	SDP	40	Home white	2020/10/01 padres40 Ryan Weathers",
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