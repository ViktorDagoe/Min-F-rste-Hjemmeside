# 01 — Fysik

Du styrer **kræfter og momenter**. Software er kun den, der beder motorerne om de rigtige omdrejninger.

## Hover: den første ligning

I stillestående luft, uden vind:

**Samlet thrust opad = vægt nedad** → hover.

- Thrust **større** end vægt → stigning (positiv acceleration opad).
- Thrust **mindre** end vægt → fald.

Vægt er `m · g`. En 1,2 kg drone vejer ca. 12 N. Fire motorer skal tilsammen levere mindst 12 N i hover — plus margen til vind og manøvre. Tommelfinger: **hover ved ca. 50–70 % throttle**, så der er overskud til at stige og kæmpe mod vind.

Antagelse: “thrust” her er den lodrette komponent af rotorernes luftkraft. Når du vipper, peger en del af thrust vandret — så den lodrette rest falder, medmindre du skruer RPM op. Derfor synker en drone, der pitcher hårdt, hvis throttle ikke kompenserer.

## Newton, to gange

**Translation (flytning):**

`F_net = m · a`

Nettokraften (thrust-vektor + tyngde + luftmodstand + vind) ændrer hastigheden. Ingen nettokraft i en retning → konstant fart i den retning (eller nul).

**Rotation (drejning):**

`M = I · α`

Moment (kraft gange arm) ændrer vinkelhastigheden. På en quad kommer momentet fra **forskel i thrust** mellem motorer — og fra reaktionsmomentet fra rotorernes spin (yaw).

Det er derfor fire RPM’er kan styre fire akser: du ændrer *sum* (thrust) og *forskelle* (roll, pitch, yaw).

## Propelen er en luftpumpe

En rotor kaster luft ned. Ifølge 3. lov går der en kraft den anden vej: **thrust opad**.

Grov model (momentum theory):

- Thrust vokser med luftens masseflow og den hastighed, luften får.
- Effekt til hover vokser hårdt med vægt. Dobbelt vægt er *ikke* dobbelt watt — det er værre, fordi du både skal løfte mere og accelerere mere luft.
- Større rotor-skive (disk-areal) løfter mere effektivt ved samme vægt: lavere nedvind, mindre spild.

Derfor har store løfte-droner store propeller eller flere rotorer — ikke bare “stærkere motorer på de samme 5-tommer props”.

## Modstand, vind og “den usynlige væg”

Luftmodstand vokser groft med `½ · ρ · v² · C_d · A`.

Konsekvenser du kan mærke:

- Hurtig vandret flyvning koster batteri, også når højden er konstant.
- Modvind = du luder mere (mere tilt) = mere throttle = kortere tid.
- En kuffert-formet gimbal-kasse har højere drag end en slank ramme. Payload er ikke kun gram — det er også areal.

## Gyro-effekt (kort)

En spinnende propel er et lille gyroskop. Når du pitcher, “kæmper” rotoren imod og giver et side-moment. Flight controllere kompenserer for det i mixeren og i PID’en. Du behøver ikke regne det i hånden. Du skal vide, at **høje RPM og store props** gør effekten tydeligere, og at det er én grund til at firmware ikke bare er “mere throttle på den motor, der hælder”.

## Batteriet er den hårde grænse

Typisk LiPo til droner: i omegnen af **150–250 Wh/kg** på pakkeniveau, afhængigt af C-rating og kemi. Flybenzin er en anden liga i energitetthed. Derfor:

- Flyvetid på små quads: ofte 8–25 minutter, ikke timer.
- Ekstra last stjæler minutter to steder: mere hover-watt **og** mindre batteri-andel af startvægten, hvis du bytter celler ud med kamera.
- “Bedre software” kan spare lidt (glattere flyvning, bedre rute). Den ændrer ikke joule i cellen.

Hvis nogen lover 2 timers hover på 250 g med 4K-kamera, er det enten en anden kemi, en anden størrelse — eller salg.

## Kvadrat-kube (hvorfor “bare gør den større” fejler)

Hvis du skalerer en drone **lineært** med faktor `k` (alle længder × k):

- Arealer (rotor-skive, vinge, køling) ~ `k²`
- Volumener og masse (hvis samme tæthed) ~ `k³`

Massen vokser hurtigere end løftefladen. Hover-effekt og struktur skal følge med. Store maskiner kan stadig flyve — fly og helikoptere findes — men de betaler med:

- disproportionelt mere batteri eller brændstof
- andre materialer
- andre tilladelser
- anden logistik (transport, startplads, failsafe)

Detaljeret stige: [04-skalering-last-stoerrelser.md](04-skalering-last-stoerrelser.md).

## Insekt-skala: hvorfor en “bi med kamera” ikke er et mini-DJI

Reynolds-tallet `Re = ρ · v · L / μ` fortæller, om luften opfører sig **træg** (højt Re, fly og DJI) eller **viskos** (lavt Re, insekter).

På bi-størrelse:

- Luften “klistre”. Små, hurtige rotorer som på en 5-tommer racer virker dårligt.
- Naturen bruger **flaksende vinger** (leading-edge vortex, clap-and-fling) — ikke fire stive propeller.
- Motorer, batteri, radio og kamera har en **fast minimumsstørrelse**. Et kamera på 2 g er stadig en kæmpe last på en 0,1 g robobee.
- Styrefrekvensen skal være høj: små inertier, hurtige forstyrrelser.

Derfor er insekt-droner **research eller niche-mikro-UAV** (gram-klassen, kort rækkevidde), ikke “formindsk den forbrugerdrone 50 gange”. Kamera-bier findes som demonstration og som militær/industri-mikro (fx Black Hornet-klassen i 10–20 g-lejet). De er dyre, korte i luften, og lovgivning + link er ofte flaskehalsen — ikke 4K-sensoren.

## Hvad du skal kunne sige højt

1. Hover: thrust = vægt. Overskud = stigning.
2. Fire RPM’er: én sum + tre forskelle = thrust, roll, pitch, yaw.
3. Vandret fart = tilt + mere throttle, ellers synker du.
4. Batteriets Wh/kg sætter tiden. Kode sætter ikke joule.
5. Miniaturisering til bi rammer viskos luft og faste komponent-gulve — ikke bare 3D-print i mindre skala.

## Næste trin

Læs [02-arkitektur-og-schematics.md](02-arkitektur-og-schematics.md). Stop når du kan pege på **strømkortet** og **signalkortet** som to forskellige plantegninger.
