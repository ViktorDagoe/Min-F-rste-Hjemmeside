# 04 — Prompt-håndværk

## Regel nr. 1

En god prompt er en **arbejdsordre**, ikke et ønske.

Dårligt:

> Skriv noget tekst til min hjemmeside.

Godt:

> Skriv dansk hjemmesidetekst til en autoværksted i Odense.
> Målgruppe: bilejere 25–60 år.
> Tone: klar, lokal, troværdig. Ingen superlativer.
> Output: hero-overskrift, undertekst, 3 fordele, CTA, FAQ med 5 Q&A.
> Længde: max 250 ord i alt for hero+fordele.

## Prompt-skabelon (brug altid)

Kopiér denne struktur:

```text
ROLLE:
Du er [rolle] med fokus på [resultat].

KONTEKST:
Kunde/virksomhed: ...
Målgruppe: ...
Mål: ...
Begrænsninger: ...

OPGAVE:
Lav præcis [output].

FORMAT:
- punkt 1
- punkt 2

KVALITETSKRAV:
- Dansk, konkret, ingen fluff
- Ingen påstande uden belæg
- Afslut med CTA
```

Se også: `prompts/00-prompt-skabelon.md`

## De 6 knapper du kan skrue på

1. **Rolle** — hvem AI’en skal være
2. **Kontekst** — hvem det er til
3. **Opgave** — hvad der skal laves
4. **Format** — hvordan svaret skal se ud
5. **Eksempler** — 1–2 gode/dårlige samples
6. **Constraints** — hvad der er forbudt

Jo mere specifik du er på knap 2, 4 og 6, jo bedre output.

## Iteration (sådan bliver det godt)

Du laver sjældent det færdige resultat i første hug.

Brug denne loop:

1. Generér v1
2. Bed om kritik: “Find 5 svagheder ift. klarhed, CTA og lokal relevans”
3. Bed om v2 med rettelser
4. Ret selv fakta og tone
5. Gem

## Prompt-typer du skal mestre først

| Type | Formål | Fil |
|---|---|---|
| Research | forstå kunde/niche | `prompts/01-research.md` |
| Tekst | hjemmeside/opslag | `prompts/02-tekst-marketing.md` |
| Web | sidestruktur/HTML | `prompts/03-web-struktur.md` |
| Salg | tilbud/mails | `prompts/04-salg-tilbud.md` |
| QA | fejlfind før levering | `prompts/05-kvalitetstjek.md` |

## Tre fejl begyndere laver

1. **For vag opgave** → AI gætter
2. **For mange opgaver i én prompt** → rodet resultat
3. **Ingen rettelse** → generisk tekst der ikke kan sælges

## Øvelse (20 min)

Vælg en lokal virksomhedstype (fx renseri, dyreklinik, elektriker).

Lav 3 prompts:

1. Hero-tekst til hjemmeside
2. 5 FAQ-svar
3. Opfølgningsmail efter tilbud

Gem dem i `prompts/` eller i dit aktuelle projekt.

## Næste fil

Læs [05 — Leverancer der kan sælges](05-leverancer.md).
