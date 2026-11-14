# Design

## Decisions (luate cu omul)
- Layout: panou vertical lateral lângă hartă. Derulare: scroll mută harta automat (cu debounce ~150 ms), plus clic pe intrare și săgeți sus/jos. Date: scenariul extrem implicit (`?scenariu=extrem`), cu posibilitatea de a reveni la cel de bază.
- Intrarea activă = cea care ocupă centrul panoului (IntersectionObserver). La schimbare: `GET /retea?data=<data>&scenariu=extrem`, cache pe dată în UI ca scroll-ul să nu reîncarce aceeași dată.
- Mai multe evenimente în aceeași zi: harta e la sfârșitul zilei (comportamentul actual al `snapshot(data)`); intrarea activă evidențiază doar elementele ei (`elemente_atinse`) prin contur, nu prin altă stare a hărții.
- Culori de decizie: aceleași ca în hartă (verde aplicat/adăugat, albastru/punctat predicție, galben de verificat, gri neaplicat, roșu eronat în prototip). Eticheta ca insignă.
- Scor înainte -> după: din `schimbari[]`; pentru evenimente cu multe schimbări (mutare fire, 20 de elemente) se arată primele 3 și „+17".
- „De ce?": `pasi[]` din aceeași intrare, fără apel suplimentar (116 KB pentru 70 de evenimente, acceptabil la o singură încărcare).

## Risks / Trade-offs
- Scroll-ul cu hartă care se schimbă poate sacada la 70 de evenimente; debounce și cache pe dată. Dacă tot sacadează, se trece pe „clic + săgeți".
- Intrările din aceeași zi nu au hărți diferite; evidențierea compensează.
