// --- CONFIGURATION ---
var userHome = Folder.myDocuments.parent.fsName; 
var icloudRoot = userHome + "/Library/Mobile Documents/com~apple~CloudDocs/Sports/Jerseys/MLB";

var sourceFolder = new Folder(icloudRoot + "/MLB Templates/2025 MLB Full jerseys");
var exportFolder = new Folder(icloudRoot + "/MLB Jersey Numbers/MLB Jersey numbers 2025");

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
"2025/03/18	Justin Turner	CHC	3	Home white Nippon Express ad patch Tokyo Series patch	2025/03/18 cubs3 Justin Turner",
"2025/03/18	Pete Crow-Armstrong	CHC	4	Home white Nippon Express ad patch Tokyo Series patch	2025/03/18 cubs4 Pete Crow-Armstrong",
"2025/03/18	Matt Shaw	CHC	6	Home white Nippon Express ad patch Tokyo Series patch	2025/03/18 cubs6 Matt Shaw",
"2025/03/18	Ryan Brasier	CHC	54	Home white Nippon Express ad patch Tokyo Series patch	2025/03/18 cubs54 Ryan Brasier",
"2025/03/18	Roki Sasaki	LAD	11	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch Tokyo Series patch	2025/03/18 dodgers11 Roki Sasaki",
"2025/03/18	Luis Garcia	LAD	57	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch Tokyo Series patch	2025/03/18 dodgers57 Luis Garcia",
"2025/03/18	Matt Sauer	LAD	64	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch Tokyo Series patch	2025/03/18 dodgers64 Matt Sauer",
"2025/03/18	Jack Dreyer	LAD	86	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch Tokyo Series patch	2025/03/18 dodgers86 Jack Dreyer",
"2025/03/27	Garrett Hampson	ARI	8	Home cream Avnet ad patch	2025/03/27 dbacks8 Garrett Hampson",
"2025/03/27	Shelby Miller	ARI	18	Home cream Avnet ad patch	2025/03/27 dbacks18 Shelby Miller",
"2025/03/27	Jalen Beeks	ARI	68	Home cream Avnet ad patch	2025/03/27 dbacks68 Jalen Beeks",
"2025/03/27	Max Muncy	ATH	10	Road yellow Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/03/27 athletics10 Max Muncy",
"2025/03/27	Luis Urias	ATH	17	Road yellow Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/03/27 athletics17 Luis Urias",
"2025/03/27	Noah Murdock	ATH	58	Road yellow Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/03/27 athletics58 Noah Murdock",
"2025/03/27	Nick Allen	ATL	2	Road gray Quikrete ad patch	2025/03/27 braves2 Nick Allen",
"2025/03/27	Drake Baldwin	ATL	30	Road gray Quikrete ad patch	2025/03/27 braves30 Drake Baldwin",
"2025/03/27	Hector Neris	ATL	50	Road gray Quikrete ad patch	2025/03/27 braves50 Hector Neris",
"2025/03/27	Jose Suarez	ATL	54	Road gray Quikrete ad patch	2025/03/27 braves54 Jose Suarez",
"2025/03/27	Enyel De Los Santos	ATL	61	Road gray Quikrete ad patch	2025/03/27 braves61 Enyel De Los Santos",
"2025/03/27	Ramon Laureano	BAL	12	Road black T. Rowe Price ad patch	2025/03/27 orioles12 Ramon Laureano",
"2025/03/27	Alex Bregman	BOS	2	Road gray MassMutual ad patch	2025/03/27 redsox2 Alex Bregman",
"2025/03/27	Sean Newcomb	BOS	19	Road gray MassMutual ad patch	2025/03/27 redsox19 Sean Newcomb",
"2025/03/27	Kristian Campbell	BOS	28	Road gray MassMutual ad patch	2025/03/27 redsox28 Kristian Campbell",
"2025/03/27	Gage Workman	CHC	25	Road royal Motorola ad patch	2025/03/27 cubs25 Gage Workman",
"2025/03/27	Brad Keller	CHC	40	Road royal Motorola ad patch	2025/03/27 cubs40 Brad Keller",
"2025/03/27	Nick Maton	CHW	0	Home white	2025/03/27 whitesox0 Nick Maton",
"2025/03/27	Jacob Amaya	CHW	8	Home white	2025/03/27 whitesox8 Jacob Amaya",
"2025/03/27	Michael A. Taylor	CHW	21	Home white	2025/03/27 whitesox21 Michael A. Taylor",
"2025/03/27	Travis Jankowski	CHW	31	Home white	2025/03/27 whitesox31 Travis Jankowski",
"2025/03/27	Mike Clevinger	CHW	52	Home white	2025/03/27 whitesox52 Mike Clevinger",
"2025/03/27	Brandon Eisert	CHW	53	Home white	2025/03/27 whitesox53 Brandon Eisert",
"2025/03/27	Fraser Ellard	CHW	55	Home white	2025/03/27 whitesox55 Fraser Ellard",
"2025/03/27	Mike Vasil	CHW	61	Home white	2025/03/27 whitesox61 Mike Vasil",
"2025/03/27	Shane Smith	CHW	64	Home white	2025/03/27 whitesox64 Shane Smith",
"2025/03/27	Austin Wynns	CIN	38	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/03/27 reds38 Austin Wynns",
"2025/03/27	Taylor Rogers	CIN	55	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/03/27 reds55 Taylor Rogers",
"2025/03/27	Scott Barlow	CIN	58	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/03/27 reds58 Scott Barlow",
"2025/03/27	Jakob Junis	CLE	16	Road gray Marathon ad patch	2025/03/27 guardians16 Jakob Junis",
"2025/03/27	Nolan Jones	CLE	22	Road gray Marathon ad patch	2025/03/27 guardians22 Nolan Jones",
"2025/03/27	Logan Allen	CLE	26	Road gray Marathon ad patch	2025/03/27 guardians26 Logan Allen",
"2025/03/27	Manuel Margot	DET	7	Road gray Meijer ad patch	2025/03/27 tigers7 Manuel Margot",
"2025/03/27	John Brebbia	DET	49	Road gray Meijer ad patch	2025/03/27 tigers49 John Brebbia",
"2025/03/27	Brendan Rodgers	HOU	1	Home white Oxy ad patch	2025/03/27 astros1 Brendan Rodgers",
"2025/03/27	Cam Smith	HOU	11	Home white Oxy ad patch	2025/03/27 astros11 Cam Smith",
"2025/03/27	Steven Okert	HOU	48	Home white Oxy ad patch	2025/03/27 astros48 Steven Okert",
"2025/03/27	Cavan Biggio	KCR	18	Home powder blue pants QuikTrip ad patch	2025/03/27 royals18 Cavan Biggio",
"2025/03/27	Mark Canha	KCR	21	Home powder blue pants QuikTrip ad patch	2025/03/27 royals21 Mark Canha",
"2025/03/27	Yoan Moncada	LAA	5	Road red FBM ad patch	2025/03/27 angels5 Yoan Moncada",
"2025/03/27	Nicky Lopez	LAA	8	Road red FBM ad patch	2025/03/27 angels8 Nicky Lopez",
"2025/03/27	Ryan Johnson	LAA	32	Road red FBM ad patch	2025/03/27 angels32 Ryan Johnson",
"2025/03/27	Ian Anderson	LAA	35	Road red FBM ad patch	2025/03/27 angels35 Ian Anderson",
"2025/03/27	Jack Kochanowicz	LAA	41	Road red FBM ad patch	2025/03/27 angels41 Jack Kochanowicz",
"2025/03/27	Garrett McDaniels	LAA	57	Road red FBM ad patch	2025/03/27 angels57 Garrett McDaniels",
"2025/03/27	Kenley Jansen	LAA	74	Road red FBM ad patch	2025/03/27 angels74 Kenley Jansen",
"2025/03/27	Tim Anderson	LAA	77	Road red FBM ad patch	2025/03/27 angels77 Tim Anderson",
"2025/03/27	Otto Lopez	MIA	6	Home white ADT ad patch	2025/03/27 marlins6 Otto Lopez",
"2025/03/27	Graham Pauley	MIA	21	Home white ADT ad patch	2025/03/27 marlins21 Graham Pauley",
"2025/03/27	Tyler Phillips	MIA	30	Home white ADT ad patch	2025/03/27 marlins30 Tyler Phillips",
"2025/03/27	Ronny Henriquez	MIA	32	Home white ADT ad patch	2025/03/27 marlins32 Ronny Henriquez",
"2025/03/27	Liam Hicks	MIA	34	Home white ADT ad patch	2025/03/27 marlins34 Liam Hicks",
"2025/03/27	Cal Quantrill	MIA	47	Home white ADT ad patch	2025/03/27 marlins47 Cal Quantrill",
"2025/03/27	Tyler Alexander	MIL	33	Road navy Bob Uecker memorial patch Northwestern Mutual ad patch	2025/03/27 brewers33 Tyler Alexander",
"2025/03/27	Chad Patrick	MIL	39	Road navy Bob Uecker memorial patch Northwestern Mutual ad patch	2025/03/27 brewers39 Chad Patrick",
"2025/03/27	Connor Thomas	MIL	57	Road navy Bob Uecker memorial patch Northwestern Mutual ad patch	2025/03/27 brewers57 Connor Thomas",
"2025/03/27	Harrison Bader	MIN	12	Road navy	2025/03/27 twins12 Harrison Bader",
"2025/03/27	Ty France	MIN	13	Road navy	2025/03/27 twins13 Ty France",
"2025/03/27	Danny Coulombe	MIN	54	Road navy	2025/03/27 twins54 Danny Coulombe",
"2025/03/27	Hayden Senger	NYM	30	Road gray Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/03/27 mets30 Hayden Senger",
"2025/03/27	Oswald Peraza	NYY	18	Home white Starr ad patch	2025/03/27 yankees18 Oswald Peraza",
"2025/03/27	Pablo Reyes	NYY	19	Home white Starr ad patch	2025/03/27 yankees19 Pablo Reyes",
"2025/03/27	Ben Rice	NYY	22	Home white Starr ad patch	2025/03/27 yankees22 Ben Rice",
"2025/03/27	Jasson Dominguez	NYY	24	Home white Starr ad patch	2025/03/27 yankees24 Jasson Dominguez",
"2025/03/27	J.C. Escarra	NYY	25	Home white Starr ad patch	2025/03/27 yankees25 J.C. Escarra",
"2025/03/27	Ryan Yarbrough	NYY	33	Home white Starr ad patch	2025/03/27 yankees33 Ryan Yarbrough",
"2025/03/27	Tim Hill	NYY	41	Home white Starr ad patch	2025/03/27 yankees41 Tim Hill",
"2025/03/27	Brent Headrick	NYY	47	Home white Starr ad patch	2025/03/27 yankees47 Brent Headrick",
"2025/03/27	Carlos Carrasco	NYY	59	Home white Starr ad patch	2025/03/27 yankees59 Carlos Carrasco",
"2025/03/27	Yoendrys Gomez	NYY	94	Home white Starr ad patch	2025/03/27 yankees94 Yoendrys Gomez",
"2025/03/27	Johan Rojas	PHI	23	Road gray IBX ad patch	2025/03/27 phillies23 Johan Rojas",
"2025/03/27	Carlos Hernandez	PHI	35	Road gray IBX ad patch	2025/03/27 phillies35 Carlos Hernandez",
"2025/03/27	Tim Mayza	PIT	18	Road black Sheetz ad patch	2025/03/27 pirates18 Tim Mayza",
"2025/03/27	Tommy Pham	PIT	28	Road black Sheetz ad patch	2025/03/27 pirates28 Tommy Pham",
"2025/03/27	Andrew Heaney	PIT	45	Road black Sheetz ad patch	2025/03/27 pirates45 Andrew Heaney",
"2025/03/27	Justin Lawrence	PIT	61	Road black Sheetz ad patch	2025/03/27 pirates61 Justin Lawrence",
"2025/03/27	Jose Iglesias	SDP	7	Home white Motorola ad patch	2025/03/27 padres7 Jose Iglesias",
"2025/03/27	Yuli Gurriel	SDP	10	Home white Motorola ad patch	2025/03/27 padres10 Yuli Gurriel",
"2025/03/27	Martin Maldonado	SDP	15	Home white Motorola ad patch	2025/03/27 padres15 Martin Maldonado",
"2025/03/27	Jason Heyward	SDP	22	Home white Motorola ad patch	2025/03/27 padres22 Jason Heyward",
"2025/03/27	Nick Pivetta	SDP	27	Home white Motorola ad patch	2025/03/27 padres27 Nick Pivetta",
"2025/03/27	Gavin Sheets	SDP	30	Home white Motorola ad patch	2025/03/27 padres30 Gavin Sheets",
"2025/03/27	Omar Cruz	SDP	60	Home white Motorola ad patch	2025/03/27 padres60 Omar Cruz",
"2025/03/27	Kyle Hart	SDP	68	Home white Motorola ad patch	2025/03/27 padres68 Kyle Hart",
"2025/03/27	Rowdy Tellez	SEA	23	Home white Nintendo ad patch	2025/03/27 mariners23 Rowdy Tellez",
"2025/03/27	Christian Koss	SFG	50	Road gray Chevrolet ad patch	2025/03/27 giants50 Christian Koss",
"2025/03/27	Lou Trivino	SFG	56	Road gray Chevrolet ad patch	2025/03/27 giants56 Lou Trivino",
"2025/03/27	Phil Maton	STL	88	Home white Stifel ad patch	2025/03/27 cardinals88 Phil Maton",
"2025/03/27	Kevin Pillar	TEX	1	Home white blue hat Energy Transfer ad patch	2025/03/27 rangers1 Kevin Pillar",
"2025/03/27	Marc Church	TEX	30	Home white blue hat Energy Transfer ad patch	2025/03/27 rangers30 Marc Church",
"2025/03/27	Luke Jackson	TEX	77	Home white blue hat Energy Transfer ad patch	2025/03/27 rangers77 Luke Jackson",
"2025/03/27	Myles Straw	TOR	3	Home white TD patch	2025/03/27 bluejays3 Myles Straw",
"2025/03/27	Alan Roden	TOR	18	Home white TD patch	2025/03/27 bluejays18 Alan Roden",
"2025/03/27	Max Scherzer	TOR	31	Home white TD patch	2025/03/27 bluejays31 Max Scherzer",
"2025/03/27	Richard Lovelady	TOR	58	Home white TD patch	2025/03/27 bluejays58 Richard Lovelady",
"2025/03/27	Jacob Barnes	TOR	67	Home white TD patch	2025/03/27 bluejays67 Jacob Barnes",
"2025/03/27	Paul DeJong	WSN	14	Home white	2025/03/27 nationals14 Paul DeJong",
"2025/03/27	Lucas Sims	WSN	39	Home white	2025/03/27 nationals39 Lucas Sims",
"2025/03/27	Colin Poche	WSN	41	Home white	2025/03/27 nationals41 Colin Poche",
"2025/03/27	Brad Lord	WSN	61	Home white	2025/03/27 nationals61 Brad Lord",
"2025/03/28	Tyler Freeman	COL	2	Road purple	2025/03/28 rockies2 Tyler Freeman",
"2025/03/28	Mickey Moniak	COL	22	Road purple	2025/03/28 rockies22 Mickey Moniak",
"2025/03/28	Nick Martini	COL	35	Road purple	2025/03/28 rockies35 Nick Martini",
"2025/03/28	Scott Alexander	COL	52	Road purple	2025/03/28 rockies52 Scott Alexander",
"2025/03/28	Mason Englert	TBR	59	Home white	2025/03/28 rays59 Mason Englert",
"2025/03/28	Jose Caballero	TBR	77	Home white	2025/03/28 rays77 Jose Caballero",
"2025/03/29	Jake Mangum	TBR	28	Home throwback	2025/03/29 rays28 Jake Mangum",
"2025/03/30	Luarbert Arias	MIA	76	Home blue ADT ad patch	2025/03/30 marlins76 Luarbert Arias",
"2025/03/30	Jonathan Ornelas	TEX	24	Home powder Energy Transfer ad patch	2025/03/30 rangers24 Jonathan Ornelas",
"2025/03/30	Mason Fluharty	TOR	68	Home powder TD patch	2025/03/30 bluejays68 Mason Fluharty",
"2025/03/31	Angel Perdomo	ATH	52	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/03/31 athletics52 Angel Perdomo",
"2025/03/31	Tyler Tolbert	KCR	2	Road powder QuikTrip ad patch	2025/03/31 royals2 Tyler Tolbert",
"2025/03/31	Darren McCaughan	MIN	51	Road gray	2025/03/31 twins51 Darren McCaughan",
"2025/04/01	Stuart Fairchild	ATL	17	Road navy Quikrete ad patch	2025/04/01 braves17 Stuart Fairchild",
"2025/04/01	Zach Thompson	ATL	73	Road navy Quikrete ad patch	2025/04/01 braves73 Zach Thompson",
"2025/04/01	Adam Ottavino	NYY	58	Home white Starr ad patch	2025/04/01 yankees58 Adam Ottavino",
"2025/04/01	Thomas Harrington	PIT	78	Road black Sheetz ad patch	2025/04/01 pirates78 Thomas Harrington",
"2025/04/03	Alexander Canario	PIT	29	Home black Pittsburgh Sheetz ad patch	2025/04/03 pirates29 Alexander Canario",
"2025/04/04	Luis F. Castillo	SEA	43	Road navy Nintendo Switch 2 ad patch	2025/04/04 mariners43 Luis F. Castillo",
"2025/04/04	Patrick Corbin	TEX	46	City connect Energy Transfer ad patch	2025/04/04 rangers46 Patrick Corbin",
"2025/04/05	Tim Tawa	ARI	13	Road red Avnet ad patch	2025/04/05 dbacks13 Tim Tawa",
"2025/04/05	Jesse Hahn	SEA	49	Road teal Nintendo Switch 2 ad patch	2025/04/05 mariners49 Jesse Hahn",
"2025/04/06	Hunter Dobbins	BOS	73	Home white MassMutual ad patch	2025/04/06 redsox73 Hunter Dobbins",
"2025/04/06	Chase Dollander	COL	32	Home white	2025/04/06 rockies32 Chase Dollander",
"2025/04/06	Michael Darrell-Hicks	LAA	61	Home white FBM ad patch	2025/04/06 angels61 Michael Darrell-Hicks",
"2025/04/06	Grant Wolfram	MIL	50	Home pinstripes Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/06 brewers50 Grant Wolfram",
"2025/04/06	Chase Shugart	PIT	55	Home black Pittsburgh Sheetz ad patch	2025/04/06 pirates55 Chase Shugart",
"2025/04/07	Jason Alexander	ATH	49	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/04/07 athletics49 Jason Alexander",
"2025/04/07	Robert Stock	BOS	78	Home white MassMutual ad patch	2025/04/07 redsox78 Robert Stock",
"2025/04/07	Logan VanWey	HOU	64	Road gray Oxy ad patch	2025/04/07 astros64 Logan VanWey",
"2025/04/07	Tsung-Che Cheng	PIT	71	Home white military hat Sheetz ad patch	2025/04/07 pirates71 Tsung-Che Cheng",
"2025/04/07	Yohel Pozo	STL	63	Road gray Stifel ad patch	2025/04/07 cardinals63 Yohel Pozo",
"2025/04/08	Zac Veen	COL	13	Home purple	2025/04/08 rockies13 Zac Veen",
"2025/04/08	Brewer Hicklen	DET	50	Home white Meijer ad patch	2025/04/08 tigers50 Brewer Hicklen",
"2025/04/08	Tomas Nido	DET	58	Home white Meijer ad patch	2025/04/08 tigers58 Tomas Nido",
"2025/04/08	Quinn Priester	MIL	46	Road gray Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/08 brewers46 Quinn Priester",
"2025/04/08	Oscar Gonzalez	SDP	39	Road sand Motorola ad patch	2025/04/08 padres39 Oscar Gonzalez",
"2025/04/08	Coco Montes	TBR	10	Home white	2025/04/08 rays10 Coco Montes",
"2025/04/08	Caleb Boushley	TEX	70	Road royal Energy Transfer ad patch	2025/04/08 rangers70 Caleb Boushley",
"2025/04/09	Rafael Montero	ATL	48	Home white Quikrete ad patch	2025/04/09 braves48 Rafael Montero",
"2025/04/09	Greg Jones	CHW	30	Road gray	2025/04/09 whitesox30 Greg Jones",
"2025/04/09	Casey Lawrence	SEA	41	Home white Nintendo ad patch	2025/04/09 mariners41 Casey Lawrence",
"2025/04/10	Omar Narvaez	CHW	22	Road black	2025/04/10 whitesox22 Omar Narvaez",
"2025/04/10	Joshua Palacios	CHW	47	Road black	2025/04/10 whitesox47 Joshua Palacios",
"2025/04/10	J.D. Davis	LAA	22	Road red FBM ad patch	2025/04/10 angels22 J.D. Davis",
"2025/04/11	Chase Meidroth	CHW	10	Home white	2025/04/11 whitesox10 Chase Meidroth",
"2025/04/11	Rob Brantly	MIA	19	Home black ADT ad patch	2025/04/11 marlins19 Rob Brantly",
"2025/04/11	Jose Quintana	MIL	62	Road navy Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/11 brewers62 Jose Quintana",
"2025/04/11	Casey Legumina	SEA	64	City connect Nintendo ad patch	2025/04/11 mariners64 Casey Legumina",
"2025/04/13	Michael Petersen	ATL	70	Road navy Quikrete ad patch	2025/04/13 braves70 Michael Petersen",
"2025/04/13	Michael Fulmer	BOS	51	Road gray MassMutual ad patch	2025/04/13 redsox51 Michael Fulmer",
"2025/04/13	Evan Sisk	KCR	47	Road royal QuikTrip ad patch	2025/04/13 royals47 Evan Sisk",
"2025/04/13	Ben Williamson	SEA	9	Home cream Nintendo ad patch	2025/04/13 mariners9 Ben Williamson",
"2025/04/13	Cole Henry	WSN	99	Road gray	2025/04/13 nationals99 Cole Henry",
"2025/04/14	Braxton Fulford	COL	37	Road gray	2025/04/14 rockies37 Braxton Fulford",
"2025/04/14	Connor Joe	SDP	24	Home white Motorola ad patch	2025/04/14 padres24 Connor Joe",
"2025/04/16	Scott Blewett	BAL	67	Home white T. Rowe Price ad patch	2025/04/16 orioles67 Scott Blewett",
"2025/04/16	Logan Henderson	MIL	43	Home cream Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/16 brewers43 Logan Henderson",
"2025/04/16	Justin Hagenman	NYM	51	Road gray Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/04/16 mets51 Justin Hagenman",
"2025/04/16	Matt Svanson	STL	49	Home white Stifel ad patch	2025/04/16 cardinals49 Matt Svanson",
"2025/04/17	Gabriel Moreno	ARI	14	Road red Avnet ad patch	2025/04/17 dbacks14 Gabriel Moreno",
"2025/04/17	Alex Verdugo	ATL	8	Home red Quikrete ad patch	2025/04/17 braves8 Alex Verdugo",
"2025/04/17	Edgar Quero	CHW	7	Home white	2025/04/17 whitesox7 Edgar Quero",
"2025/04/17	Jose Azocar	NYM	28	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/04/17 mets28 Jose Azocar",
"2025/04/18	Eddie Rosario	LAD	9	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/04/18 dodgers9 Eddie Rosario",
"2025/04/18	Noah Davis	LAD	56	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/04/18 dodgers56 Noah Davis",
"2025/04/18	Caleb Durbin	MIL	21	City connect Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/18 brewers21 Caleb Durbin",
"2025/04/18	Luke Keaschall	MIN	15	Road gray	2025/04/18 twins15 Luke Keaschall",
"2025/04/18	Jonah Bride	MIN	31	Road gray	2025/04/18 twins31 Jonah Bride",
"2025/04/18	Chandler Simpson	TBR	14	City connect	2025/04/18 rays14 Chandler Simpson",
"2025/04/19	J.P. Feyereisen	ARI	61	Road black Avnet ad patch	2025/04/19 dbacks61 J.P. Feyereisen",
"2025/04/19	Juan Morillo	ARI	67	Road black Avnet ad patch	2025/04/19 dbacks67 Juan Morillo",
"2025/04/19	Brandon Young	BAL	63	Home orange orange pants T. Rowe Price ad patch	2025/04/19 orioles63 Brandon Young",
"2025/04/19	Bailey Horn	DET	67	Home white Meijer ad patch	2025/04/19 tigers67 Bailey Horn",
"2025/04/19	Forrest Whitley	HOU	55	Home white Oxy ad patch	2025/04/19 astros55 Forrest Whitley",
"2025/04/19	Patrick Monteverde	MIA	44	Road black ADT ad patch	2025/04/19 marlins44 Patrick Monteverde",
"2025/04/19	Tirso Ornelas	SDP	21	Road sand Motorola ad patch	2025/04/19 padres21 Tirso Ornelas",
"2025/04/20	Cody Poteet	BAL	53	Home white T. Rowe Price ad patch	2025/04/20 orioles53 Cody Poteet",
"2025/04/20	Randy Wynne	CIN	53	Road gray Pete Rose 14 memorial patch Kroger ad patch	2025/04/20 reds53 Randy Wynne",
"2025/04/20	Zach Agnos	COL	36	City connect	2025/04/20 rockies36 Zach Agnos",
"2025/04/20	Ronny Simon	MIA	41	Road gray ADT ad patch	2025/04/20 marlins41 Ronny Simon",
"2025/04/20	Cade Gibson	MIA	58	Road gray ADT ad patch	2025/04/20 marlins58 Cade Gibson",
"2025/04/20	Sauryn Lao	SEA	78	Road navy Nintendo Switch 2 ad patch	2025/04/20 mariners78 Sauryn Lao",
"2025/04/20	Dillon Tate	TOR	9	Home powder TD patch	2025/04/20 bluejays9 Dillon Tate",
"2025/04/20	Paxton Schultz	TOR	65	Home powder TD patch	2025/04/20 bluejays65 Paxton Schultz",
"2025/04/20	Andry Lara	WSN	72	Road gray	2025/04/20 nationals72 Andry Lara",
"2025/04/21	Scott Blewett	ATL	63	Home white Quikrete ad patch	2025/04/21 braves63 Scott Blewett",
"2025/04/21	Bobby Dalbec	CHW	31	Road black	2025/04/21 whitesox31 Bobby Dalbec",
"2025/04/21	Zak Kent	CLE	61	Home white Marathon ad patch	2025/04/21 guardians61 Zak Kent",
"2025/04/21	Agustin Ramirez	MIA	50	Home white ADT ad patch	2025/04/21 marlins50 Agustin Ramirez",
"2025/04/21	Craig Yoho	MIL	48	Road navy Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/21 brewers48 Craig Yoho",
"2025/04/22	Nathan Wiles	ATL	71	Home white Quikrete ad patch	2025/04/22 braves71 Nathan Wiles",
"2025/04/22	Will Wilson	CLE	7	Home red Marathon ad patch	2025/04/22 guardians7 Will Wilson",
"2025/04/22	Chase Lee	DET	53	Home white Meijer ad patch	2025/04/22 tigers53 Chase Lee",
"2025/04/22	Tyler Matzek	NYY	68	Road gray Starr ad patch	2025/04/22 yankees68 Tyler Matzek",
"2025/04/23	Nick Kurtz	ATH	16	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/04/23 athletics16 Nick Kurtz",
"2025/04/23	Nicky Lopez	CHC	12	Home white Motorola ad patch	2025/04/23 cubs12 Nicky Lopez",
"2025/04/23	Drew Pomeranz	CHC	45	Home white Motorola ad patch	2025/04/23 cubs45 Drew Pomeranz",
"2025/04/23	Carl Edwards Jr.	LAA	52	Home white FBM ad patch	2025/04/23 angels52 Carl Edwards Jr.",
"2025/04/23	Nick Ahmed	TEX	23	Road gray Energy Transfer ad patch	2025/04/23 rangers23 Nick Ahmed",
"2025/04/24	Juan Mejia	COL	47	Road gray	2025/04/24 rockies47 Juan Mejia",
"2025/04/24	Matt Gorski	PIT	62	Road black Sheetz ad patch	2025/04/24 pirates62 Matt Gorski",
"2025/04/25	Doug Nikhazy	CLE	65	Home red Marathon ad patch	2025/04/25 guardians65 Doug Nikhazy",
"2025/04/25	Owen Miller	COL	11	City connect	2025/04/25 rockies11 Owen Miller",
"2025/04/25	Ryan Bergert	SDP	38	City connect Motorola ad patch	2025/04/25 padres38 Ryan Bergert",
"2025/04/26	Grant Wolfram	BAL	86	Road black T. Rowe Price ad patch	2025/04/26 orioles86 Grant Wolfram",
"2025/04/26	Gage Workman	CHW	41	Road black	2025/04/26 whitesox41 Gage Workman",
"2025/04/26	Kolby Allard	CLE	49	Home red Marathon ad patch	2025/04/26 guardians49 Kolby Allard",
"2025/04/26	Jake Eder	LAA	39	Road red FBM ad patch	2025/04/26 angels39 Jake Eder",
"2025/04/26	Jose Fermin	LAA	68	Road red FBM ad patch	2025/04/26 angels68 Jose Fermin",
"2025/04/26	Yoendrys Gomez	LAD	94	City connect Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/04/26 dodgers94 Yoendrys Gomez",
"2025/04/26	Daz Cameron	MIL	20	Road gray Bob Uecker memorial patch Northwestern Mutual ad patch	2025/04/26 brewers20 Daz Cameron",
"2025/04/26	Kody Clemens	MIN	18	Home white	2025/04/26 twins18 Kody Clemens",
"2025/04/26	Travis Jankowski	TBR	20	Road navy	2025/04/26 rays20 Travis Jankowski",
"2025/04/27	Tom Cosgrove	CHC	38	Home white Motorola ad patch	2025/04/27 cubs38 Tom Cosgrove",
"2025/04/27	Alan Trejo	COL	31	Home white	2025/04/27 rockies31 Alan Trejo",
"2025/04/27	Jose Urena	NYM	54	Road gray Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/04/27 mets54 Jose Urena",
"2025/04/27	David Morgan	SDP	66	Home camo brown Motorola ad patch	2025/04/27 padres66 David Morgan",
"2025/04/27	Logan Evans	SEA	73	Home cream Nintendo ad patch	2025/04/27 mariners73 Logan Evans",
"2025/04/28	Eddie Rosario	ATL	9	Road gray Quikrete ad patch	2025/04/28 braves9 Eddie Rosario",
"2025/04/28	Ian Anderson	ATL	34	Road gray Quikrete ad patch	2025/04/28 braves34 Ian Anderson",
"2025/04/28	Kade Strowd	BAL	57	Home white T. Rowe Price ad patch	2025/04/28 orioles57 Kade Strowd",
"2025/04/28	Maverick Handley	BAL	98	Home white T. Rowe Price ad patch	2025/04/28 orioles98 Maverick Handley",
"2025/04/28	Cody Bolton	CLE	58	Home white Marathon ad patch	2025/04/28 guardians58 Cody Bolton",
"2025/04/28	Jose Barrero	STL	27	Road gray navy hat Stifel ad patch	2025/04/28 cardinals27 Jose Barrero",
"2025/04/29	Kyle Gibson	BAL	48	Home white T. Rowe Price ad patch	2025/04/29 orioles48 Kyle Gibson",
"2025/04/29	Vince Velasquez	CLE	35	Home red Marathon ad patch	2025/04/29 guardians35 Vince Velasquez",
"2025/04/29	Samad Taylor	SEA	0	Home white Nintendo ad patch	2025/04/29 mariners0 Samad Taylor",
"2025/04/29	Casey Lawrence	TOR	58	Home white TD patch	2025/04/29 bluejays58 Casey Lawrence",
"2025/04/30	Carlos Duran	ATH	39	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/04/30 athletics39 Carlos Duran",
"2025/04/30	Chris Flexen	CHC	58	Road royal Motorola ad patch	2025/04/30 cubs58 Chris Flexen",
"2025/04/30	Tyler Callihan	CIN	32	Home red Pete Rose 14 memorial patch Kroger ad patch	2025/04/30 reds32 Tyler Callihan",
"2025/04/30	Chase Petty	CIN	61	Home red Pete Rose 14 memorial patch Kroger ad patch	2025/04/30 reds61 Chase Petty",
"2025/04/30	AJ Blubaugh	HOU	69	Home white Oxy ad patch	2025/04/30 astros69 AJ Blubaugh",
"2025/04/30	Noah Cameron	KCR	65	Road gray QuikTrip ad patch	2025/04/30 royals65 Noah Cameron",
"2025/04/30	Chris Devenski	NYM	49	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/04/30 mets49 Chris Devenski",
"2025/04/30	Brandon Waddell	NYM	82	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/04/30 mets82 Brandon Waddell",
"2025/04/30	Rhylan Thomas	SEA	31	Home white Nintendo ad patch	2025/04/30 mariners31 Rhylan Thomas",
"2025/04/30	Tucker Barnhart	TEX	18	Home white blue hat Energy Transfer ad patch	2025/04/30 rangers18 Tucker Barnhart",
"2025/04/30	Eric Lauer	TOR	56	Home powder TD patch	2025/04/30 bluejays56 Eric Lauer",
"2025/05/01	Jose Castillo	ARI	66	Road gray black hat Avnet ad patch	2025/05/01 dbacks66 Jose Castillo",
"2025/05/01	Luis Mey	CIN	62	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/05/01 reds62 Luis Mey",
"2025/05/01	Tyler Owens	DET	62	Road gray Meijer ad patch	2025/05/01 tigers62 Tyler Owens",
"2025/05/01	Genesis Cabrera	NYM	92	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/05/01 mets92 Genesis Cabrera",
"2025/05/01	Andrew Chafin	WSN	53	Road navy	2025/05/01 nationals53 Andrew Chafin",
"2025/05/02	Gunnar Hoglund	ATH	53	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/02 athletics53 Gunnar Hoglund",
"2025/05/02	Matt Festa	CLE	52	Road gray Marathon ad patch	2025/05/02 guardians52 Matt Festa",
"2025/05/02	Luke Maile	KCR	15	Road gray QuikTrip ad patch	2025/05/02 royals15 Luke Maile",
"2025/05/02	Niko Kavadas	LAA	20	Home white FBM ad patch	2025/05/02 angels20 Niko Kavadas",
"2025/05/02	Blaine Crim	TEX	13	City connect Energy Transfer ad patch	2025/05/02 rangers13 Blaine Crim",
"2025/05/03	Abraham Toro	BOS	29	Home yellow MassMutual ad patch	2025/05/03 redsox29 Abraham Toro",
"2025/05/03	Touki Toussaint	LAA	55	Home white FBM ad patch	2025/05/03 angels55 Touki Toussaint",
"2025/05/03	Tanner Rainey	PIT	27	Home black Pittsburgh Sheetz ad patch	2025/05/03 pirates27 Tanner Rainey",
"2025/05/04	Caleb Freeman	CHW	68	Home white	2025/05/04 whitesox68 Caleb Freeman",
"2025/05/04	Blade Tidwell	NYM	40	Road royal Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/05/04 mets40 Blade Tidwell",
"2025/05/05	Jose Urena	TOR	48	Road royal TD patch	2025/05/05 bluejays48 Jose Urena",
"2025/05/06	Hector Neris	LAA	54	Home white FBM ad patch	2025/05/06 angels54 Hector Neris",
"2025/05/06	Connor Brogdon	LAA	75	Home white FBM ad patch	2025/05/06 angels75 Connor Brogdon",
"2025/05/06	J.P. Feyereisen	LAD	40	Road gray Los Angeles Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/05/06 dodgers40 J.P. Feyereisen",
"2025/05/06	Dylan Moore	SEA	25	Road navy Nintendo Switch 2 ad patch	2025/05/06 mariners25 Dylan Moore",
"2025/05/07	Tomas Nido	DET	0	Road gray Meijer ad patch	2025/05/07 tigers0 Tomas Nido",
"2025/05/07	Leody Taveras	SEA	4	Road navy Nintendo Switch 2 ad patch	2025/05/07 mariners4 Leody Taveras",
"2025/05/07	Braydon Fisher	TOR	63	Road royal TD patch	2025/05/07 bluejays63 Braydon Fisher",
"2025/05/09	Elvis Alvarado	ATH	61	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/09 athletics61 Elvis Alvarado",
"2025/05/09	Luke Williams	ATL	37	Road gray Quikrete ad patch	2025/05/09 braves37 Luke Williams",
"2025/05/09	Chris Flexen	CHC	77	Road gray Motorola ad patch	2025/05/09 cubs77 Chris Flexen",
"2025/05/09	Matthew Lugo	LAA	15	Home white FBM ad patch	2025/05/09 angels15 Matthew Lugo",
"2025/05/09	Shaun Anderson	LAA	64	Home white FBM ad patch	2025/05/09 angels64 Shaun Anderson",
"2025/05/09	Connor Seabold	TBR	41	City connect	2025/05/09 rays41 Connor Seabold",
"2025/05/09	Sam Haggerty	TEX	0	Road gray Energy Transfer ad patch	2025/05/09 rangers0 Sam Haggerty",
"2025/05/09	Michael Stefanic	TOR	16	Road gray TD patch	2025/05/09 bluejays16 Michael Stefanic",
"2025/05/10	Cade Horton	CHC	22	Road royal Motorola ad patch	2025/05/10 cubs22 Cade Horton",
"2025/05/10	Tim Elko	CHW	30	Home white	2025/05/10 whitesox30 Tim Elko",
"2025/05/10	Connor Joe	CIN	17	Road gray Pete Rose 14 memorial patch Kroger ad patch	2025/05/10 reds17 Connor Joe",
"2025/05/11	Yoendrys Gomez	CHW	94	Home white Mother's Day patch	2025/05/11 whitesox94 Yoendrys Gomez",
"2025/05/11	Ryan Rolison	COL	50	Home white Mother's Day patch	2025/05/11 rockies50 Ryan Rolison",
"2025/05/12	Kendall Graveman	ARI	49	Road black Avnet ad patch	2025/05/12 dbacks49 Kendall Graveman",
"2025/05/13	Moises Ballesteros	CHC	25	Home white Motorola ad patch	2025/05/13 cubs25 Moises Ballesteros",
"2025/05/14	Chayce McDermott	BAL	59	Home black T. Rowe Price ad patch	2025/05/14 orioles59 Chayce McDermott",
"2025/05/14	Colton Gordon	HOU	61	Home white Oxy ad patch	2025/05/14 astros61 Colton Gordon",
"2025/05/14	Dalton Rushing	LAD	68	Home white Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/05/14 dodgers68 Dalton Rushing",
"2025/05/14	Daniel Robert	PHI	48	Home cream IBX ad patch	2025/05/14 phillies48 Daniel Robert",
"2025/05/16	Christian Montes De Oca	ARI	59	City connect Avnet ad patch	2025/05/16 dbacks59 Christian Montes De Oca",
"2025/05/16	Anthony Maldonado	ATH	56	Road gray Armed Forces hat Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/16 athletics56 Anthony Maldonado",
"2025/05/16	Matt Krook	ATH	62	Road gray Armed Forces hat Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/16 athletics62 Matt Krook",
"2025/05/16	Nick Burdi	BOS	68	City connect MassMutual ad patch	2025/05/16 redsox68 Nick Burdi",
"2025/05/16	Vinny Capra	CHW	41	Road black Armed Forces hat	2025/05/16 whitesox41 Vinny Capra",
"2025/05/16	Miguel Castro	CHW	60	Road black Armed Forces hat	2025/05/16 whitesox60 Miguel Castro",
"2025/05/16	Carson Palmquist	COL	45	Road gray Armed Forces hat	2025/05/16 rockies45 Carson Palmquist",
"2025/05/16	Ryan Loutos	LAD	65	Home white Armed Forces hat Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/05/16 dodgers65 Ryan Loutos",
"2025/05/16	Ryan Fitzgerald	MIN	53	Road gray Armed Forces hat	2025/05/16 twins53 Ryan Fitzgerald",
"2025/05/16	Nick Solak	PIT	46	Road gray Armed Forces hat Sheetz ad patch	2025/05/16 pirates46 Nick Solak",
"2025/05/17	Jose Castillo	NYM	54	Road gray Armed Forces hat Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/05/17 mets54 Jose Castillo",
"2025/05/18	Hunter Strickland	LAA	60	Road red Armed Forces hat FBM ad patch	2025/05/18 angels60 Hunter Strickland",
"2025/05/18	Lou Trivino	LAD	58	Home white Armed Forces hat Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/05/18 dodgers58 Lou Trivino",
"2025/05/18	Easton McGee	MIL	50	Home cream Armed Forces hat Bob Uecker memorial patch Northwestern Mutual ad patch	2025/05/18 brewers50 Easton McGee",
"2025/05/18	Carson McCusker	MIN	60	Road gray Armed Forces hat	2025/05/18 twins60 Carson McCusker",
"2025/05/18	Mick Abel	PHI	40	Home cream Armed Forces hat IBX ad patch	2025/05/18 phillies40 Mick Abel",
"2025/05/20	Adrian Houser	CHW	57	Home white	2025/05/20 whitesox57 Adrian Houser",
"2025/05/20	Brandon Walter	HOU	60	Road gray Mens Mental Health Awareness Month patch Oxy ad patch	2025/05/20 astros60 Brandon Walter",
"2025/05/20	Isaac Mattson	PIT	72	Home black Pittsburgh Sheetz ad patch	2025/05/20 pirates72 Isaac Mattson",
"2025/05/22	Robert Hassell III	WSN	57	Home navy	2025/05/22 nationals57 Robert Hassell III",
"2025/05/23	Denzel Clarke	ATH	1	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/23 athletics1 Denzel Clarke",
"2025/05/23	Logan Davidson	ATH	6	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/23 athletics6 Logan Davidson",
"2025/05/23	CJ Alexander	ATH	26	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/23 athletics26 CJ Alexander",
"2025/05/23	Willie MacIver	ATH	65	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/23 athletics65 Willie MacIver",
"2025/05/23	Garrett Hampson	CIN	6	City connect Pete Rose 14 memorial patch Kroger ad patch	2025/05/23 reds6 Garrett Hampson",
"2025/05/23	Blas Castano	SEA	62	Road navy Nintendo Switch 2 ad patch	2025/05/23 mariners62 Blas Castano",
"2025/05/23	Daylen Lile	WSN	51	City connect	2025/05/23 nationals51 Daylen Lile",
"2025/05/24	Terrin Vavra	BAL	54	Road gray T. Rowe Price ad patch	2025/05/24 orioles54 Terrin Vavra",
"2025/05/24	Yaramil Hiraldo	BAL	76	Road gray T. Rowe Price ad patch	2025/05/24 orioles76 Yaramil Hiraldo",
"2025/05/24	Marcelo Mayer	BOS	39	City connect MassMutual ad patch	2025/05/24 redsox39 Marcelo Mayer",
"2025/05/24	Brooks Kriske	CHC	57	Road royal Motorola ad patch	2025/05/24 cubs57 Brooks Kriske",
"2025/05/24	Nic Enright	CLE	59	Road gray Marathon ad patch	2025/05/24 guardians59 Nic Enright",
"2025/05/24	Janson Junk	MIA	26	Road black Mental Health Awareness patch ADT ad patch	2025/05/24 marlins26 Janson Junk",
"2025/05/25	Cooper Hummel	BAL	67	Road gray T. Rowe Price ad patch	2025/05/25 orioles67 Cooper Hummel",
"2025/05/25	Reese McGuire	CHC	20	Road gray Motorola ad patch	2025/05/25 cubs20 Reese McGuire",
"2025/05/25	Chris Stratton	LAD	41	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/05/25 dodgers41 Chris Stratton",
"2025/05/25	Alejandro Osuna	TEX	19	Road royal Energy Transfer ad patch	2025/05/25 rangers19 Alejandro Osuna",
"2025/05/25	Ali Sanchez	TOR	20	Road powder Mens Mental Health Awareness Month patch TD ad patch	2025/05/25 bluejays20 Ali Sanchez",
"2025/05/26	Chadwick Tromp	BAL	41	Home white Memorial Day patch T. Rowe Price ad patch	2025/05/26 orioles41 Chadwick Tromp",
"2025/05/26	John Rave	KCR	26	Home powder white pants Memorial Day patch QuikTrip ad patch	2025/05/26 royals26 John Rave",
"2025/05/26	Chris Taylor	LAA	33	Home white Memorial Day patch FBM ad patch	2025/05/26 angels33 Chris Taylor",
"2025/05/26	Victor Mesa Jr.	MIA	10	Road gray Memorial Day patch ADT ad patch	2025/05/26 marlins10 Victor Mesa Jr.",
"2025/05/26	Braxton Ashcraft	PIT	67	Road gray Memorial Day patch Sheetz ad patch	2025/05/26 pirates67 Braxton Ashcraft",
"2025/05/27	Drew Avans	ATH	35	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/27 athletics35 Drew Avans",
"2025/05/28	Sean Newcomb	ATH	31	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/05/28 athletics31 Sean Newcomb",
"2025/05/28	Andrew Walters	CLE	91	Home white Marathon ad patch	2025/05/28 guardians91 Andrew Walters",
"2025/05/28	Orlando Arcia	COL	8	Road gray	2025/05/28 rockies8 Orlando Arcia",
"2025/05/28	Andrew Hoffmann	KCR	54	Home white QuikTrip ad patch	2025/05/28 royals54 Andrew Hoffmann",
"2025/05/28	Scott Kingery	LAA	13	Home white FBM ad patch	2025/05/28 angels13 Scott Kingery",
"2025/05/28	Matt Thaiss	TBR	34	Home white Mens Mental Health Awareness Month patch	2025/05/28 rays34 Matt Thaiss",
"2025/05/29	Genesis Cabrera	CHC	92	Home powder Motorola ad patch	2025/05/29 cubs92 Genesis Cabrera",
"2025/05/29	Brett de Geus	PHI	74	Home powder IBX ad patch	2025/05/29 phillies74 Brett de Geus",
"2025/05/30	Ildemaro Vargas	ARI	6	City connect Avnet ad patch	2025/05/30 dbacks6 Ildemaro Vargas",
"2025/05/30	Jeff Brigham	ARI	34	City connect Avnet ad patch	2025/05/30 dbacks34 Jeff Brigham",
"2025/05/30	Jose Azocar	ATL	18	Home red Quikrete ad patch	2025/05/30 braves18 Jose Azocar",
"2025/05/30	Dan Altavilla	CHW	58	Road gray	2025/05/30 whitesox58 Dan Altavilla",
"2025/05/30	Dylan Smith	DET	58	Road gray Meijer ad patch	2025/05/30 tigers58 Dylan Smith",
"2025/05/30	Jack Winkler	MIA	63	Home black ADT ad patch	2025/05/30 marlins63 Jack Winkler",
"2025/05/30	Heriberto Hernandez	MIA	64	Home black ADT ad patch	2025/05/30 marlins64 Heriberto Hernandez",
"2025/05/30	Bradgley Rodriguez	SDP	72	City connect Motorola ad patch	2025/05/30 padres72 Bradgley Rodriguez",
"2025/05/31	Jordyn Adams	BAL	80	Home orange orange pants T. Rowe Price ad patch	2025/05/31 orioles80 Jordyn Adams",
"2025/05/31	Keston Hiura	COL	7	Road purple	2025/05/31 rockies7 Keston Hiura",
"2025/05/31	Cole Young	SEA	2	Home white Nintendo ad patch	2025/05/31 mariners2 Cole Young",
"2025/05/31	Ryan Vilade	STL	13	Road powder Stifel ad patch	2025/05/31 cardinals13 Ryan Vilade",
"2025/06/01	Nate Eaton	BOS	40	Road gray Lou Gehrig Day patch MassMutual ad patch	2025/06/01 redsox40 Nate Eaton",
"2025/06/01	Jacob Melton	HOU	31	Home navy Lou Gehrig Day patch Oxy ad patch	2025/06/01 astros31 Jacob Melton",
"2025/06/01	Codi Heuer	TEX	54	Home powder Lou Gehrig Day patch Energy Transfer ad patch	2025/06/01 rangers54 Codi Heuer",
"2025/06/02	Will Klein	LAD	61	Home white Lou Gehrig Day patch Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/06/02 dodgers61 Will Klein",
"2025/06/03	Jac Caglianone	KCR	14	Road powder QuikTrip ad patch	2025/06/03 royals14 Jac Caglianone",
"2025/06/03	Jose Urena	LAD	47	Home white Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/06/03 dodgers47 Jose Urena",
"2025/06/04	Wade Miley	CIN	22	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/06/04 reds22 Wade Miley",
"2025/06/04	Dominic Smith	SFG	7	Home cream Chevrolet ad patch	2025/06/04 giants7 Dominic Smith",
"2025/06/04	Andrew Knizner	SFG	21	Home cream Chevrolet ad patch	2025/06/04 giants21 Andrew Knizner",
"2025/06/04	Daniel Johnson	SFG	56	Home cream Chevrolet ad patch	2025/06/04 giants56 Daniel Johnson",
"2025/06/05	Michael Kelly	ATH	49	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/06/05 athletics49 Michael Kelly",
"2025/06/05	Owen White	CHW	67	Home white	2025/06/05 whitesox67 Owen White",
"2025/06/05	Thomas Hatch	KCR	38	Road powder QuikTrip ad patch	2025/06/05 royals38 Thomas Hatch",
"2025/06/06	Craig Kimbrel	ATL	46	Road navy Quikrete ad patch	2025/06/06 braves46 Craig Kimbrel",
"2025/06/06	Dylan Dodd	ATL	53	Road navy Quikrete ad patch	2025/06/06 braves53 Dylan Dodd",
"2025/06/06	Kyle Teel	CHW	8	City connect red hat	2025/06/06 whitesox8 Kyle Teel",
"2025/06/06	Dom Nunez	CLE	46	City connect Marathon ad patch	2025/06/06 guardians46 Dom Nunez",
"2025/06/06	Ryan Ritter	COL	8	City connect	2025/06/06 rockies8 Ryan Ritter",
"2025/06/06	Orlando Arcia	COL	11	City connect	2025/06/06 rockies11 Orlando Arcia",
"2025/06/06	Jahmai Jones	DET	18	Home white Meijer ad patch	2025/06/06 tigers18 Jahmai Jones",
"2025/06/06	Travis Adams	MIN	45	City connect	2025/06/06 twins45 Travis Adams",
"2025/06/06	Alan Rangel	PHI	56	Road gray IBX ad patch	2025/06/06 phillies56 Alan Rangel",
"2025/06/07	Aramis Garcia	ARI	66	Road black Avnet ad patch	2025/06/07 dbacks66 Aramis Garcia",
"2025/06/07	Austin Cox	ATL	68	Road red Quikrete ad patch	2025/06/07 braves68 Austin Cox",
"2025/06/07	Joe La Sorsa	CIN	66	Home red Pete Rose 14 memorial patch Kroger ad patch	2025/06/07 reds66 Joe La Sorsa",
"2025/06/07	Trevor Richards	KCR	43	Road powder QuikTrip ad patch	2025/06/07 royals43 Trevor Richards",
"2025/06/07	Otto Kemp	PHI	4	Road gray IBX ad patch	2025/06/07 phillies4 Otto Kemp",
"2025/06/07	Brett Sullivan	PIT	59	Home black Pittsburgh Sheetz ad patch	2025/06/07 pirates59 Brett Sullivan",
"2025/06/08	Kyle Backhus	ARI	43	Road gray black crown hat Avnet ad patch	2025/06/08 dbacks43 Kyle Backhus",
"2025/06/08	Jose Ruiz	ATL	63	Road navy Quikrete ad patch	2025/06/08 braves63 Jose Ruiz",
"2025/06/08	Scott Blewett	BAL	67	Road gray T. Rowe Price ad patch	2025/06/08 orioles67 Scott Blewett",
"2025/06/08	Tyler Alexander	CHW	70	Home white	2025/06/08 whitesox70 Tyler Alexander",
"2025/06/08	Ian Seymour	TBR	61	Home white	2025/06/08 rays61 Ian Seymour",
"2025/06/09	Austin Wynns	ATH	29	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/06/09 athletics29 Austin Wynns",
"2025/06/09	Dylan Dodd	ATL	46	Road gray Quikrete ad patch	2025/06/09 braves46 Dylan Dodd",
"2025/06/09	Roman Anthony	BOS	48	Home white MassMutual ad patch	2025/06/09 redsox48 Roman Anthony",
"2025/06/09	Brian Van Belle	BOS	77	Home white MassMutual ad patch	2025/06/09 redsox77 Brian Van Belle",
"2025/06/09	Justin Garza	NYM	71	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/06/09 mets71 Justin Garza",
"2025/06/09	Spencer Turnbull	TOR	12	Road royal TD patch	2025/06/09 bluejays12 Spencer Turnbull",
"2025/06/10	Tayler Scott	ARI	53	Home red Avnet ad patch	2025/06/10 dbacks53 Tayler Scott",
"2025/06/10	Luis Vazquez	BAL	52	Home white T. Rowe Price ad patch	2025/06/10 orioles52 Luis Vazquez",
"2025/06/10	Roman Anthony	BOS	19	Home white MassMutual ad patch	2025/06/10 redsox19 Roman Anthony",
"2025/06/10	Grant Taylor	CHW	31	Road black	2025/06/10 whitesox31 Grant Taylor",
"2025/06/10	LaMonte Wade Jr.	LAA	35	Home white FBM ad patch	2025/06/10 angels35 LaMonte Wade Jr.",
"2025/06/11	Jorge Alcala	BOS	71	Home white MassMutual ad patch	2025/06/11 redsox71 Jorge Alcala",
"2025/06/11	Logan Porter	SFG	13	Road gray Chevrolet ad patch	2025/06/11 giants13 Logan Porter",
"2025/06/11	Will Robertson	TOR	39	Road royal TD patch	2025/06/11 bluejays39 Will Robertson",
"2025/06/12	Matt Gage	DET	99	Road gray Meijer ad patch	2025/06/12 tigers99 Matt Gage",
"2025/06/12	Jacob Misiorowski	MIL	33	City connect Bob Uecker memorial patch Northwestern Mutual ad patch	2025/06/12 brewers33 Jacob Misiorowski",
"2025/06/12	Joey Wentz	MIN	63	Home white	2025/06/12 twins63 Joey Wentz",
"2025/06/12	Scott Effross	NYY	57	Road gray Starr ad patch	2025/06/12 yankees57 Scott Effross",
"2025/06/12	Andre Granillo	STL	65	Road gray Stifel ad patch	2025/06/12 cardinals65 Andre Granillo",
"2025/06/13	Christian Moore	LAA	4	Road red FBM ad patch	2025/06/13 angels4 Christian Moore",
"2025/06/13	Drew Avans	MIL	18	City connect Bob Uecker memorial patch Northwestern Mutual ad patch	2025/06/13 brewers18 Drew Avans",
"2025/06/13	Jacob Misiorowski	MIL	32	City connect Bob Uecker memorial patch Northwestern Mutual ad patch	2025/06/13 brewers32 Jacob Misiorowski",
"2025/06/13	Zach Pop	SEA	35	City connect Nintendo ad patch	2025/06/13 mariners35 Zach Pop",
"2025/06/14	Ryan Noda	CHW	29	Road gray	2025/06/14 whitesox29 Ryan Noda",
"2025/06/14	Aaron Civale	CHW	43	Road gray	2025/06/14 whitesox43 Aaron Civale",
"2025/06/14	Luis Guillorme	HOU	0	Home white Oxy ad patch	2025/06/14 astros0 Luis Guillorme",
"2025/06/14	Cooper Hummel	HOU	16	Home white Oxy ad patch	2025/06/14 astros16 Cooper Hummel",
"2025/06/14	Ryan Loutos	WSN	52	City connect	2025/06/14 nationals52 Ryan Loutos",
"2025/06/15	Anthony DeSclafani	ARI	21	Home cream Father's Day patch Avnet ad patch	2025/06/15 dbacks21 Anthony DeSclafani",
"2025/06/15	Freddy Tarnok	MIA	56	Road gray Father's Day patch ADT ad patch	2025/06/15 marlins56 Freddy Tarnok",
"2025/06/15	Trenton Brooks	SDP	41	Road sand Father's Day patch Motorola ad patch	2025/06/15 padres41 Trenton Brooks",
"2025/06/15	Joey Lucchesi	SFG	57	Road gray Father's Day patch Chevrolet ad patch	2025/06/15 giants57 Joey Lucchesi",
"2025/06/16	Jason Alexander	HOU	54	Road gray orange brim hat Oxy ad patch	2025/06/16 astros54 Jason Alexander",
"2025/06/16	Bryce Johnson	SDP	29	Road sand Motorola ad patch	2025/06/16 padres29 Bryce Johnson",
"2025/06/16	Forrest Whitley	TBR	38	Home white	2025/06/16 rays38 Forrest Whitley",
"2025/06/16	Brady House	WSN	55	Home navy	2025/06/16 nationals55 Brady House",
"2025/06/17	Carlos Hernandez	DET	49	Home white Meijer ad patch	2025/06/17 tigers49 Carlos Hernandez",
"2025/06/17	Rafael Devers	SFG	16	City connect Chevrolet ad patch	2025/06/17 giants16 Rafael Devers",
"2025/06/17	Justin Bruihl	TOR	58	Home white TD patch	2025/06/17 bluejays58 Justin Bruihl",
"2025/06/19	Aramis Garcia	ARI	35	Road black Avnet ad patch	2025/06/19 dbacks35 Aramis Garcia",
"2025/06/19	Jack Little	LAD	81	Home white Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/06/19 dodgers81 Jack Little",
"2025/06/19	Robinson Pina	MIA	81	Home white ADT ad patch	2025/06/19 marlins81 Robinson Pina",
"2025/06/19	Jayvien Sandridge	NYY	88	Home white Starr ad patch	2025/06/19 yankees88 Jayvien Sandridge",
"2025/06/20	Didier Fuentes	ATL	75	Road gray Quikrete ad patch	2025/06/20 braves75 Didier Fuentes",
"2025/06/20	Jake Palisch	CHW	60	Road gray	2025/06/20 whitesox60 Jake Palisch",
"2025/06/20	Wikelman Gonzalez	CHW	66	Road gray	2025/06/20 whitesox66 Wikelman Gonzalez",
"2025/06/21	Josh Simpson	MIA	66	City connect ADT ad patch	2025/06/21 marlins66 Josh Simpson",
"2025/06/21	Paul Gervase	TBR	54	Home throwback	2025/06/21 rays54 Paul Gervase",
"2025/06/22	Jack Perkins	ATH	50	Home white Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/06/22 athletics50 Jack Perkins",
"2025/06/23	James McCann	ARI	8	Road black Avnet ad patch	2025/06/23 dbacks8 James McCann",
"2025/06/23	Michael Fulmer	CHC	49	Road gray Motorola ad patch	2025/06/23 cubs49 Michael Fulmer",
"2025/06/23	Travis Jankowski	NYM	21	Home black Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/06/23 mets21 Travis Jankowski",
"2025/06/23	Richard Lovelady	NYM	57	Home black Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/06/23 mets57 Richard Lovelady",
"2025/06/23	Allan Winans	NYY	62	Road gray Starr ad patch	2025/06/23 yankees62 Allan Winans",
"2025/06/24	Chase Burns	CIN	26	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/06/24 reds26 Chase Burns",
"2025/06/24	Jordan Weems	HOU	51	Home navy orange brim hat Oxy ad patch	2025/06/24 astros51 Jordan Weems",
"2025/06/24	Michael Darrell-Hicks	PIT	41	Road gray Sheetz ad patch	2025/06/24 pirates41 Michael Darrell-Hicks",
"2025/06/24	Garrett Hampson	STL	13	Home white Stifel ad patch	2025/06/24 cardinals13 Garrett Hampson",
"2025/06/25	Ryan Vilade	CIN	46	Home white Pete Rose 14 memorial patch Kroger ad patch	2025/06/25 reds46 Ryan Vilade",
"2025/06/25	Jonathan Pintaro	NYM	91	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/06/25 mets91 Jonathan Pintaro",
"2025/06/26	Dietrich Enns	DET	51	Home white Meijer ad patch	2025/06/26 tigers51 Dietrich Enns",
"2025/06/27	Colin Poche	NYM	83	Road gray Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/06/27 mets83 Colin Poche",
"2025/06/27	Genesis Cabrera	PIT	92	City connect white pants Sheetz ad patch	2025/06/27 pirates92 Genesis Cabrera",
"2025/06/27	Carson Seymour	SFG	77	Road gray Chevrolet ad patch	2025/06/27 giants77 Carson Seymour",
"2025/06/27	Michael Helman	TEX	24	City connect Energy Transfer ad patch	2025/06/27 rangers24 Michael Helman",
"2025/06/28	John Curtiss	ARI	46	Home cream Avnet ad patch	2025/06/28 dbacks46 John Curtiss",
"2025/06/28	Kevin Herget	ATL	57	City connect Quikrete ad patch	2025/06/28 braves57 Kevin Herget",
"2025/06/28	Juan Burgos	SEA	67	Road navy Nintendo Switch 2 ad patch	2025/06/28 mariners67 Juan Burgos",
"2025/06/28	Joe Rock	TBR	68	Road navy	2025/06/28 rays68 Joe Rock",
"2025/06/30	Colby Thomas	ATH	32	Road yellow Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/06/30 athletics32 Colby Thomas",
"2025/06/30	Jordan Hicks	BOS	46	Home white MassMutual ad patch	2025/06/30 redsox46 Jordan Hicks",
"2025/06/30	Geoff Hartlieb	NYY	64	Road gray Starr ad patch	2025/06/30 yankees64 Geoff Hartlieb",
"2025/07/01	Jacob Stallings	BAL	25	Road gray T. Rowe Price ad patch	2025/07/01 orioles25 Jacob Stallings",
"2025/07/01	Sam Benschoter	CIN	63	Road gray Pete Rose 14 memorial patch Kroger ad patch	2025/07/01 reds63 Sam Benschoter",
"2025/07/01	Austin Nola	COL	20	Home white York Space Systems ad patch	2025/07/01 rockies20 Austin Nola",
"2025/07/01	Yanquiel Fernandez	COL	35	Home white York Space Systems ad patch	2025/07/01 rockies35 Yanquiel Fernandez",
"2025/07/01	Anthony Seigler	MIL	18	Road gray Bob Uecker memorial patch Northwestern Mutual ad patch	2025/07/01 brewers18 Anthony Seigler",
"2025/07/01	Billy McKinney	TEX	23	Home white blue hat Energy Transfer ad patch	2025/07/01 rangers23 Billy McKinney",
"2025/07/02	Jake Woodford	ARI	41	Home cream Avnet ad patch	2025/07/02 dbacks41 Jake Woodford",
"2025/07/02	Corbin Martin	BAL	48	Road gray T. Rowe Price ad patch	2025/07/02 orioles48 Corbin Martin",
"2025/07/02	Zack Short	HOU	38	Road orange Oxy ad patch	2025/07/02 astros38 Zack Short",
"2025/07/02	Clayton Beeter	NYY	29	Road gray Starr ad patch	2025/07/02 yankees29 Clayton Beeter",
"2025/07/02	Eduarniel Nunez	SDP	79	Road sand Motorola ad patch	2025/07/02 padres79 Eduarniel Nunez",
"2025/07/02	Joe Jacques	SEA	71	Home white Nintendo ad patch	2025/07/02 mariners71 Joe Jacques",
"2025/07/03	Chad Stevens	LAA	21	Road red FBM ad patch	2025/07/03 angels21 Chad Stevens",
"2025/07/03	Esteury Ruiz	LAD	27	Home white Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/07/03 dodgers27 Esteury Ruiz",
"2025/07/03	Rico Garcia	NYM	50	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/07/03 mets50 Rico Garcia",
"2025/07/03	Sergio Alcantara	SFG	39	Road black Chevrolet ad patch	2025/07/03 giants39 Sergio Alcantara",
"2025/07/03	Ha-Seong Kim	TBR	7	Road navy 4th of July hat	2025/07/03 rays7 Ha-Seong Kim",
"2025/07/04	Colson Montgomery	CHW	12	Road black 4th of July hat	2025/07/04 whitesox12 Colson Montgomery",
"2025/07/04	Lazaro Estrada	TOR	60	City connect 4th of July hat TD patch	2025/07/04 bluejays60 Lazaro Estrada",
"2025/07/05	Zach Pop	NYM	56	City connect Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/07/05 mets56 Zach Pop",
"2025/07/05	Scott Alexander	SFG	54	Road gray Chevrolet ad patch	2025/07/05 giants54 Scott Alexander",
"2025/07/05	Robinson Pina	TOR	33	Home white TD patch	2025/07/05 bluejays33 Robinson Pina",
"2025/07/06	Tristin English	ARI	30	Home cream Avnet ad patch	2025/07/06 dbacks30 Tristin English",
"2025/07/06	Alex Jackson	BAL	70	Road gray T. Rowe Price ad patch	2025/07/06 orioles70 Alex Jackson",
"2025/07/07	Tristan Gray	CHW	41	Home white	2025/07/07 whitesox41 Tristan Gray",
"2025/07/07	Kenedy Corona	HOU	47	City connect Oxy ad patch	2025/07/07 astros47 Kenedy Corona",
"2025/07/07	Julian Fernandez	LAD	62	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/07/07 dodgers62 Julian Fernandez",
"2025/07/07	Andrew Vaughn	MIL	28	Home cream Bob Uecker memorial patch Northwestern Mutual ad patch	2025/07/07 brewers28 Andrew Vaughn",
"2025/07/08	Isaiah Campbell	BOS	48	Home white MassMutual ad patch	2025/07/08 redsox48 Isaiah Campbell",
"2025/07/08	Cam Devanney	KCR	17	Home white QuikTrip ad patch	2025/07/08 royals17 Cam Devanney",
"2025/07/08	Alexis Diaz	LAD	40	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/07/08 dodgers40 Alexis Diaz",
"2025/07/08	Alex Carrillo	NYM	84	Road gray Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/07/08 mets84 Alex Carrillo",
"2025/07/08	Luis Garcia	WSN	9	Road gray AARP ad patch	2025/07/08 nationals9 Luis Garcia",
"2025/07/09	Carson Fulmer	LAA	49	Home throwback FBM ad patch	2025/07/09 angels49 Carson Fulmer",
"2025/07/09	Anthony Misiewicz	MIN	57	Home white	2025/07/09 twins57 Anthony Misiewicz",
"2025/07/09	Cam Schlittler	NYY	31	Home white Starr ad patch	2025/07/09 yankees31 Cam Schlittler",
"2025/07/10	Bryan Baker	TBR	47	Road navy	2025/07/10 rays47 Bryan Baker",
"2025/07/11	Will Robertson	CHW	37	City connect red hat Bobby Jenks 45 memorial patch	2025/07/11 whitesox37 Will Robertson",
"2025/07/11	Brice Matthews	HOU	28	Home orange Oxy ad patch	2025/07/11 astros28 Brice Matthews",
"2025/07/11	Yohan Ramirez	PIT	49	Road black Sheetz ad patch	2025/07/11 pirates49 Yohan Ramirez",
"2025/07/12	Joey Wentz	ATL	33	Road gray Quikrete ad patch	2025/07/12 braves33 Joey Wentz",
"2025/07/12	Nacho Alvarez Jr.	ATL	67	Road gray Quikrete ad patch	2025/07/12 braves67 Nacho Alvarez Jr.",
"2025/07/13	Wander Suero	ATL	45	Road gray Quikrete ad patch	2025/07/13 braves45 Wander Suero",
"2025/07/17	Rico Garcia	NYY	50	Road gray Starr ad patch	2025/07/17 yankees50 Rico Garcia",
"2025/07/18	Sergio Alcantara	ARI	3	City connect Avnet ad patch	2025/07/18 dbacks3 Sergio Alcantara",
"2025/07/18	Trevor Richards	ARI	38	City connect Avnet ad patch	2025/07/18 dbacks38 Trevor Richards",
"2025/07/18	Dane Dunning	ATL	34	Home red Quikrete ad patch	2025/07/18 braves34 Dane Dunning",
"2025/07/18	John Rave	KCR	16	Road gray QuikTrip ad patch	2025/07/18 royals16 John Rave",
"2025/07/18	Adam Frazier	KCR	26	Road gray QuikTrip ad patch	2025/07/18 royals26 Adam Frazier",
"2025/07/18	Matt Gage	SFG	93	Road gray Chevrolet ad patch	2025/07/18 giants93 Matt Gage",
"2025/07/18	Cody Freeman	TEX	39	City connect Energy Transfer ad patch	2025/07/18 rangers39 Cody Freeman",
"2025/07/18	Rowdy Tellez	TEX	44	City connect Energy Transfer ad patch	2025/07/18 rangers44 Rowdy Tellez",
"2025/07/19	Kevin Herget	NYM	57	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/07/19 mets57 Kevin Herget",
"2025/07/20	Jon Singleton	HOU	35	Road orange orange brim hat Oxy ad patch	2025/07/20 astros35 Jon Singleton",
"2025/07/21	Sandy Leon	ATL	9	Home white Quikrete ad patch	2025/07/21 braves9 Sandy Leon",
"2025/07/21	Brandyn Garcia	SEA	43	Home white Nintendo ad patch	2025/07/21 mariners43 Brandyn Garcia",
"2025/07/22	Carlos Cortes	ATH	26	Road yellow Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/07/22 athletics26 Carlos Cortes",
"2025/07/22	Rich Hill	KCR	35	Road gray QuikTrip ad patch	2025/07/22 royals35 Rich Hill",
"2025/07/22	Stuart Fairchild	TBR	20	City connect	2025/07/22 rays20 Stuart Fairchild",
"2025/07/22	Konnor Pilkington	WSN	45	Home white AARP ad patch	2025/07/22 nationals45 Konnor Pilkington",
"2025/07/23	Ben Bowden	ATH	62	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/07/23 athletics62 Ben Bowden",
"2025/07/23	Hunter Stratton	ATL	65	Home white Quikrete ad patch	2025/07/23 braves65 Hunter Stratton",
"2025/07/23	Troy Melton	DET	52	Road gray Meijer ad patch	2025/07/23 tigers52 Troy Melton",
"2025/07/24	Geoff Hartlieb	DET	64	Home white Meijer ad patch	2025/07/24 tigers64 Geoff Hartlieb",
"2025/07/25	Jeremiah Jackson	BAL	82	City connect HoF weekend hat T. Rowe Price ad patch	2025/07/25 orioles82 Jeremiah Jackson",
"2025/07/25	Nick Anderson	COL	61	Road gray HoF weekend hat York Space Systems ad patch	2025/07/25 rockies61 Nick Anderson",
"2025/07/25	Josh Naylor	SEA	12	Road navy HoF weekend hat Nintendo Switch 2 ad patch	2025/07/25 mariners12 Josh Naylor",
"2025/07/26	Brandyn Garcia	ARI	55	Road gray HoF weekend hat Avnet ad patch	2025/07/26 dbacks55 Brandyn Garcia",
"2025/07/26	Warming Bernabel	COL	25	Road purple HoF weekend hat York Space Systems ad patch	2025/07/26 rockies25 Warming Bernabel",
"2025/07/26	Luke Jackson	DET	49	Home white HoF weekend hat Meijer ad patch	2025/07/26 tigers49 Luke Jackson",
"2025/07/26	Ryan McMahon	NYY	19	Home white HoF weekend hat Starr ad patch	2025/07/26 yankees19 Ryan McMahon",
"2025/07/26	Tristan Gray	TBR	10	Road navy HoF weekend hat	2025/07/26 rays10 Tristan Gray",
"2025/07/27	Randal Grichuk	KCR	15	Home powder white pants HoF weekend hat QuikTrip ad patch	2025/07/27 royals15 Randal Grichuk",
"2025/07/27	Luke Maile	KCR	17	Home powder white pants HoF weekend hat QuikTrip ad patch	2025/07/27 royals17 Luke Maile",
"2025/07/27	Gregory Soto	NYM	65	Road royal HoF weekend hat Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/07/27 mets65 Gregory Soto",
"2025/07/27	Amed Rosario	NYY	14	Home white HoF weekend hat Starr ad patch	2025/07/27 yankees14 Amed Rosario",
"2025/07/28	Erick Fedde	ATL	22	Road gray Quikrete ad patch	2025/07/28 braves22 Erick Fedde",
"2025/07/28	Carson Whisenhunt	SFG	88	Home cream Chevrolet ad patch	2025/07/28 giants88 Carson Whisenhunt",
"2025/07/29	Elvin Rodriguez	BAL	83	Home white T. Rowe Price ad patch	2025/07/29 orioles83 Elvin Rodriguez",
"2025/07/29	Houston Roth	BAL	95	Home white T. Rowe Price ad patch	2025/07/29 orioles95 Houston Roth",
"2025/07/29	Chris Paddack	DET	40	Home white Meijer ad patch	2025/07/29 tigers40 Chris Paddack",
"2025/07/29	Alex Freeland	LAD	76	Road gray Los Angeles Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/07/29 dodgers76 Alex Freeland",
"2025/07/29	Troy Johnston	MIA	75	Road gray ADT ad patch	2025/07/29 marlins75 Troy Johnston",
"2025/07/29	Danny Jansen	MIL	33	Home cream Bob Uecker memorial patch Northwestern Mutual ad patch	2025/07/29 brewers33 Danny Jansen",
"2025/07/29	Pierson Ohl	MIN	62	Home cream Securian Financial ad patch	2025/07/29 twins62 Pierson Ohl",
"2025/07/29	Nick Fortes	TBR	40	Road navy	2025/07/29 rays40 Nick Fortes",
"2025/07/29	Seranthony Dominguez	TOR	48	Road gray TD patch	2025/07/29 bluejays48 Seranthony Dominguez",
"2025/07/30	Luis Garcia	LAA	66	Home white FBM ad patch	2025/07/30 angels66 Luis Garcia",
"2025/07/30	Noah Davis	MIN	63	Home white Securian Financial ad patch	2025/07/30 twins63 Noah Davis",
"2025/07/30	Austin Slater	NYY	29	Home white Starr ad patch	2025/07/30 yankees29 Austin Slater",
"2025/07/30	Caleb Ferguson	SEA	43	Road navy Nintendo Switch 2 ad patch	2025/07/30 mariners43 Caleb Ferguson",
"2025/07/30	Luis Curvelo	TEX	57	Road royal Energy Transfer ad patch	2025/07/30 rangers57 Luis Curvelo",
"2025/07/31	Tyler Kinley	ATL	45	Road navy Quikrete ad patch	2025/07/31 braves45 Tyler Kinley",
"2025/07/31	Carlos Carrasco	ATL	59	Road navy Quikrete ad patch	2025/07/31 braves59 Carlos Carrasco",
"2025/07/31	Ke'Bryan Hayes	CIN	3	Home red Pete Rose 14 memorial patch Kroger ad patch	2025/07/31 reds3 Ke'Bryan Hayes",
"2025/07/31	Kyle Finnegan	DET	64	Road gray Meijer ad patch	2025/07/31 tigers64 Kyle Finnegan",
"2025/07/31	Tyler Rogers	NYM	71	Home black Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/07/31 mets71 Tyler Rogers",
"2025/07/31	Eugenio Suarez	SEA	28	City connect Nintendo ad patch	2025/07/31 mariners28 Eugenio Suarez",
"2025/08/01	Tyler Locklear	ARI	28	Road gray black crown hat Avnet ad patch	2025/08/01 dbacks28 Tyler Locklear",
"2025/08/01	Connor Kaiser	ARI	65	Road gray black crown hat Avnet ad patch	2025/08/01 dbacks65 Connor Kaiser",
"2025/08/01	Eduarniel Nunez	ATH	54	Home kelly green Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/08/01 athletics54 Eduarniel Nunez",
"2025/08/01	Luis Morales	ATH	58	Home kelly green Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/08/01 athletics58 Luis Morales",
"2025/08/01	Steven Matz	BOS	41	City connect MassMutual ad patch	2025/08/01 redsox41 Steven Matz",
"2025/08/01	Willi Castro	CHC	1	Home powder Ryne Sandberg 23 memorial patch Motorola ad patch	2025/08/01 cubs1 Willi Castro",
"2025/08/01	Taylor Rogers	CHC	17	Home powder Ryne Sandberg 23 memorial patch Motorola ad patch	2025/08/01 cubs17 Taylor Rogers",
"2025/08/01	Andrew Kittredge	CHC	59	Home powder Ryne Sandberg 23 memorial patch Motorola ad patch	2025/08/01 cubs59 Andrew Kittredge",
"2025/08/01	Corey Julks	CHW	32	Road black Bobby Jenks 45 memorial patch	2025/08/01 whitesox32 Corey Julks",
"2025/08/01	Dugan Darnell	COL	52	City connect York Space Systems ad patch	2025/08/01 rockies52 Dugan Darnell",
"2025/08/01	Rafael Montero	DET	99	Road gray Meijer ad patch	2025/08/01 tigers99 Rafael Montero",
"2025/08/01	Carlos Correa	HOU	1	Road orange Oxy ad patch	2025/08/01 astros1 Carlos Correa",
"2025/08/01	Jesus Sanchez	HOU	4	Road orange Oxy ad patch	2025/08/01 astros4 Jesus Sanchez",
"2025/08/01	Ramon Urias	HOU	29	Road orange Oxy ad patch	2025/08/01 astros29 Ramon Urias",
"2025/08/01	Mike Yastrzemski	KCR	18	Road gray QuikTrip ad patch	2025/08/01 royals18 Mike Yastrzemski",
"2025/08/01	Oswald Peraza	LAA	10	Home white FBM ad patch	2025/08/01 angels10 Oswald Peraza",
"2025/08/01	Andrew Chafin	LAA	39	Home white FBM ad patch	2025/08/01 angels39 Andrew Chafin",
"2025/08/01	Alex Call	LAD	12	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/08/01 dodgers12 Alex Call",
"2025/08/01	Brock Stewart	LAD	41	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/08/01 dodgers41 Brock Stewart",
"2025/08/01	Paul Gervase	LAD	65	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/08/01 dodgers65 Paul Gervase",
"2025/08/01	Jakob Marsee	MIA	87	Home black ADT ad patch	2025/08/01 marlins87 Jakob Marsee",
"2025/08/01	Brandon Lockridge	MIL	20	Road navy Bob Uecker memorial patch Northwestern Mutual ad patch	2025/08/01 brewers20 Brandon Lockridge",
"2025/08/01	Austin Martin	MIN	16	Road gray Securian Financial ad patch	2025/08/01 twins16 Austin Martin",
"2025/08/01	Alan Roden	MIN	19	Road gray Securian Financial ad patch	2025/08/01 twins19 Alan Roden",
"2025/08/01	Erasmo Ramirez	MIN	30	Road gray Securian Financial ad patch	2025/08/01 twins30 Erasmo Ramirez",
"2025/08/01	Jose Urena	MIN	54	Road gray Securian Financial ad patch	2025/08/01 twins54 Jose Urena",
"2025/08/01	Cedric Mullins	NYM	28	Home black Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/08/01 mets28 Cedric Mullins",
"2025/08/01	Ryan Helsley	NYM	56	Home black Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/08/01 mets56 Ryan Helsley",
"2025/08/01	David Bednar	NYY	53	Road gray Starr ad patch	2025/08/01 yankees53 David Bednar",
"2025/08/01	Jake Bird	NYY	59	Road gray Starr ad patch	2025/08/01 yankees59 Jake Bird",
"2025/08/01	Jose Caballero	NYY	72	Road gray Starr ad patch	2025/08/01 yankees72 Jose Caballero",
"2025/08/01	Camilo Doval	NYY	75	Road gray Starr ad patch	2025/08/01 yankees75 Camilo Doval",
"2025/08/01	Harrison Bader	PHI	2	City connect IBX ad patch	2025/08/01 phillies2 Harrison Bader",
"2025/08/01	Rob Thomson	PHI	49	City connect IBX ad patch	2025/08/01 phillies49 Rob Thomson",
"2025/08/01	Jhoan Duran	PHI	59	City connect IBX ad patch	2025/08/01 phillies59 Jhoan Duran",
"2025/08/01	Ramon Laureano	SDP	5	City connect Motorola ad patch	2025/08/01 padres5 Ramon Laureano",
"2025/08/01	Mason Miller	SDP	22	City connect Motorola ad patch	2025/08/01 padres22 Mason Miller",
"2025/08/01	Ryan O'Hearn	SDP	32	City connect Motorola ad patch	2025/08/01 padres32 Ryan O'Hearn",
"2025/08/01	JP Sears	SDP	38	City connect Motorola ad patch	2025/08/01 padres38 JP Sears",
"2025/08/01	Freddy Fermin	SDP	54	City connect Motorola ad patch	2025/08/01 padres54 Freddy Fermin",
"2025/08/01	Kai-Wei Teng	SFG	66	Road gray Chevrolet ad patch	2025/08/01 giants66 Kai-Wei Teng",
"2025/08/01	Jose Butto	SFG	70	Road gray Chevrolet ad patch	2025/08/01 giants70 Jose Butto",
"2025/08/01	Griffin Jax	TBR	22	City connect	2025/08/01 rays22 Griffin Jax",
"2025/08/01	Hunter Feduccia	TBR	30	City connect	2025/08/01 rays30 Hunter Feduccia",
"2025/08/01	Merrill Kelly	TEX	23	Road gray Energy Transfer ad patch	2025/08/01 rangers23 Merrill Kelly",
"2025/08/01	Danny Coulombe	TEX	54	Road gray Energy Transfer ad patch	2025/08/01 rangers54 Danny Coulombe",
"2025/08/01	Phil Maton	TEX	88	Road gray Energy Transfer ad patch	2025/08/01 rangers88 Phil Maton",
"2025/08/01	Ty France	TOR	2	City connect TD patch	2025/08/01 bluejays2 Ty France",
"2025/08/01	Louis Varland	TOR	77	City connect TD patch	2025/08/01 bluejays77 Louis Varland",
"2025/08/02	Jonathan Ornelas	ATL	19	Road navy Speedway Classic Quikrete ad patch	2025/08/02 braves19 Jonathan Ornelas",
"2025/08/02	Dietrich Enns	BAL	71	Road orange T. Rowe Price ad patch	2025/08/02 orioles71 Dietrich Enns",
"2025/08/02	Dustin May	BOS	85	Home yellow MassMutual ad patch	2025/08/02 redsox85 Dustin May",
"2025/08/02	Michael Soroka	CHC	41	Home royal Ryne Sandberg 23 Motorola ad patch	2025/08/02 cubs41 Michael Soroka",
"2025/08/02	Miguel Andujar	CIN	38	Home white Speedway Classic Kroger ad patch	2025/08/02 reds38 Miguel Andujar",
"2025/08/02	Zack Littell	CIN	52	Home white Speedway Classic Kroger ad patch	2025/08/02 reds52 Zack Littell",
"2025/08/02	Carlos Hernandez	CLE	40	Home red Marathon ad patch	2025/08/02 guardians40 Carlos Hernandez",
"2025/08/02	C.J. Kayfus	CLE	63	Home red Marathon ad patch	2025/08/02 guardians63 C.J. Kayfus",
"2025/08/02	Charlie Morton	DET	50	Road gray Meijer ad patch	2025/08/02 tigers50 Charlie Morton",
"2025/08/02	Bailey Falter	KCR	36	Road powder QuikTrip ad patch	2025/08/02 royals36 Bailey Falter",
"2025/08/02	Ryan Bergert	KCR	38	Road powder QuikTrip ad patch	2025/08/02 royals38 Ryan Bergert",
"2025/08/02	Bryce Teodosio	LAA	22	Home white FBM ad patch	2025/08/02 angels22 Bryce Teodosio",
"2025/08/02	Adrian Houser	TBR	37	Home throwback	2025/08/02 rays37 Adrian Houser",
"2025/08/03	Ryan Noda	BAL	41	Road gray T. Rowe Price ad patch	2025/08/03 orioles41 Ryan Noda",
"2025/08/03	Curtis Mead	CHW	29	Road black Bobby Jenks 45 memorial patch	2025/08/03 whitesox29 Curtis Mead",
"2025/08/03	John Rooney	HOU	67	Road orange orange brim hat Oxy ad patch	2025/08/03 astros67 John Rooney",
"2025/08/03	Nestor Cortes Jr.	SDP	65	Home camo brown Motorola ad patch	2025/08/03 padres65 Nestor Cortes Jr.",
"2025/08/04	Andrew Hoffmann	ARI	56	Home cream Avnet ad patch	2025/08/04 dbacks56 Andrew Hoffmann",
"2025/08/04	Vidal Brujan	BAL	40	Road gray T. Rowe Price ad patch	2025/08/04 orioles40 Vidal Brujan",
"2025/08/04	Dom Hamel	NYM	53	Home white Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/08/04 mets53 Dom Hamel",
"2025/08/05	Bryan Hudson	CHW	60	Road black Bobby Jenks 45 memorial patch	2025/08/05 whitesox60 Bryan Hudson",
"2025/08/05	Thomas Hatch	MIN	56	Road navy Securian Financial ad patch	2025/08/05 twins56 Thomas Hatch",
"2025/08/05	Cam Sanders	PIT	64	Home white Dave Parker COBRA memorial chest patch Sheetz ad patch	2025/08/05 pirates64 Cam Sanders",
"2025/08/05	Buddy Kennedy	TOR	24	Road gray TD patch	2025/08/05 bluejays24 Buddy Kennedy",
"2025/08/05	Clayton Beeter	WSN	39	Home navy AARP ad patch	2025/08/05 nationals39 Clayton Beeter",
"2025/08/05	PJ Poulin	WSN	50	Home navy AARP ad patch	2025/08/05 nationals50 PJ Poulin",
"2025/08/06	Casey Kelly	ARI	60	Home red Avnet ad patch	2025/08/06 dbacks60 Casey Kelly",
"2025/08/06	Brooks Kriske	MIN	61	Road navy Securian Financial ad patch	2025/08/06 twins61 Brooks Kriske",
"2025/08/07	Rico Garcia	BAL	50	City connect T. Rowe Price ad patch	2025/08/07 orioles50 Rico Garcia",
"2025/08/07	Jacob Amaya	CHW	0	Road black Bobby Jenks 45 memorial patch	2025/08/07 whitesox0 Jacob Amaya",
"2025/08/08	Greg Allen	BAL	25	City connect T. Rowe Price ad patch	2025/08/08 orioles25 Greg Allen",
"2025/08/08	Kyle Karros	COL	12	Road gray York Space Systems ad patch	2025/08/08 rockies12 Kyle Karros",
"2025/08/08	Codi Heuer	DET	57	City connect Meijer ad patch	2025/08/08 tigers57 Codi Heuer",
"2025/08/08	Enyel De Los Santos	HOU	65	Road orange Oxy ad patch	2025/08/08 astros65 Enyel De Los Santos",
"2025/08/08	Justin Dean	LAD	75	Home white Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/08/08 dodgers75 Justin Dean",
"2025/08/08	Shelby Miller	MIL	55	City connect Bob Uecker memorial patch Northwestern Mutual ad patch	2025/08/08 brewers55 Shelby Miller",
"2025/08/08	Jhonny Pereda	MIN	65	City connect Securian Financial ad patch	2025/08/08 twins65 Jhonny Pereda",
"2025/08/08	Drew Gilbert	SFG	61	Home orange Chevrolet ad patch	2025/08/08 giants61 Drew Gilbert",
"2025/08/08	Tristan Peters	TBR	25	Road powder	2025/08/08 rays25 Tristan Peters",
"2025/08/09	Juan Burgos	ARI	52	Home black Avnet ad patch	2025/08/09 dbacks52 Juan Burgos",
"2025/08/09	Vidal Brujan	ATL	17	City connect Quikrete ad patch	2025/08/09 braves17 Vidal Brujan",
"2025/08/09	Hurston Waldrep	ATL	64	City connect Quikrete ad patch	2025/08/09 braves64 Hurston Waldrep",
"2025/08/09	Tyler Zuber	MIA	55	Road black ADT ad patch	2025/08/09 marlins55 Tyler Zuber",
"2025/08/09	Ryan Gusto	MIA	65	Road black ADT ad patch	2025/08/09 marlins65 Ryan Gusto",
"2025/08/10	Elvis Peguero	CHW	47	Home white Bobby Jenks 45 memorial patch	2025/08/10 whitesox47 Elvis Peguero",
"2025/08/10	Jorge Alcala	STL	56	Home white Sunday hat Stifel ad patch	2025/08/10 cardinals56 Jorge Alcala",
"2025/08/11	Ali Sanchez	BOS	18	Road gray MassMutual ad patch	2025/08/11 redsox18 Ali Sanchez",
"2025/08/11	Jovani Moran	BOS	47	Road gray MassMutual ad patch	2025/08/11 redsox47 Jovani Moran",
"2025/08/11	Luinder Avila	KCR	58	Home white QuikTrip ad patch	2025/08/11 royals58 Luinder Avila",
"2025/08/11	Everson Pereira	TBR	45	Road navy	2025/08/11 rays45 Everson Pereira",
"2025/08/12	Daniel Johnson	BAL	56	Home white T. Rowe Price ad patch	2025/08/12 orioles56 Daniel Johnson",
"2025/08/13	Ronny Simon	PIT	63	Road gray Dave Parker COBRA memorial chest patch Sheetz ad patch	2025/08/13 pirates63 Ronny Simon",
"2025/08/14	Owen Caissie	CHC	19	Road gray Motorola ad patch	2025/08/14 cubs19 Owen Caissie",
"2025/08/15	Buddy Kennedy	LAD	46	Home white Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/08/15 dodgers46 Buddy Kennedy",
"2025/08/15	Steward Berroa	MIL	35	Road gray Bob Uecker memorial patch Northwestern Mutual ad patch	2025/08/15 brewers35 Steward Berroa",
"2025/08/15	Evan Sisk	PIT	51	Road gray Dave Parker COBRA memorial chest patch Sheetz ad patch	2025/08/15 pirates51 Evan Sisk",
"2025/08/15	Bob Seymour	TBR	41	Road navy	2025/08/15 rays41 Bob Seymour",
"2025/08/16	Dylan Beavers	BAL	12	Road orange T. Rowe Price ad patch	2025/08/16 orioles12 Dylan Beavers",
"2025/08/16	James Outman	MIN	43	Home white Securian Financial ad patch	2025/08/16 twins43 James Outman",
"2025/08/16	Nolan McLean	NYM	26	City connect Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/08/16 mets26 Nolan McLean",
"2025/08/17	Nabil Crismatt	ARI	61	Road red Avnet ad patch	2025/08/17 dbacks61 Nabil Crismatt",
"2025/08/17	Samuel Basallo	BAL	29	Road gray T. Rowe Price ad patch	2025/08/17 orioles29 Samuel Basallo",
"2025/08/17	Joey Wiemer	MIA	41	Road gray ADT ad patch	2025/08/17 marlins41 Joey Wiemer",
"2025/08/17	Genesis Cabrera	MIN	92	Home cream Securian Financial ad patch	2025/08/17 twins92 Genesis Cabrera",
"2025/08/17	Nathan Church	STL	27	Home white Sunday hat Stifel ad patch	2025/08/17 cardinals27 Nathan Church",
"2025/08/17	Anthony Veneziano	STL	67	Home white Sunday hat Stifel ad patch	2025/08/17 cardinals67 Anthony Veneziano",
"2025/08/18	Nathaniel Lowe	BOS	37	Home white MassMutual ad patch	2025/08/18 redsox37 Nathaniel Lowe",
"2025/08/18	Tayler Scott	HOU	50	Road gray Oxy ad patch	2025/08/18 astros50 Tayler Scott",
"2025/08/18	Maximo Acosta	MIA	24	Home white ADT ad patch	2025/08/18 marlins24 Maximo Acosta",
"2025/08/18	Nolan Hoffman	PHI	47	Home white IBX ad patch	2025/08/18 phillies47 Nolan Hoffman",
"2025/08/19	Connor Seabold	ATL	61	Home white Quikrete ad patch	2025/08/19 braves61 Connor Seabold",
"2025/08/20	Will Banfield	CIN	49	Road red Pete Rose 14 memorial patch Kroger ad patch	2025/08/20 reds49 Will Banfield",
"2025/08/20	Parker Messick	CLE	77	Road navy Marathon ad patch	2025/08/20 guardians77 Parker Messick",
"2025/08/21	Jake Fraley	ATL	16	Home red Quikrete ad patch	2025/08/21 braves16 Jake Fraley",
"2025/08/21	Jhostynxon Garcia	BOS	51	Road gray MassMutual ad patch	2025/08/21 redsox51 Jhostynxon Garcia",
"2025/08/21	Paul Blackburn	NYY	58	Home white Starr ad patch	2025/08/21 yankees58 Paul Blackburn",
"2025/08/21	Joel Peguero	SFG	63	Road gray Chevrolet ad patch	2025/08/21 giants63 Joel Peguero",
"2025/08/21	Carson Williams	TBR	77	Home white	2025/08/21 rays77 Carson Williams",
"2025/08/22	Cal Quantrill	ATL	48	Home red Quikrete ad patch	2025/08/22 braves48 Cal Quantrill",
"2025/08/22	Vimael Machin	BAL	65	City connect T. Rowe Price ad patch	2025/08/22 orioles65 Vimael Machin",
"2025/08/22	Zach Maxwell	CIN	78	Road gray Pete Rose 14 memorial patch Kroger ad patch	2025/08/22 reds78 Zach Maxwell",
"2025/08/22	Drew Sommers	DET	51	City connect Meijer ad patch	2025/08/22 tigers51 Drew Sommers",
"2025/08/22	Craig Kimbrel	HOU	46	Road gray Oxy ad patch	2025/08/22 astros46 Craig Kimbrel",
"2025/08/22	Bubba Chandler	PIT	57	City connect white pants Dave Parker COBRA memorial chest patch Sheetz ad patch	2025/08/22 pirates57 Bubba Chandler",
"2025/08/22	Brian Van Belle	TBR	67	City connect	2025/08/22 rays67 Brian Van Belle",
"2025/08/22	Shane Bieber	TOR	57	Road powder TD patch	2025/08/22 bluejays57 Shane Bieber",
"2025/08/23	Mick Abel	MIN	20	Road gray Securian Financial ad patch	2025/08/23 twins20 Mick Abel",
"2025/08/24	Wander Suero	ATL	50	Home white Quikrete ad patch	2025/08/24 braves50 Wander Suero",
"2025/08/24	McCade Brown	COL	51	Road gray York Space Systems ad patch	2025/08/24 rockies51 McCade Brown",
"2025/08/24	Taj Bradley	MIN	26	Road navy Securian Financial ad patch	2025/08/24 twins26 Taj Bradley",
"2025/08/24	Will Wagner	SDP	24	Home camo brown Motorola ad patch	2025/08/24 padres24 Will Wagner",
"2025/08/26	Mason Barnett	ATH	63	Home kelly green Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/08/26 athletics63 Mason Barnett",
"2025/08/26	Lou Trivino	PHI	57	Road gray IBX ad patch	2025/08/26 phillies57 Lou Trivino",
"2025/08/27	Taylor Rashi	ARI	54	Road red Avnet ad patch	2025/08/27 dbacks54 Taylor Rashi",
"2025/08/27	Roansy Contreras	BAL	66	Home white T. Rowe Price ad patch	2025/08/27 orioles66 Roansy Contreras",
"2025/08/27	Seth Martinez	MIA	40	Home white ADT ad patch	2025/08/27 marlins40 Seth Martinez",
"2025/08/27	Erick Fedde	MIL	59	Home cream Bob Uecker memorial patch Northwestern Mutual ad patch	2025/08/27 brewers59 Erick Fedde",
"2025/08/28	Shawn Dubin	BAL	62	Home white T. Rowe Price ad patch	2025/08/28 orioles62 Shawn Dubin",
"2025/08/29	John Brebbia	ATL	60	Road red Quikrete ad patch	2025/08/29 braves60 John Brebbia",
"2025/08/29	Payton Tolle	BOS	70	City connect MassMutual ad patch	2025/08/29 redsox70 Payton Tolle",
"2025/08/29	Stephen Kolek	KCR	32	City connect QuikTrip ad patch	2025/08/29 royals32 Stephen Kolek",
"2025/08/29	Jonah Tong	NYM	21	Home black Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/08/29 mets21 Jonah Tong",
"2025/08/29	Jimmy Crooks	STL	8	Road gray navy hat Stifel ad patch	2025/08/29 cardinals8 Jimmy Crooks",
"2025/08/29	Cesar Prieto	STL	31	Road gray navy hat Stifel ad patch	2025/08/29 cardinals31 Cesar Prieto",
"2025/08/29	Dylan Moore	TEX	25	Road gray Energy Transfer ad patch	2025/08/29 rangers25 Dylan Moore",
"2025/08/29	C.J. Stubbs	WSN	36	City connect AARP ad patch	2025/08/29 nationals36 C.J. Stubbs",
"2025/08/30	Cam Devanney	PIT	34	Road black Dave Parker COBRA memorial sleeve patch Sheetz ad patch	2025/08/30 pirates34 Cam Devanney",
"2025/08/31	Jose Urena	LAA	54	Road red FBM ad patch	2025/08/31 angels54 Jose Urena",
"2025/08/31	Ryan Kreidler	PIT	6	Road black Dave Parker COBRA memorial sleeve patch Sheetz ad patch	2025/08/31 pirates6 Ryan Kreidler",
"2025/09/01	Scott McGough	ATH	48	Road gray Rickey Henderson 24 memorial patch Sacramento patch Las Vegas ad patch	2025/09/01 athletics48 Scott McGough",
"2025/09/01	Rolddy Munoz	ATL	70	Road gray Quikrete ad patch	2025/09/01 braves70 Rolddy Munoz",
"2025/09/01	Aaron Civale	CHC	38	Home white Ryne Sandberg 23 memorial patch Motorola ad patch	2025/09/01 cubs38 Aaron Civale",
"2025/09/01	Carlos Santana	CHC	41	Home white Ryne Sandberg 23 memorial patch Motorola ad patch	2025/09/01 cubs41 Carlos Santana",
"2025/09/01	Sal Stewart	CIN	43	Home red Pete Rose 14 memorial patch Kroger ad patch	2025/09/01 reds43 Sal Stewart",
"2025/09/01	George Valera	CLE	35	Road navy Marathon ad patch	2025/09/01 guardians35 George Valera",
"2025/09/01	Carter Jensen	KCR	22	Home white QuikTrip ad patch	2025/09/01 royals22 Carter Jensen",
"2025/09/01	Mitch Farris	LAA	70	Road red FBM ad patch	2025/09/01 angels70 Mitch Farris",
"2025/09/01	Michael Petersen	MIA	49	Road gray ADT ad patch	2025/09/01 marlins49 Michael Petersen",
"2025/09/01	Brian Navarreto	MIA	70	Road gray ADT ad patch	2025/09/01 marlins70 Brian Navarreto",
"2025/09/01	Tim Mayza	PHI	54	Road gray IBX ad patch	2025/09/01 phillies54 Tim Mayza",
"2025/09/01	Harry Ford	SEA	5	Road navy Nintendo Switch 2 ad patch	2025/09/01 mariners5 Harry Ford",
"2025/09/01	Luke Jackson	SEA	77	Road navy Nintendo Switch 2 ad patch	2025/09/01 mariners77 Luke Jackson",
"2025/09/01	JT Brubaker	SFG	34	Road gray Chevrolet ad patch	2025/09/01 giants34 JT Brubaker",
"2025/09/01	Isiah Kiner-Falefa	TOR	7	Road powder TD patch	2025/09/01 bluejays7 Isiah Kiner-Falefa",
"2025/09/01	Andrew Alvarez	WSN	54	Home navy AARP ad patch	2025/09/01 nationals54 Andrew Alvarez",
"2025/09/02	Ha-Seong Kim	ATL	9	Road navy Quikrete ad patch	2025/09/02 braves9 Ha-Seong Kim",
"2025/09/02	Hayden Harris	ATL	79	Road navy Quikrete ad patch	2025/09/02 braves79 Hayden Harris",
"2025/09/02	Reiver Sanmartin	CIN	48	Home red Pete Rose 14 memorial patch Kroger ad patch	2025/09/02 reds48 Reiver Sanmartin",
"2025/09/02	Ryan Borucki	TOR	35	Road royal TD patch	2025/09/02 bluejays35 Ryan Borucki",
"2025/09/02	Jorge Alfaro	WSN	44	Home navy AARP ad patch	2025/09/02 nationals44 Jorge Alfaro",
"2025/09/03	Roansy Contreras	COL	59	Home purple York Space Systems ad patch	2025/09/03 rockies59 Roansy Contreras",
"2025/09/03	Jayden Murray	HOU	70	Home white Oxy ad patch	2025/09/03 astros70 Jayden Murray",
"2025/09/04	Logan Davidson	LAA	21	Road red FBM ad patch	2025/09/04 angels21 Logan Davidson",
"2025/09/04	Ben Rortvedt	LAD	47	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/09/04 dodgers47 Ben Rortvedt",
"2025/09/04	Jose Castillo	SEA	67	Road navy Nintendo Switch 2 ad patch	2025/09/04 mariners67 Jose Castillo",
"2025/09/05	Dominic Fletcher	CHW	5	Road gray Bobby Jenks 45 memorial patch	2025/09/05 whitesox5 Dominic Fletcher",
"2025/09/05	Wander Suero	NYM	54	Road royal Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/09/05 mets54 Wander Suero",
"2025/09/06	Chuckie Robinson	LAD	52	Road gray Los Angeles Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/09/06 dodgers52 Chuckie Robinson",
"2025/09/06	Christian Roa	MIA	82	City connect ADT ad patch	2025/09/06 marlins82 Christian Roa",
"2025/09/07	Sammy Peralta	LAA	57	Home white Childhood Cancer Awareness patch FBM ad patch	2025/09/07 angels57 Sammy Peralta",
"2025/09/07	Brandon Sproat	NYM	40	Road gray Childhood Cancer Awareness patch Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/09/07 mets40 Brandon Sproat",
"2025/09/07	Carl Edwards Jr.	TEX	58	Home powder Childhood Cancer Awareness patch Energy Transfer ad patch	2025/09/07 rangers58 Carl Edwards Jr.",
"2025/09/08	Sandy Leon	ATL	8	Home white Quikrete ad patch	2025/09/08 braves8 Sandy Leon",
"2025/09/08	Alexis Diaz	ATL	48	Home white Quikrete ad patch	2025/09/08 braves48 Alexis Diaz",
"2025/09/08	Sebastian Rivero	LAA	38	Home white FBM ad patch	2025/09/08 angels38 Sebastian Rivero",
"2025/09/08	Donovan Walton	PHI	18	Home white IBX ad patch	2025/09/08 phillies18 Donovan Walton",
"2025/09/08	Nick Raquet	STL	70	Road gray Stifel ad patch	2025/09/08 cardinals70 Nick Raquet",
"2025/09/09	Connelly Early	BOS	71	Road gray MassMutual ad patch	2025/09/09 redsox71 Connelly Early",
"2025/09/09	Carson Williams	TBR	7	Road navy	2025/09/09 rays7 Carson Williams",
"2025/09/10	Kyle Harrison	BOS	38	Road gray MassMutual ad patch	2025/09/10 redsox38 Kyle Harrison",
"2025/09/11	Joey Gerber	TBR	55	Road navy	2025/09/11 rays55 Joey Gerber",
"2025/09/12	Blaine Crim	COL	16	Road gray York Space Systems ad patch	2025/09/12 rockies16 Blaine Crim",
"2025/09/12	Jose Urquidy	DET	65	Road gray Meijer ad patch	2025/09/12 tigers65 Jose Urquidy",
"2025/09/12	Zach Cole	HOU	16	Road gray Oxy ad patch	2025/09/12 astros16 Zach Cole",
"2025/09/12	Chad Wallach	LAA	35	Road red FBM ad patch	2025/09/12 angels35 Chad Wallach",
"2025/09/12	Cody Laweryson	MIN	66	City connect Securian Financial ad patch	2025/09/12 twins66 Cody Laweryson",
"2025/09/12	Walker Buehler	PHI	31	City connect IBX ad patch	2025/09/12 phillies31 Walker Buehler",
"2025/09/13	Denzer Guzman	LAA	13	Road red FBM ad patch	2025/09/13 angels13 Denzer Guzman",
"2025/09/13	Garrett Acton	TBR	54	Road navy	2025/09/13 rays54 Garrett Acton",
"2025/09/14	Carson Ragsdale	BAL	83	Road gray T. Rowe Price ad patch	2025/09/14 orioles83 Carson Ragsdale",
"2025/09/15	Michael Soroka	CHC	99	Road gray Roberto Clemente Day patch Ryne Sandberg 23 memorial patch Motorola ad patch	2025/09/15 cubs99 Michael Soroka",
"2025/09/15	Bryce Eldridge	SFG	78	Road gray Roberto Clemente Day patch Chevrolet ad patch	2025/09/15 giants78 Bryce Eldridge",
"2025/09/15	Trey Yesavage	TOR	39	Road royal Roberto Clemente Day patch TD patch	2025/09/15 bluejays39 Trey Yesavage",
"2025/09/16	Jose Castillo	BAL	66	Road gray T. Rowe Price ad patch	2025/09/16 orioles66 Jose Castillo",
"2025/09/16	Carter Kieboom	LAA	17	Road red Roberto Clemente Day patch FBM ad patch	2025/09/16 angels17 Carter Kieboom",
"2025/09/16	Rafael Lantigua	PHI	19	Road gray IBX ad patch	2025/09/16 phillies19 Rafael Lantigua",
"2025/09/17	Cole Wilcox	TBR	73	Home white	2025/09/17 rays73 Cole Wilcox",
"2025/09/17	Sauryn Lao	WSN	73	Home white AARP ad patch	2025/09/17 nationals73 Sauryn Lao",
"2025/09/18	Philip Abner	ARI	50	City connect Avnet ad patch	2025/09/18 dbacks50 Philip Abner",
"2025/09/18	Paul Sewald	DET	62	Home white Meijer ad patch	2025/09/18 tigers62 Paul Sewald",
"2025/09/18	Sam Aldegheri	LAA	61	Road red FBM ad patch	2025/09/18 angels61 Sam Aldegheri",
"2025/09/19	Jhancarlos Lara	ATL	81	Road red Quikrete ad patch	2025/09/19 braves81 Jhancarlos Lara",
"2025/09/19	Jose Espada	BAL	72	City connect T. Rowe Price ad patch	2025/09/19 orioles72 Jose Espada",
"2025/09/20	Petey Halpin	CLE	0	Road gray Marathon ad patch	2025/09/20 guardians0 Petey Halpin",
"2025/09/20	Bruce Zimmermann	MIL	55	Road gray Bob Uecker memorial patch Northwestern Mutual ad patch	2025/09/20 brewers55 Bruce Zimmermann",
"2025/09/20	Richard Lovelady	NYM	58	City connect Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/09/20 mets58 Richard Lovelady",
"2025/09/20	Jesse Scholtens	TBR	65	Home throwback	2025/09/20 rays65 Jesse Scholtens",
"2025/09/21	Austin Pope	ARI	66	Home red Avnet ad patch	2025/09/21 dbacks66 Austin Pope",
"2025/09/21	Tanner Rainey	DET	32	Home white Meijer ad patch	2025/09/21 tigers32 Tanner Rainey",
"2025/09/21	Robert Gasser	MIL	54	Road gray Bob Uecker memorial patch Northwestern Mutual ad patch	2025/09/21 brewers54 Robert Gasser",
"2025/09/22	Charlie Morton	ATL	50	Home white Quikrete ad patch	2025/09/22 braves50 Charlie Morton",
"2025/09/23	Joel Payamps	ATL	53	Home white Quikrete ad patch	2025/09/23 braves53 Joel Payamps",
"2025/09/23	Brett Wisely	ATL	60	Home white Quikrete ad patch	2025/09/23 braves60 Brett Wisely",
"2025/09/23	Hunter Barco	PIT	45	Road black Dave Parker COBRA memorial sleeve patch Sheetz ad patch	2025/09/23 pirates45 Hunter Barco",
"2025/09/23	Julian Fernandez	WSN	65	Road navy AARP ad patch	2025/09/23 nationals65 Julian Fernandez",
"2025/09/24	Derek Hill	CHW	47	Road gray Bobby Jenks 45 memorial patch	2025/09/24 whitesox47 Derek Hill",
"2025/09/24	Billy McKinney	TEX	33	Home white blue hat Scott Littlefield SL memorial patch Energy Transfer ad patch	2025/09/24 rangers33 Billy McKinney",
"2025/09/26	Donovan Solano	TEX	16	Road gray Scott Littlefield SL memorial patch Energy Transfer ad patch	2025/09/26 rangers16 Donovan Solano",
"2025/09/26	Jose Corniell	TEX	59	Road gray Scott Littlefield SL memorial patch Energy Transfer ad patch	2025/09/26 rangers59 Jose Corniell",
"2025/09/27	Andrew Heaney	LAD	33	Road gray Dodgers Fernando Valenzuela 34 memorial patch Guggenheim ad patch	2025/09/27 dodgers33 Andrew Heaney",
"2025/09/27	Dylan Ross	NYM	50	Road gray Ed Kranepool 7 memorial patch New York-Presbyterian ad patch	2025/09/27 mets50 Dylan Ross",
"2025/09/28	Jose De Leon	BOS	78	Home white MassMutual ad patch	2025/09/28 redsox78 Jose De Leon",
"2025/09/30	Chase DeLauter	CLE	34	Home red Marathon ad patch	2025/09/30 guardians34 Chase DeLauter",
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