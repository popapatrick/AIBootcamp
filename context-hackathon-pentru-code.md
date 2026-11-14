# Context hackathon: pentru Claude Code

Scris pe 14 noiembrie 2026, din conversația cu Victor (student CTI anul 1, UPB, scrie în română, lucrează pe Mac).
Scopul acestui fișier: să nu se piardă ce am stabilit, ca să poți începe implementarea.

## Cum vrea Victor să lucrăm
- Întreabă-l despre orice nu e clar explicat. Nu decide în locul lui și nu prezenta un plan finit.
- Când a zis „nu vreau demo, vreau să înțelegi ce vreau să fac”, a însemnat că vrea întâi înțelegere comună, nu cod. Confirmă înțelegerea înainte să construiești.
- Răspunde în română. Textele pentru documentul hackathonului pot fi în engleză.

## Hackathonul și brief-ul
- Tema: „2. A grid model that keeps itself up to date”. Brief oficial: Challenge 2 de la PPC, „A digital model of the grid that updates itself as the network evolves”. Zona: GIS / date tehnice de rețea.
- Problema din brief: modelul GIS al rețelei (înaltă, medie și joasă tensiune) nu reflectă mereu realitatea din teren. Secțiuni lipsă sau poziționate greșit, schimbările din teren nu ajung în sistem, datele vechi rămân neactualizate. Decalajul nu se vede până când o decizie depinde de el.
- Constrângeri din brief: trebuie să funcționeze alături de platforma GIS de distribuție existentă a companiei și să respecte reglementările din sectorul distribuției.
- Ce oferă mentorii PPC: un eșantion de date GIS, informații despre reglementările actuale, mentorat tehnic de la echipa responsabilă de model.
- Succes înseamnă: un mecanism funcțional care identifică schimbările din teren pentru actualizarea modelului, cu un nivel de încredere vizibil și clar comunicat pentru secțiunile neverificate recent.
- Întrebările din brief: unde se pierd schimbările (în teren, în acte sau la introducerea datelor); ce echipă suferă cel mai mult și cât costă o decizie greșită; ce semnale există deja (comenzi de lucru, cereri de racordare, rapoarte de avarii); cum ar vrea un utilizator să vadă „cât pot avea încredere în această secțiune”.
- Mai departe, în notițe, apare „date standardizate” scris de mână lângă întrebări.

## Ce a aflat Victor de la mentorii PPC
- Rețeaua veche, moștenită de PPC de la Enel, e stocată pe hârtie, în 6 dulapuri cu bibliorafturi, organizată după adresă, plus câteva date alfanumerice. Schimbările noi sunt și ele alfanumerice, în baze de date.
- Datele sunt ținute separat pe departamente: racordări, mentenanță, investiții.
- PPC vrea o soluție „out of process”, care să le țină baza de date la zi.
- Ideea inițială a echipei: camere video pe mașinile PPC care, la o comandă de lucru, fac poze cu metadate, filtrate de un AI care actualizează rețeaua.
- Expertul a spus că se concentrează prea mult pe proces și a dat exemple de ce a încercat PPC cu piloți de dronă și cu imagini satelitare. Victor are senzația că expertul îi împinge spre direcția asta. Ce a mers și ce nu din încercările lor nu știm încă.
- „Claudiu” apare ca titlu în notițele lui. Nu e confirmat că e numele mentorului. Întreabă-l.

## Ce am găsit în cercetare (surse publice)
- PPC (grecii) a cumpărat operațiunile Enel din România pe 25 octombrie 2023. Distribuția se face prin Rețele Electrice România (Muntenia, Banat, Dobrogea), cu circa 136.000 km de rețea, 293 de stații și peste 26.000 de posturi de transformare. Rețele Electrice Muntenia acoperă București, Ilfov, Giurgiu, deci și zona Politehnicii.
- Sistemul din perioada Enel, „Global Repository & 3D Modelling”, adună nori de puncte și imagini din elicopter, dronă, scaner laser și mobile mapping.
- Aprilie 2026: licitație de până la 45 mil. lei pentru o platformă nouă GIS&Topology care înlocuiește GIS-ul actual, cu aplicație mobilă prin care se actualizează date din teren. În noiembrie 2025 au început un sistem AADMS și un sistem WFM.
- Nu am găsit date publice cu poziții de stâlpi sau linii de la Rețele Electrice. Nu înseamnă că nu există.
- Planul de dezvoltare 2026–2035 e public (PDF, 7,17 MB) pe reteleelectrice.ro, la Despre noi → Rețea și investiții → „Consultare publică”, cu anexele 8, 9 și 10. Nu a fost descărcat și nu știm ce conține.
- Seturi deschise cu rețele reale din alte țări, utile ca date de test (verifică licența): E-REDES Portugalia (poziții de stâlpi de joasă tensiune, CC BY 4.0), Enexis Olanda (stații și conexiuni MT și JT, CC0, shapefile), UK Power Networks (stâlpi JT și 33 kV, parțial vectorizați), Ergon Energy Australia, rețele de test EDP/Oviedo.

