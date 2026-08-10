# Prompts — Kvalitetstjek

## 1) Hård redaktør

```text
Du er en streng dansk forretningsredaktør.
Gennemgå teksten og find:
1. Fluff-sætninger
2. Uklare CTA’er
3. Påstande uden belæg
4. For lange afsnit
5. Manglende lokal relevans

Giv:
- Score 0–10
- Top 5 rettelser
- Omskrevet version

Tekst:
[indsæt]
```

## 2) Kundetest (skeptic)

```text
Spil en travl virksomhedsejer i [branche].
Du har 20 sekunder. 
Sig ærligt:
1. Forstår jeg tilbuddet?
2. Stoler jeg på det?
3. Ved jeg hvad jeg skal gøre nu?
4. Hvad får mig til at sige nej?

Tekst/side:
[indsæt]
```

## 3) Leverance-accepttest

```text
Tjek om denne leverance er kunde-klar.
Kriterier:
- Kan bruges uden ekstra forklaring
- Filstruktur er tydelig
- Antagelser er markeret
- Scope er overholdt
- CTA’er er konkrete

Returnér: GODKENDT / IKKE GODKENDT + checklist.
```
