# FSI Mesh Study — akční plán k dizertaci

> Doprovodný plán k `fsi-mesh-study-log.md`. Cílem je převést solidní data-engine na
> **obhajitelnou dizertační kapitolu.** Řazeno podle priority pro obhajobu.
> Verze 2026-07-XX.

## 0. Přerámování claimu (udělat jako první, je to zdarma)

Studie se **neprodává** jako „predikce padákového opening-loadu" (to by bez validace a s infinite-mass neobstálo), ale jako:

> **Metodika pro extrakci mesh-konvergovaných otevíracích metrik z padákového FSI** — CFC filtrace near-singulární špičky + replikátové ošetření chaotického nafukování, s kvantifikací numerické nejistoty.

Do úvodu kapitoly explicitně: rozsah (jeden provozní bod, infinite-mass jako horní odhad), a co je a není nárokem.

---

## 1. VALIDACE (Tier 1 — bez toho tě vrátí)

Tři nezávislé kotvy. Jedna hotová, dvě levné.

### 1a. Ustálený odpor — ✅ HOTOVO
Padák má v ustáleném opadání `Cd` shodný s testy. To validuje ustálený stav a dává ti důvěryhodné **`C_D·S`** do vzorců níže. Do práce: tabulka sim `Cd` vs test `Cd`, relativní chyba.

> Pozor na náklon 38–42°: ustálené `Cd` reportuj z **výslednice** `|F|/(q·S)`, ne z osové `Fpz` — jinak porovnáváš špatnou složku (viz §4).

### 1b. Plnicí čas — Knackeho korelace (levné, silné)
Knackeho vztah pro dobu plnění:

```
t_f = n · D_0 / v
```

- `t_f` … doba plnění [s]  (= tvůj **t_fill**)
- `n`  … bezrozměrná plnicí konstanta (tabulovaná dle typu vrchlíku, Knacke)
- `D_0` … nominální (konstrukční) průměr, `D_0 = sqrt(4·S_0/π)`
- `v`  … rychlost na začátku plnění [m/s] (= 20 m/s)

**Validace:** z tvého t_fill spočítej `n = t_f · v / D_0` a porovnej s tabulkovou `n` pro tvůj typ vrchlíku. Když sedí (řádově), máš validovanou dynamiku plnění — a zároveň fyzikální zdůvodnění, proč t_fill reportovat.

### 1c. Špička — opening-force koeficient (Pflanz–Ludtke)
Otevírací síla obecně:

```
F_max = C_x · X_1 · (C_D·S) · q ,      q = ½·ρ·v²
```

- `C_x` … opening-force coefficient (infinite-mass), konstanta dle typu vrchlíku (Knacke/Ludtke tabulky/křivky)
- `X_1` … redukční faktor konečné hmoty (Pflanz), `X_1 = f(mass ratio)`; **`X_1 = 1` pro infinite-mass**
- `C_D·S` … drag area plně otevřeného (z §1a, validované)
- `q` … dynamický tlak

**Ty jsi infinite-mass ⇒ X_1 = 1**, takže z tvé simulace přímo vytáhneš:

```
C_x(sim) = F_peak / (C_D·S·q) = F_peak / F_steady
```

a porovnáš s tabulkovou infinite-mass `C_x`. To je **přímá validace špičky** — a elegantně to využívá zrovna to, že jsi infinite-mass (jinak slabina, tady výhoda).

---

## 2. Numerická úplnost (Tier 1–2)

### 2a. Nemonotónní konvergence vs GCI — ošetřit explicitně
Klasický **ASME V&V 20 / GCI (Roache)** nejde použít (nemonotónnost). Do práce napiš proč a nabídni náhradu:
- pro **impulz** (monotónní/robustní) proveď GCI standardně → formální numerická nejistota,
- pro **peak** argumentuj replikátovou statistikou (rozptyl přes realizace) jako mírou nejistoty místo Richardsona, a **cituj**, že chaotický peak je z principu nevhodný pro deterministický GCI.