## Ce a fost eliminat sau limitat
- Google Street View: termenii nu permit descărcare în masă, cache sau analiză automată. Direcția a fost oprită.
- Mapillary: prea puține poze în zona lui. Pozele făcute de Victor cu telefonul ar evita problema.
- Sentinel-2 (10 m pe pixel) nu vede stâlpi. Poate prinde doar schimbări mari. Pentru stâlpi trebuie dronă sau imagini aeriene de rezoluție mare. Cablurile îngropate nu se văd deloc din imagini.

## Ipotezele pe care le-a ales Victor (format: We believe that … has the problem … when … because … and would change what they do if …)
Alese: 1, 7, 8 din lista de opt. Plus una nouă despre săpături. Părțile de după „if” sunt propuneri ale mele, nealese de el.

1. Fiecare departament PPC (racordări, mentenanță, investiții) are problema că schimbările lui nu ajung în modelul GIS comun, când se schimbă ceva în rețea, pentru că fiecare le ține separat, alfanumeric, iar partea veche e în bibliorafturi.
7. Echipa de operare lucrează pe un model care rămâne în urma rețelei, când rețeaua se schimbă zilnic, pentru că actualizarea depinde de cineva care merge în teren și completează hârtii. Ar schimba ce face dacă modelul s-ar actualiza singur prin standardizarea inputurilor și prin predicția schimbărilor în rețea.
8. Echipa de planificare nu știe ce tip de activ sau secțiune are în față, când înregistrările sunt incomplete, pentru că cele vechi au doar câteva atribute alfanumerice. Ar schimba ce face dacă ar folosi o clasificare dedusă din informațiile cunoscute, cu nivel de încredere vizibil.
Nouă. Echipa care sapă pentru reparații sau racorduri are problema că sapă după un cablu care nu mai e acolo, când deschide pământul, pentru că o schimbare anterioară (reconfigurare sau înlocuire) nu a fost înregistrată în GIS. Ar schimba ce face dacă ar vedea înainte de săpătură ce secțiuni s-au schimbat sau n-au fost verificate recent. Nu știm dacă mentorul a pomenit astfel de cazuri.
Cele cinci rămase din listă (2, 3, 4, 5, 6) au fost scrise, dar nu alese.

## Planul spus de Victor, ca un singur paragraf
Din mai multe inputuri (comenzi de lucru, cereri de racordare, planuri de investiții, imagini) se generează schimbări asupra GIS-ului, rezultatul fiind o hartă actuală, cu statistici actualizate. Statisticile ar putea însemna scorul de încredere pe secțiune și procentul de rețea verificat recent, dar asta nu e confirmat. Cere ca etapele să fie vizibile.

## Schiță de implementare (propunerea mea, NEDECISĂ)
Etape: (1) semnale de la echipe, fiecare în formatul ei; (2) standardizare într-o structură comună; (3) potrivire pe un element din model, după ID sau poziție; (4) propunere de modificare cu scor de încredere, nimic nu intră direct în model; (5) validare de către un om și aplicare, ce e doar planificat rămâne propunere.
Schema comună de eveniment, ca punct de plecare: event_id, echipă sursă, tip (racord_nou, activ_înlocuit, linie_planificată), referință (ID de element sau coordonate), status (executat sau planificat), dată, fiabilitatea sursei.
Scorul de încredere scade în timp de la ultima verificare, crește la confirmare, iar un semnal îl mută pe „de verificat”.
Am construit un widget cu date inventate care ilustrează fluxul (nu e cod reutilizabil). Victor a spus explicit că nu vrea un demo acum.
Piesă opțională: detectarea schimbărilor între două imagini aeriene ale aceleiași zone mici, dacă găsim imagini cu sursă și licență clare. Nu știm încă de unde.
Idee în discuție: clasificarea tipului de stâlp din poze cu un model multimodal, testată pe 30–50 de poze făcute de Victor, cu răspuns de încredere. Netestată.
Date folosibile pentru test: eșantionul GIS promis de mentori, dacă îl primesc, altfel seturile deschise din alte țări, etichetate clar ca nefiind ale PPC.

## Întrebări deschise
- Ce a mers și ce nu din încercările PPC cu drone și imagini satelitare?
- „Claudiu” este mentorul? Ce funcție are?
- Ce conține eșantionul GIS și ce platformă GIS e în uz azi?
- „Real-time” e necesar sau sunt suficiente actualizări mai dese?
- Cât durează azi de la schimbarea în teren până în GIS și cât costă întârzierea?
- Care este toleranța acceptabilă de poziție?
- Ce regulă spune cine poate valida o modificare?
- Ce se întâmplă în procesul de avize de amplasament pentru cei care sapă?
- Ce forme are demo-ul (cât durează prezentarea)? Nu a răspuns încă.

## Fișiere create în conversație
- cercetare-stalpi-retea.md: cercetarea inițială despre detectarea stâlpilor (mai veche, centrată pe poze).
- intrebari-deschise-mentor.md: 34 de întrebări pentru mentor.
- brief-challenge-2-ppc.md: rezumatul brief-ului oficial.
- cercetare-ppc-romania-harti.md: PPC în România și datele lor de hărți, cu surse.
- Prezentarea „A grid model that keeps itself up to date”, 6 slide-uri, publicată ca artifact în Slides. A fost făcută înainte de brief și de ipoteze, deci titlurile și întrebările ei sunt vechi. Se poate actualiza.
