# Design

## Context

Potrivirea merge pe ID, apoi coordonate, apoi adresă; adresa nu e geocodată (rămâne `nepotrivit`). Cache-ul OSM conține străzi cu nume (de exemplu Strada Primăverii, Șoseaua Giurgiului). Numărul casei nu se poate geocoda. Un stâlp nou se acceptă ca „nod nou" la 2,5 m de alte noduri.

## Goals / Non-Goals

**Goals:**
- Locația exactă a stâlpului din traseu când adresa e vagă.
- Explicație clară în „De ce?": strada, opririle găsite, timpul petrecut.

**Non-Goals:**
- Nu colectăm GPS real în prototip; traseul e simulat.
- Nu geocodăm numărul adresei; doar numele străzii.
- Nu rezolvăm confidențialitatea locației operatorilor; datele sunt fictive.

## Decisions

- Oprire = grup de puncte într-o rază de 12 m (din `weights.yaml`) cu durata totală peste un prag (3 min); locul opririi = media ponderată în timp.
- Alegerea locului: dintre opriri, cele aflate la cel mult 40 m de strada potrivită cu adresa; câștigă cea cu timpul cel mai lung. Fără stradă potrivită, câștigă oprirea cea mai lungă, cu scor mai mic.
- Fereastra de timp (60 min) și pragurile merg în `weights.yaml`, nu în cod.
- Rezultatul intră în potrivire ca „coordonate din trace": elementul existent la ≤ 15 m se confirmă, altfel se propune stâlp nou prin regula existentă. Scorul scade dacă oprirea cea mai lungă și a doua sunt apropiate ca durată (ambiguitate).
- Sursa rămâne tableta (0,90); trace-ul schimbă calitatea potrivirii, nu ponderea sursei.

## Risks / Trade-offs

- GPS-ul din interior sau cu zgomot dă opriri false; pragurile de rază și durată sunt necalibrate pe date reale (se spune în documentație).
- Operatorul poate sta mai mult la un alt loc (pauză): ambiguitatea scade scorul, deci poate rămâne doar predicție.
- Strada potrivită prin nume poate fi greșită dacă numele diferă de OSM; atunci se cade pe varianta fără stradă.
