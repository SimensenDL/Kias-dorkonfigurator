I now have a complete picture. Let me compile the text for you.

Her er teksten du kan kopiere og feede til Claude Code:

---

## Transportmål-kalkulator – Fullstendig forklaring

### Konsept

Arket "Transportmål" beregner **transportåpninger** (den faktiske plassen tilgjengelig for å flytte gjenstander gjennom en dør) basert på karmtype, karmmål, og dørtype. Eksempelet bruker en M10x21-dør (ca. 1010 mm bred × 2110 mm høy utsparing i vegg).

### Karmgrupper og hvordan karmmål beregnes fra veggåpning

Det finnes 3 karmgrupper som definerer forholdet mellom **utsparing i vegg (Uts. Vegg)** og **karmmål**:

| Gruppe | Karmtype                | Bredde karm               | Høyde karm               |
| ------ | ----------------------- | ------------------------- | ------------------------ |
| 1      | SD1/BD1, KD1/YD1, PD1…E | Uts. Vegg bredde **+ 70** | Uts. Vegg høyde **+ 30** |
| 2      | SD2/BD2, KD2/YD2, PD2…E | Uts. Vegg bredde **+ 90** | Uts. Vegg høyde **+ 40** |
| 3      | SD3/ID, KD3/YD3         | Uts. Vegg bredde **− 20** | Uts. Vegg høyde **− 20** |

For **pardører (2-fløy, PD…D)** gjelder:

- PD1…D: Bredde = Uts. Vegg bredde + 70, Høyde = Uts. Vegg høyde + 30 (gruppe 1-logikk, men ca. dobbel bredde for 2-fløy)
- PD2…D: Bredde = Uts. Vegg bredde + 90, Høyde = Uts. Vegg høyde + 40 (gruppe 2-logikk)

### Dørtyper i tabellen

**Slagdører / Branndører (SD/BD) – rad 4-6:**

- SD1/BD1 (gruppe 1): Karm B=1080, H=2140. Formler: `Karm B = Uts.Vegg B + 70`, `Karm H = Uts.Vegg H + 30`
- SD2/BD2 (gruppe 2): Karm B=1100, H=2150. Formler: `Karm B = Uts.Vegg B + 90`, `Karm H = Uts.Vegg H + 40`
- SD3/ID (gruppe 3): Karm B=990, H=2090. Formler: `Karm B = Uts.Vegg B − 20`, `Karm H = Uts.Vegg H − 20`

**Kjøledører / Ytterdører (KD/YD) – rad 8-10:**

- KD1/YD1 (gruppe 1): Karm B=1080, H=2140. Samme gruppe 1-relasjoner.
- KD2/YD2 (gruppe 2): Karm B=1100, H=2150. Samme gruppe 2-relasjoner.
- KD3/YD3 (gruppe 3): Karm B=990, H=2090. Samme gruppe 3-relasjoner.

**Pendeldører enkelfløy (PD…E) – rad 12-13:**

- PD1…E (gruppe 1): Karm B=1080, H=2140.
- PD2…E (gruppe 2): Karm B=1100, H=2150.

**Pendeldører dobbelfløy (PD…D) – rad 14-15:**

- PD1…D: Karm B=2080, H=2140. (dobbel bredde)
- PD2…D: Karm B=2100, H=2150. (dobbel bredde)

---

### Transportåpning-beregninger (kolonne F–L)

#### Kolonne F: Transportåpning bredde ved 90° åpning av dør

Beregner fri bredde når døren åpnes 90 grader. Fradragene varierer per karmtype pga. ulik karmprofiltykkelse og dørbladstykkelse:

| Karmtype | Formel                    | Forklaring                                              |
| -------- | ------------------------- | ------------------------------------------------------- |
| SD1/BD1  | `Karm B − 160 − 30`       | 160 = 2×80 karmfalsprofil, 30 = dørblad i åpen posisjon |
| SD2/BD2  | `Karm B − 160 − 30`       | Samme profil som SD1                                    |
| SD3/ID   | `Karm B − 44 − 44 − 35`   | 44 mm karmfals per side, 35 = dørblad/hengsel           |
| KD1/YD1  | `Karm B − 100 − 100 − 50` | 100 mm karmfals per side, 50 = dørblad                  |
| KD2/YD2  | `Karm B − 100 − 100 − 50` | Samme som KD1                                           |
| KD3/YD3  | `Karm B − 46 − 46 − 50`   | 46 mm karmfals, 50 = dørblad                            |
| PD1…E    | `Karm B − 240`            | Pendeldør har bredere beslag/karmfals                   |
| PD2…E    | `Karm B − 240`            | Samme som PD1E                                          |
| PD1…D    | `Karm B − 290`            | 2-fløy pendeldør, bredere fradrag                       |
| PD2…D    | `Karm B − 290`            | Samme som PD1D                                          |

#### Kolonne G: Transportåpning bredde ved 180° åpning av dør

Beregner fri bredde når døren åpnes helt opp (180°). Dørbladet folder helt bak karmen, så fradrag er mindre (bare karmprofil):

| Karmtype | Formel               | Forklaring                        |
| -------- | -------------------- | --------------------------------- |
| SD1/BD1  | `Karm B − 160`       | Kun karmfals, dørblad ut av veien |
| SD2/BD2  | `Karm B − 160`       | Samme                             |
| SD3/ID   | `Karm B − 44 − 44`   | Kun karmfals per side             |
| KD1/YD1  | `Karm B − 100 − 100` | Kun karmfals                      |
| KD2/YD2  | `Karm B − 100 − 100` | Samme                             |
| KD3/YD3  | `Karm B − 46 − 46`   | Kun karmfals                      |
| PD…E/D   | `-` (ikke mulig)     | Pendeldører kan ikke åpnes 180°   |

#### Kolonne H: Transportåpning høyde ved luftespalte (22mm) / slepelist (LS 22mm)

Beregner fri høyde med kun luftespalte og slepelist (ingen terskel):

| Karmtype | Formel         | Fradrag fra karm H           |
| -------- | -------------- | ---------------------------- |
| SD1/BD1  | `Karm H − 80`  | 80 mm (karmhode + slepelist) |
| SD2/BD2  | `Karm H − 60`  | 60 mm                        |
| SD3/ID   | `Karm H − 44`  | 44 mm (karmhode)             |
| KD1/YD1  | `Karm H − 100` | 100 mm                       |
| KD2/YD2  | `Karm H − 100` | 100 mm                       |
| KD3/YD3  | `Karm H − 46`  | 46 mm                        |
| PD1…E/D  | `Karm H − 80`  | 80 mm for alle pendeldører   |
| PD2…E/D  | `Karm H − 80`  | 80 mm                        |

#### Kolonne I: Transportåpning høyde ved terskel 37mm (LS 22mm)

Fri høyde med standard terskel (37mm) og slepelist (22mm):

| Karmtype | Formel              | Forklaring                               |
| -------- | ------------------- | ---------------------------------------- |
| SD1/BD1  | `Karm H − 60 − 37`  | 60 mm topp + 37 mm terskel               |
| SD2/BD2  | `Karm H − 60 − 37`  | Samme                                    |
| SD3/ID   | `Karm H − 44 − 37`  | 44 mm topp + 37 mm terskel               |
| KD1/YD1  | `Karm H − 100 − 37` | 100 mm topp + 37 mm terskel              |
| KD2/YD2  | `Karm H − 100 − 37` | Samme                                    |
| KD3/YD3  | `Karm H − 46 − 37`  | 46 mm topp + 37 mm terskel               |
| PD…E/D   | `-`                 | Pendeldører bruker ikke standard terskel |

#### Kolonne J: Transportåpning høyde ved kjørbar terskel 25mm (LS 13mm)

