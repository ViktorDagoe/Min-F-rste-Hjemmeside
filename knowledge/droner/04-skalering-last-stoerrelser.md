# 04 — Skalering, last og størrelser

Størrelse er ikke æstetik. Den sætter **hvad du kan løfte, hvor længe, hvilke sensorer, og hvilket regelspor** du er på.

Tallene nedenfor er **ordenstørrelser**, ikke et produktkatalog. Mærker ændrer sig. Fysikken gør ikke.

## Størrelsesstigen

| Klasse | Masse (orden) | Hvad den kan bære | Typisk lufttid | Flaskehals |
|---|---|---|---|---|
| Insekt / robobee | 0,1–2 g | Næsten ingen. Kamera er research | sekunder–få min | Reynolds, effekt, radio |
| Mikro-UAV (fx Black Hornet-klasse) | ~10–20 g | Lille EO-kamera | ~10–25 min | Rækkevidde, pris, lov |
| Sub-250 g (C0-agtig) | under 250 g | Let 4K / 12 MP | 10–20 min | Vind, last, rækkevidde |
| Arbejdsdrone | ~0,7–2 kg | Gimbal-RGB, lille termisk | 20–45 min | Batteri vs. overlap-flyvning |
| Cinema / let survey | ~2–6 kg | Større kamera, RTK | 20–35 min | Vind, certificering |
| LiDAR / tung sensor | ~5–15 kg | LiDAR + RGB + RTK | 15–30 min | Watt, kalibrering, pris |
| Heavy / special | 25 kg+ | Kasse, spray, stor LiDAR | meget variabel | Tilladelse, logistik, fail |

“Bi med kamera” bor i de **to øverste rækker**. En DJI Mini-agtig 249 g er *ikke* en bi — den er allerede et konventionelt rotorcraft, bare let.

Store dataindsamlere bor i **arbejdsdrone og opefter**. Punkt sky i landmålingskvalitet vil have RTK og planlagt overlap — ikke et håndholdt hero-shot.

## Last er tre tal, ikke ét

Når nogen siger “den løfter 2 kg”, spørg:

1. **Payload-masse** — kamera, gimbal, LiDAR, computer.
2. **Hover-margen** — hvor meget thrust der er tilbage i vind og ved fuld gimbal-vinkel.
3. **Energi** — minutter *efter* at payloaden er sat på.

En drone der hover’er 28 minutter tom, kan lande på 16 med LiDAR. Det er forventeligt: mere watt i hover, og batteriet er den samme pakke (eller en tungere, som igen stjæler payload-budget).

Tyngdepunkt: payload foran eller under skifter trim. FC’ens I-led tager noget. Mekanisk dårlig CG tager resten i oscillation og dårligere billeder.

## Disk-areal vs. vægt

Fra [01-fysik.md](01-fysik.md): hover-effekt falder, når rotor-skiven er større ved samme masse.

Praktisk:

- Racing 5" props: dårlig hover-økonomi, god til acceleration.
- Fotodroner: større props, lavere RPM, længere tid.
- Heavy lift: store blade eller mange rotorer (hexa/octo) — redundant plus disk-areal.

Octo er ikke “fordi 8 er sejt”. Det er disk-areal, redundancy (én motor død) og plads til at sprede last. Prisen er flere ESC’er, mere fejlflade, mere vægt.

## Kvadrat-kube, anvendt på stigen

Skalér en 1 kg-drone op til 8 kg ved at gange længder med 2 (hvis det var en ren skalamodel): masse ~ 8×, skiveareal ~ 4×. Du har 8 gange vægt på 4 gange løfteflade. Hover bliver dyr, strukturen skal tykkere (endnu mere masse). Virkelige store droner **ændrer form**: andre profiler, andre materialer, andre batteri-andele, nogle gange hybrid (generator).

Derfor hopper industrien i **klasser**, ikke i kontinuerlig zoom. Hver klasse har sit payload-vindue.

## Batteri-andel

Grov virkelighed på mange quads: batteriet er **30–50 %** af startmasse.

- Mere batteri → længere tid, indtil rammen og motorerne ikke kan løfte det effektivt.
- Mere payload → du fjerner batteri eller accepterer kortere tid.
- Høj C-rating (racer) vejer og koster for at levere ampere, ikke Wh.

Survey-flyvning er ofte **mange korte batterier** (byt på 15–20 min) plus et fast mønster, ikke én hero-flyvning på 50 min.

## Hvad hver klasse er *til* (civilt)

**Insekt / mikro:** forskning, korte kig ind i rum, hvor en 1 kg-maskine ikke kan. Ikke volumendata. Link og lov er ofte tættere loftet end megapixels.

**Sub-250 g:** øvelse, ejendomsfoto, simple inspektioner i åben kategori med færre krav (tjek gældende regler). Dårlig i kuling. Lille overlap-kort over et hus er muligt; stor mark med RTK-kvalitet er det typisk ikke.

**1–2 kg arbejdsdrone:** hus, tag, solceller, mindre byggeplads, ortofoto. Det er default-svaret på “drone der samler data” for SMV.

**5–15 kg:** LiDAR i vegetation, længere stræk, cinema-full-frame. Kræver pilot, procedure, ofte Specific-kategori. Data er dyrt at *tage* og dyrt at *regne*.

**25 kg+:** sprøjtning, tung cargo, special. Det er et luftfartsprojekt, ikke en weekendmaskine.

## Vind og skala

Små maskiner har lav inerti og højt areal/masse. Et vindstød flytter dem. Store har mere momentum, men større areal og højere kinetisk energi ved fejl — derfor andre afstande, andre fail-modes, andre tilladelser.

Tommelfinger: hvis du skal bruge dataene, flyv **ikke** på kanten af vindspec. Bevægelsessløring og RTK-afbrydelser ødelægger reconstrueringen billigere, end du sparer i “nåede det i dag”.

## Hvad du skal kunne sige højt

1. Bi-kamera ≠ mini-arbejdsdrone. Forskellig fysik, forskellig last.
2. Last = gram + watt + minutter + CG.
3. Større rotor-skive er effektiv hover; racing-props er det ikke.
4. Masse vokser hurtigere end løfteflade, hvis du bare skalerer.
5. Survey-kvalitet bor på RTK + plan + batteribyt — ikke på den største prop alene.

## Næste trin

Læs [05-data-og-plantegninger.md](05-data-og-plantegninger.md). Stop når du kan skelne **udendørs fodaftryk** fra **indvendig plantegning** og nævne kæden foto → punkt sky → produkt.
