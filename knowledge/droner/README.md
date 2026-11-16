# Drone-håndbog

Civilt opslagsværk: fysik, hardware, styring, skalering og data — fra “bi med kamera” til survey-drone, og fra foto til plantegning.

Dette er et **valgfrit vidensspor**. Det erstatter ikke Kickstart og 90-dages roadmap i `manual/`.

## Antagelser

- **Civilt og lovligt:** inspektion, kortlægning, landbrug, film, forsknings-mikrodroner.
- **Ikke med:** våben, uautoriseret overvågning, jammer, geofence-/firmware-bypass, produktions-CAD klar til flyvning.
- **Mål:** forstå systemet og kunne forklare det. Ikke at lodde en flyvedygtig drone fra en stykliste i denne omgang.
- **Schematics her:** blokdiagrammer og styresløjfer i Markdown + Mermaid. Læsbare plantegninger — ikke fabriksskitse.
- **Plantegninger betyder to ting:** (1) drone-schematics, (2) bygningsplantegning fra lovligt indsamlet sensor-data.
- **Indkomstbro (senere, hvis overhovedet):** efterbehandling af data — kort, 3D, plantegning, inspektionsrapport. Ikke at sælge flyvning uden certifikat.

## Læserækkefølge

Læs i nummerorden første gang. Brug derefter som opslag.

| # | Fil | Du kan bagefter |
|---|---|---|
| 0 | [00-systemkort.md](00-systemkort.md) | Tegne kontrolsløjfen og data-grenen |
| 1 | [01-fysik.md](01-fysik.md) | Forklare hover, moment og hvorfor batteriet vinder |
| 2 | [02-arkitektur-og-schematics.md](02-arkitektur-og-schematics.md) | Pege på strøm vs. signal på en blokplantegning |
| 3 | [03-styring-og-kontrolvektorer.md](03-styring-og-kontrolvektorer.md) | Nævne de 4 kontrolvektorer og hvorfor du vipper for at køre frem |
| 4 | [04-skalering-last-stoerrelser.md](04-skalering-last-stoerrelser.md) | Placere en drone på størrelsesstigen og gætte last vs. flyvetid |
| 5 | [05-data-og-plantegninger.md](05-data-og-plantegninger.md) | Beskrive vejen foto → punkt sky → kort/plantegning |
| 6 | [06-loesninger-og-ai.md](06-loesninger-og-ai.md) | Skelne flyvning, dataarbejde og AI — plus DK/EU på 1 side |

Hver fil slutter med **ét næste trin**.

## Mindste handling nu

Åbn [00-systemkort.md](00-systemkort.md). Læs kernen. Tegn sløjfen med papir eller i hovedet, før du går videre.