Fri høyde med kjørbar terskel (25mm) og kortere slepelist (13mm):

| Karmtype | Formel              | Forklaring                   |
| -------- | ------------------- | ---------------------------- |
| SD1/BD1  | `Karm H − 60 − 25`  | 60 mm topp + 25 mm terskel   |
| SD2/BD2  | `Karm H − 60 − 25`  | Samme                        |
| SD3/ID   | `Karm H − 44 − 25`  | 44 mm topp + 25 mm terskel   |
| KD1/YD1  | `Karm H − 100 − 25` | 100 mm topp + 25 mm terskel  |
| KD2/YD2  | `Karm H − 100 − 25` | Samme                        |
| KD3/YD3  | `Karm H − 46 − 25`  | 46 mm topp + 25 mm terskel   |
| PD…E/D   | `-`                 | Ikke aktuelt for pendeldører |

#### Kolonne K: Transportåpning høyde ved HC-terskel 20mm (LS 8mm)

Fri høyde med HC-terskel (universell utforming, 20mm) og kort slepelist (8mm):

| Karmtype | Formel              | Forklaring                  |
| -------- | ------------------- | --------------------------- |
| SD1/BD1  | `Karm H − 60 − 20`  | 60 mm topp + 20 mm terskel  |
| SD2/BD2  | `Karm H − 60 − 20`  | Samme                       |
| SD3/ID   | `Karm H − 44 − 20`  | 44 mm topp + 20 mm terskel  |
| KD1/YD1  | `Karm H − 100 − 20` | 100 mm topp + 20 mm terskel |
| KD2/YD2  | `Karm H − 100 − 20` | Samme                       |
| KD3/YD3  | `Karm H − 46 − 20`  | 46 mm topp + 20 mm terskel  |
| PD…E/D   | `-`                 | Ikke aktuelt                |

#### Kolonne L: Transportåpning høyde ved HCID-terskel 25mm (LS 18mm)

Kun relevant for SD3/ID-karm:

| Karmtype   | Formel             |
| ---------- | ------------------ |
| SD3/ID     | `Karm H − 44 − 20` |
| Alle andre | `-` (ikke aktuelt) |

---

### Hvilke karmer passer til hvilke dørtyper

| Dørtype                                | Tillatte karmer                        |
| -------------------------------------- | -------------------------------------- |
| **SDI (Slagdør innvendig)**            | SD1, SD2, SD3 (SD3 = ID-karm)          |
| **BD (Branndør B30)**                  | SD1 (BD1 = SD1)                        |
| **KD (Kjøledør)**                      | KD1, KD2, KD3                          |
| **YD (Ytterdør)**                      | YD1, YD2, YD3 (YD = KD-profil)         |
| **FD (Fjøsdør)**                       | FD1, FD2 (= KD1, KD2), FD3 (= KD3)     |
| **PDPC/PDPO (Pendeldør polykarbonat)** | PD1, PD2 (enkelfløy E / dobbelfløy D)  |
| **PDI (Pendeldør isolert)**            | PD1, PD2 (enkelfløy E / dobbelfløy D)  |
| **ID (Innerdør)**                      | SD3/ID-karm (innerdørkarm med notspor) |
| **BO (Boddør)**                        | Boddørkarm med notspor (egen type)     |

### Viktige notater

- Alle mål er i **millimeter (mm)**
- "Uts. Vegg" = Utsparing i vegg (hullet i veggen)
- YD (Ytterdør) bruker samme karmprofiler som KD (Kjøledør) / FD (Fjøsdør) – se notat i B25: "YD = KD / FD?"
- FD3 er antatt lik KD3
- Pendeldører (PD) kan **ikke** åpnes 180° og bruker **ikke** standard terskel/kjørbar terskel/HC-terskel
- Pardører (2-fløy, …D) har ca. dobbel bredde men samme høydefradrag som enkelfløy