### 2b. Konvergence časového kroku — doplnit
dt byl celou dobu propletený se sítí kvůli stabilitě. Potřebuješ **čistou dt-konvergenci při fixní síti** (produkční CSD50/CFD100): 2–3 běhy s dt ∈ {0.25, 0.5, 0.75 ms}, filtrovaně, ukázat že peak/t_fill jsou na dt nezávislé (nebo kvantifikovat).

### 2c. Turbulentní citlivost — aspoň komentář, ideálně 1 běh
Odtržený úplav (zdroj oscilací) je na closure citlivější než na síť. Minimum: odstavec, že k-ω SST URANS je volba a její limity. Lepší: 1 srovnávací běh (jiný model / LES-blízký) na produkční síti jako sensitivity.

---

## 3. Dokončení mesh/replikátové části

- Impulz: GCI (viz 2a).
- Peak/t_fill: produkční síť **CSD≤50, CFD≤100**, potvrzeno; CFD peak-nezávislé, CSD coarser→vyšší.
- (Volitelně) CSD=40 doladit jako spodní kotvu konvergence, jak řešíme přes kontakt.

---

## 4. Fyzikální správnost výstupů (Tier 2)

- **Reportovat tah v riseru = výslednici podél zavěšení**, ne tělesovou `Fpz`. Vrchlík letí v náklonu 38–42°, takže `Fpz` není návrhová složka. Přepočítat peak i steady na výslednici.
- **Náklon/kuželení** doložit jako samostatný výsledek (úhel vektoru síly v čase) — je to fyzikálně zajímavé a ukazuje, že chápeš, co model dělá.

---

## 5. Most infinite-mass → finite-mass (Tier 1 rámování, levné)

Nemusíš hned počítat finite-mass. Použij Pflanz–Ludtke redukci:

```
F_finite ≈ C_x · X_1(A) · (C_D·S) · q
```

kde `A` je bezrozměrný **mass ratio / balistický parametr** (přesná definice dle Knacke kap. 5 / Ludtke — vzít z primárního zdroje, normalizací je víc). Z tvého infinite-mass `C_x` a odhadu `X_1(A)` pro reálné zatížení payloadu dostaneš **odhad reálného opening-loadu** — a v práci to ukáže, že infinite-mass je vědomý horní odhad napojený na standardní teorii, ne slepá ulička. Jeden skutečný finite-mass běh jako ověření = silné future work / bonus kapitola.

---

## 6. Kontakt + propustnost (ODLOŽENO, ale zarámovat správně)

Až na to dojde: propustnost i kontakt **ukotvit fyzikou** (měření tkaniny / literatura), **ne ladit na hezký peak** — jinak kruhový argument. Framing: propustnost jako fyzikální mechanismus, který snižuje citlivost špičky na numerický kontakt.

---

## Pořadí a odhad práce

| # | Krok | Typ | Náročnost |
|---|---|---|---|
| 0 | Přerámovat claim + rozsah | psaní | hodiny |
| 1a | Cd vs test (výslednice) | psaní | hodiny |
| 1b | t_fill vs Knacke (n) | výpočet z dat + psaní | hodiny |
| 1c | C_x sim vs Knacke/Ludtke | výpočet z dat + psaní | hodiny |
| 4 | Přepočet na riser-výslednici | přepočet z dat | den |
| 2b | dt-konvergence | 2–3 běhy | dny |
| 2a | GCI (impulz) + zdůvodnění (peak) | výpočet + psaní | dny |
| 5 | infinite→finite most (X_1) | psaní + odhad | den |
| 2c | turbulentní citlivost | 1 běh / odstavec | dny |
| 6 | kontakt + propustnost | běhy | týdny (odloženo) |

**Kritická cesta k obhajitelnosti = kroky 0, 1a–1c, 4, 2a.** To je většinou přepočet z existujících dat + psaní, ne nové simulace. Data-engine máš; chybí validace a formální rámec.

## Zdroje
- Knacke, T.W. — *Parachute Recovery Systems Design Manual* (plnicí čas, C_x, mass ratio).
- Pflanz / Ludtke — opening-force method, redukční faktor X_1.
- Roache / ASME V&V 20 — GCI, numerická nejistota.
