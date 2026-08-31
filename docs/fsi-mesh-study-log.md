# FSI Mesh-Dependence Study — pracovní log vlákna

> Průběžný log spolupráce s Claude (Claude Code) na mesh-dependence studii padáku.
> Slouží k přenosu kontextu mezi stroji/sezeními — otevři nové vlákno a odkaž na tento soubor.
> Poslední aktualizace: **2026-07-09**. Grafy: https://claude.ai/code/artifact/136045e5-6469-4f4b-b935-31df1688d8ce

## Úloha

LS-DYNA ICFD FSI simulace padáku (infinite-mass „wind tunnel", v = 20 m/s konst., vrchlík držen SPC vazbou a v čase *death* uvolněn). Studie závislosti na síti: CSD (strukturální) 50/100/200/300 mm × CFD (tekutinová) 50/100/200 mm; dále časový krok, virtuální tloušťka kontaktu, délka výpočtu. Výsledky = ICFD drag `.dat` (sloupce time, Fpx…Mvz; Fpz = osová síla).

**Setup decky v kořeni repa:** `00_FSI_setup.k` (master: SPC birth/death, kontakt Canopy2Lines, includes), `00_CSD_setup.k` (implicitní struktura, MAT_FABRIC ~39 g/m², kontakt SAST), `00_CFD_setup.k` (ICFD: `*ICFD_CONTROL_FSI` owc=0 silné spřažení, `*ICFD_CONTROL_TIME`, porézní vrchlík).

## Klíčová zjištění (chronologicky)

### 1. Integrita dat (opakovaně!)
- Květnová sada: strašáky `ID-6/-7/-8.dat` ve složkách `raw/sim_1/2/3` přebíjely správné soubory (parser bere první `.dat` dle abecedy — `infinite_mass.py`); ID8 měl připojený soubor ID7. Opraveno, karanténa `data/fsi/_quarantine/`.
- „CFD=300" běhy (ID13/14/15) byly **bajtově identické** s CFD=200 protějšky → síť 300 se nikdy nedostala do decků (uživatel potvrdil). CFD=300 opuštěno jako zbytečné.
- **Pravidlo: každou novou sadu hashovat (md5) před analýzou.**

### 2. Stabilita řešiče
- Padák = lehká tkanina → added-mass problém. Silné spřažení nutné (je aktivní). `NSUB` v `*ICFD_CONTROL_FSI` = limit FSI subiterací; manuál doslova jmenuje padáky (resonance-like mód v subiteracích). nsub=0 = bez limitu.
- Pád v t=0,1 s (moment uvolnění SPC) při dt=0,5 ms + kontakt 8 mm na hrubé síti: **viníkem byla tloušťka kontaktu, ne krok** (izolováno: kontakt 10 mm → OK i s dt=0,5 ms).
- **Tloušťka kontaktu = numerický knoflík škálovaný se sítí** (fyzická tkanina 0,06 mm; kontakt 8 mm jemné / 8,5–10 mm hrubé). Bereme jako součást „rozlišení sítě", nekazí porovnání (ID11 vs ID12: táž síť, dt 0,5→0,75 ms + kontakt 8→10 mm → Δ steady Fpz 2,7 N, v šumu).
- IDC=1.0 v `*ICFD_CONTROL_FSI` = detekční koeficient FSI (d ≤ IDC·min(h,H)), 4× default — záměr, OK.
- dctol=0.02 volné záměrně (ráz po uvolnění SPC).

### 3. Finální matice (přepočet, dt=0,5 ms všude kromě ID12)
Steady Fpz [N] ±2·SEM, okno 0,5–1,0 s (POZOR: okno nese bias ~5–10 N, viz bod 4):

| CSD\CFD | 50 | 100 | 200 |
|---|---|---|---|
| 50 | −154,8 | −165,7 | **−173,7 ±2,7** (4s) |
| 100 | −147,8 | −146,1 | **−140,1 ±1,2** (4s) |
| 200 | −153,4 | −148,8 (kontakt 8,5) | **−155,8 ±6,3** (4s, CoV 32 %!) |
| 300 | −165,9 (k10, drift) | −147,4 (k10, drift) | — |

ID12 = fakticky 200/200 (dt 0,75, k10): −151,1. ID16: nezkonvergoval, síť nezaznamenána (nevyřešeno).

### 4. Dlouhé běhy 4 s (ID9/10/11_long.dat)
- Okno 0,5–1,0 s NEBYLO stacionární (ID9 ještě stoupal −166→−174). Stacionarita od t≈1 s. **Finální čísla jen z dlouhých oken.**
- CSD závislost reálná a nemonotónní: 50→100 = +33,6 N (+24 %!), 100→200 = −15,8 N, vše významné.
- ID11 (200/200) osciluje trvale (std 36 N, p-p >300 N) — vlastnost hrubé CSD.

### 5. Klopení a pivot metriky
- Vrchlík se po nafouknutí ustálí v **kuželovém/klouzavém stavu ~38–42°** (|F_lat| ≈ 125–140 N ≈ |Fpz|). Steady stav při 20 m/s ≠ axiální sestup — potvrzena hypotéza uživatele.
- Přes výslednici |F|: CSD 50→100 efekt klesne z 24 % na 14 % (půlka „mesh efektu" byla poloha, půlka reálná zátěž). |F| = 220,1 / 188,6 / 201,5 N (CSD 50/100/200).
- **Priorita uživatele = nafukovací ráz (špička + čas špičky), ne steady.** Ráz (t_peak ≈ 0,15–0,17 s) probíhá PŘED rozvojem klopení → klopení ho nekontaminuje.
- Špičky staré matice: −574…−851 N, bez mesh-trendu, chaotický rozptyl ±10–15 % (n=1 na buňku nestačí!). t_fill ~50–75 ms robustní (výjimka ID11: 130 ms). Impulz ∫Fpz dt (0,1–0,6 s) mesh-robustní ±8 %. Podezření: sloupec CFD=200 má systematicky slabší špičky — možná artefakt nevyvinutého proudu při release 0,1 s (viz bod 6).
- 7,5 m/s (sestupová rychlost): NEdělat matici; kuželování je vlastnost statické stability a při 7,5 nejspíš přetrvá; pro sestup je správný nástroj finite-mass (drop). Max 1 průzkumný běh na finální síti.

### 6. Kampaň na špičku (BĚŽÍ)
**Protokol:** release SPC posunout z 0,1 s (proud urazil jen 2 m — nevyvinutý, navíc různě vyvinutý pro různé CFD sítě = falešný mesh efekt) do vyvinutého proudu. Špičky nového protokolu NEsrovnávat se starým.

**Pilot (2026-07-09, `ID10_death5.dat` rel=0,5 s / `ID10_death10.dat` rel=1,0 s, síť ID10 = CSD100/CFD200):**
- Plateau drženého vrchlíku: Fpz ustálené na −12,2 N už od ~0,3 s, dál dokonale stacionární → **release ≥ 0,4 s je bezpečný**.
- Ráz: death5 → peak **−687,6 N**, t_fill 70 ms, impulz −78,9 N·s; death10 → peak **−813,0 N**, t_fill 54 ms, impulz −83,5 N·s.
- **Perturbace release časem funguje**: 2 realizace z makroskopicky identické PP se liší o 17 % ve špičce → chaotická citlivost nafukování potvrzena; jednoběhová porovnání špiček jsou bezcenná; replikáty nutné.
- Nový protokol dává vyšší špičky než starý (−688/−813 vs −610 u ID10) → potvrzen confounder nevyvinutého proudu ve starém protokolu.
- **Rozhodující běh trend-vs-chaos (`ID10_death5005.dat`, death=0,5005 = posun o 1 dt):** pre-release trajektorie bitově shodná s death5; peak **−615,7 N**. Posun o 0,5 ms → 10,5% změna špičky, posun o 0,5 s → 18,2 % → **chaos dominuje**, vývoj úplavu není potřeba k vysvětlení (geometrie domény: box 30×30×100 m, vrchlík 29,7 m za inletem / 70,3 m před outletem; ocas úplavu se sice vyvíjí do ~3,5 s, ale zpětný vliv na vrchlík je omezen silovou stopou na <1 %). Release časy jsou platné replikáty.
- **Buňka B zatím (n=3):** peak −687,6 / −615,7 / −813,0 → průměr −705, std ~100 N (CV 14 %); impulz −78,9 / −80,1 / −83,5 → průměr −80,8, std 2,4 (CV **3 %**). → **Impulz je ~5× těsnější metrika než špička — primární metrika konvergence; špičku reportovat jako průměr ± pásmo** (návrhová obálka). Rychlejší plnění koreluje s vyšší špičkou (54 ms ↔ −813 N).

**Plán (L-design, 4 replikáty/buňku, release ~{0,5; 0,7; 0,9; 1,1} × endtim=release+0,5):**
| buňka | síť | stav |
|---|---|---|
| B | CSD100/CFD200 (deck ID10) | **hotovo 4/4** |
| A | CSD50/CFD200 (deck ID9) | **hotovo 4/4** |
| C | CSD100/CFD100 (deck ID6) | **hotovo 4/4** |

### VÝSLEDKY KAMPANĚ (2026-07-19, soubory ID{9,10,6}_death*.dat v kořeni)

Integrita ✓ (12 unikátních hashů), plateau ✓, žádný trend špičky s release časem (chaos potvrzen i napříč buňkami).

| buňka | síť | peak Fpz [N] | t_fill [ms] | impulz [N·s] |
|---|---|---|---|---|
| A | 50/200 | **−586 ±19** (CV 3 %!) | 69 ±8 | −77,8 ±3,9 |
| B | 100/200 | −710 ±82 (CV 12 %) | 64 ±7 | −80,9 ±1,9 |
| C | 100/100 | −771 ±52 (CV 7 %) | 55 ±2 | −82,7 ±2,3 |

Porovnání (Welch, 2·SE):
- **CSD 50→100 (A→B): špička Δ = −124 N VÝZNAMNÉ** (hrubá CSD nadhodnocuje špičku ~21 % a má 4× větší rozptyl); t_fill, impulz v šumu.
- **CFD 200→100 (B→C): t_fill Δ = −9 ms VÝZNAMNÉ** (jemnější CFD plní rychleji, ostřejší transient); špička Δ = −61 N stejným směrem (hrubá CFD ráz podhodnocuje = nekonzervativní!), ale pod prahem při n=4; impulz v šumu.
- **Impulz konvergovaný napříč vším** (−78…−83, rozdíly v šumu) — celkový přenos hybnosti je mesh-robustní; síť mění jen jeho časové rozložení (špičku).
- Bonus: jemná CSD (50) dělá nafouknutí výrazně reprodukovatelnějším (CV 3 % vs 12 %).

**Brána rozhodla: oba efekty reálné → doplnit buňku D = CSD50/CFD100 (deck ID5), 4 replikáty {0,5; 0,7; 0,9; 1,1}, endtim=release+0,5, ~20 h/běh.** Očekávání: peak ≈ −650 ±?; ověří, zda nízký rozptyl jemné CSD platí i s jemnou CFD. Po buňce D: finální volba produkční sítě + report + aktualizace grafů (artifact).

**Souběžně:** CSD=25/CFD=200 4s běh (starý protokol) — pro steady CSD konvergenci (čeká se). Pokud spadne v subiteracích → konečný NSUB, ne dt/kontakt.

## Inventář dat
- `data/fsi/` — appka (portál AerisVault, modul FSI): DB + raw/processed, 15 sims (květen, 1s běhy, steady okno biased)
- `Results/` — přepočtená matice v2 (12 unikátních běhů) + `FSI-results.xlsx` (nastavení)
- kořen repa: `ID9/10/11_long.dat` (4 s), `ID10_death5/death10.dat` (pilot kampaně)
- `data/fsi/_quarantine/` — karanténa vadných souborů (smazat po uzavření)

## To-Do
- [ ] Buňka B: +2 replikáty (release 0,7 a 0,9; endtim 1,2/1,4)
- [ ] Buňky A a C: po 4 replikátech
- [ ] CSD=25/CFD=200 (4 s, starý protokol) — vyhodnotit steady konvergenci
- [ ] Vyhodnocení kampaně (Claude): průměry±rozptyl, významnost, volba produkční sítě
- [ ] Nahrát finální data do aplikace; úklid (_quarantine, kořenové .dat, ID16)
- [ ] Volitelné: 1× 7,5 m/s na finální síti; finite-mass drop pro sestup
- [ ] Report: špička+t_fill+impulz s nejistotami, steady |F|+náklon, kontakt škálovaný se sítí, volba sítě

## Jak pokračovat s Claude
Nové vlákno v repu → „Pokračujeme v FSI mesh study, kontext je v `docs/fsi-mesh-study-log.md`". Claude má i persistentní paměť (`fsi-mesh-study.md` v memory adresáři tohoto projektu na tomto stroji); na cizím stroji stačí tento log. Analýzy: hash-check → parse `.dat` (sloupec 4 = Fpz) → block-means SEM na stacionárním okně.
