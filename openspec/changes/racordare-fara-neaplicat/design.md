# Design

## Decisions

- `prezice_lant` (A) primește și `cfg["racordare"]["raza_extinsa_m"]` și întoarce `treapta` ∈ {1,2,3,4} și scorul `urmeaza_strada` doar când urmează strada. Treapta 4 întoarce doar casa.
- Scorul cade natural cu treapta prin factori din `weights.yaml` (`factor_fara_strada` există; se adaugă `factor_raza_extinsa`, `factor_linie_dreapta_lunga`, `factor_doar_casa`), nu printr-un plafon artificial.
- `prag_afisare` (de ex. 0,15) < `praguri.predictie`: între ele nivelul e `predictie` cu `slaba: true`. Sub `prag_afisare`, dacă locația e în zonă, punctul casei se desenează oricum ca „de verificat" fără lanț.
- Zona prototipului (feature `safeguard-zona-prototip`) se aplică înainte: în afara ei nu se prezice.
- Predicția rămâne neaplicată; scorul și treapta apar în „De ce?" ca să se vadă cât de nesigură e.

## Risks / Trade-offs

- Predicțiile slabe pot aglomera harta; UI-ul le poate ascunde cu un filtru pe scor.
