# 06 — Løsninger, AI og lov (kort)

Dette spor lærer systemet. Penge — hvis de kommer — sidder i **lovligt indsamlet data, gjort brugbart**. Ikke i at eje en drone. Ikke i at styre motorer fra et chatvindue.

Kickstart-pakken i `sales/` er stadig første indkomstspor. Dette kapitel er et **senere** bro-kort, ikke en ny prisliste.

## Civile løsninger (hvad maskinen er til)

| Job | Typisk klasse | Data-produkt |
|---|---|---|
| Ejendoms- og arkitektfoto | sub-250 g til 2 kg | Still, kort video |
| Tag, skorsten, solceller | 1–2 kg + obliques/termisk | Annoteret rapport |
| Byggeplads / mængder | 2 kg + RTK, gentagne grid | Ortofoto, volumen |
| Landbrug | 2 kg + multispektral | NDVI, zoner |
| Kortlægning / GIS | RTK-arbejdsdrone | Ortofoto, DSM, fodaftryk |
| Vegetation / ledningsgade | LiDAR 5–15 kg | Klassificeret sky |
| Film | cine-klasse, gimbal | Billeder, ikke GIS |
| Indoor dokumentation | SLAM-rig eller indoor-drone | Punkt sky, rumplan |

Ikke på listen: våben, jammer, skjult overvågning, bypass af geofence eller firmware. Det er uden for sporet.

## Tre roller — bland dem ikke

1. **Pilot / operatør** — luftfart, sikkerhed, certifikat, forsikring, flyvning.
2. **Databehandler** — fotogrammetri, GIS, CAD, rapport. Kan være en anden person.
3. **AI-assistent** — klassificering, tekst, QA-tjek på *færdige* lag.

En begynder i denne workstation kan sigte mod rolle 2–3 **på data, der allerede er lovligt taget** (kunde flyver, eller en certificeret partner). Rolle 1 er et spor for sig: uddannelse, A2-teori, evt. Specific.

## Hvor AI faktisk hjælper

Virker:

- Find solceller, tagvinduer, biler på ortofoto (detektion)
- Sammenlign to epoker (change detection)
- Første udkast til inspektionsrapport ud fra annoteringer
- Klassificer punkt sky groft (jord / bygning / vegetation) — med menneske-QA
- Spor fodaftryk som *forslag*; du retter i QGIS

Virker ikke som magi:

- “Lav en indvendig plantegning” fra 12 dronebilleder af facaden
- Styrate-loop og ESC-mix fra ChatGPT
- Absolutte temperaturer fra ét ukalibreret termisk screenshot
- Lovligt BVLOS fordi modellen “godt kan”

AI er et **lag på produktet**, ikke en erstatning for overlap, RTK og en pilot, der følger reglerne.

## Mini-pipeline til et sælbart data-produkt (senere)

Kun når flyvningen er lovlig og aftalt:

1. Brief: hvad skal kunden *åbne* fredag? PDF-rapport, GeoTIFF, DWG-skitse?
2. Capture-plan: grid, GSD, RTK/GCP, overlap.
3. Process: sky + ortofoto.
4. Menneske: mål-check på jorden, ret forkerte kanter.
5. AI (valgfri): forslag til skader/objekter, rapport-udkast.
6. Leverance: filer med navne + 10 linjers brugsnote. Samme standard som i `manual/05-leverancer.md`.

Hvis du ikke kan beskrive filen kunden får, er du ikke i salg endnu — du er i hobby-flyvning.

## DK/EU på én side (ikke juridisk rådgivning)

Reglerne ændrer sig. **Kilde:** Trafikstyrelsen (droneområde) og EASA’s Open/Specific. Læs dem, før du flyver. Dette er et hukommelseskort, ikke en tilladelse.

**Open-kategori** (forenklet idé):

- **A1** — tæt på mennesker med *meget* lette/C0–C1-maskiner, med restriktioner. Ikke over folkemængder.
- **A2** — tættere på folk med visse C2-maskiner, **kræver A2-teorieksamen** plus afstandskrav.
- **A3** — langt fra folk, større Open-maskiner, “flyv hvor du ikke er til fare”.

**Vægt og klasse-mærke (C0–C6)** styrer, hvad der må hvad. Sub-250 g er *lettere* i Open — ikke lovløs. Registrering af operatør, drone-mærkning, forsikring: tjek gældende krav.

**Specific-kategori:** når Open ikke rækker (BVLOS, tungere, by, standardscenarier). Kræver operationstilladelse / erklæring efter gældende ordning.

**Andet, du ikke må glemme:**

- Fotografering og persondatabeskyttelse (ansigter, haver, arbejdspladser)
- No-fly: lufthavne, visse institutioner, midlertidige zoner — tjek kort før hver flyvning
- Forsikring og ansvar ved nedfald

Hvis der er tvivl: **lænd på jorden** og læs Trafikstyrelsen. Denne håndbog overtrumfer ikke loven.

## Forhold til Kickstart

Du sælger ikke “drone-fysik”. Du sælger, hvis nogensinde, et **synligt kort eller en rapport**. Før det: færdiggør projekt 1–5 og Kickstart. Dette mappe-spor er forståelse + et senere håndværk.

## Hvad du skal kunne sige højt

1. Fire vektorer, tilt for at køre, batteri som grænse — fra 00–04.
2. Foto med overlap bliver kort; udendørs kort er ikke stueplan — fra 05.
3. AI annoterer og skriver; den flyver ikke rate-loop.
4. Trafikstyrelsen er kilden. Open A1/A2/A3 er startkortet.
5. Første betalte opgave i denne repo er stadig Kickstart, ikke en LiDAR-oktokopter.

## Næste trin

Gå tilbage til [00-systemkort.md](00-systemkort.md). Tegn flyvesløjfen og datagrene på papir uden at kigge. Hvis de 4 kontrolvektorer sidder fast, er sporet læst — ikke memoriseret som katalog, men som system.
