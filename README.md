# Koronavirus Suomen jätevesissä

Olen kerännyt [tähän](./data/) Terveyden ja hyvinvoinnin laitoksen julkaiseman koronaviruksen jätevesiseurannan [viikkoraportin](https://www.thl.fi/episeuranta/jatevesi/jatevesiseuranta_viikkoraportti.html) kaikki julkaistut aineistot 2022-04-29 (viikko 17) alkaen CSV-taulukkoina.

Taulukot ©THL, lisenssillä [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).


## Huomioitavaa

- Raportissa 2022-11-18 (viikko 46) taulukkoon lisättiin uuteen sarakkeeseen uudella menetelmällä (RNA-standardi) saadut määritystulokset. Uuden menetelmän tuloksia lisättiin takautuvasti usean kuukauden ajalle. Samalla sarakkeiden nimet muuttuivat ja yksi sarake poistettiin.

- Esikäsittelymenetelmä muuttui 2023-01-01, minkä jälkeen tulokset eivät THL:n mukaan ole täysin vertailukelpoisia aiempien kanssa. Asiantuntija Tarja Pitkänen kertoo muutoksesta tarkemmin [Twitterissä](https://nitter.net/TarjaPitkanen/status/1615355863530700801#m) (2023-01-17):

    > Uusi esikäsittelymenetelmä on lähes yhtä herkkä kuin vanha ja nopeampi tehdä. Jos seurattavaa mikrobia on jätevedessä paljon, niin eroa ei juuri ole. Menetelmämuutos siksi, että aiemmassa menetelmässä käytetyt kertakäyttöiset muoviset ultrasuodattimet loppuivat täysin maailmasta.

    Raportin mukaan uudella esikäsittelymenetelmällä määritysraja on kymmenen kertaa niin suuri kuin vanhalla. Menetelmämuutos saattaa siis alentaa tuloksia.

- Viive näytteenotosta analyysiin on kasvanut 2023-08-01 alkaen, mikä voi sekin alentaa tuloksia.


## Puuttuvat raportit

- En ole tallentanut lainkaan ennen 2022-03-11 (viikko 10) julkaistujen raporttien aineistoja.
- Ajalta 2022-03-11...04-22 (viikot 10–16) olen tallentanut vain kaksi raporttia, 2022-03-11 sekä 2022-04-08 (viikot 10 ja 14).
- Kesätauon 2022-07-22...29  (viikot 29–30) aikana raportteja ei julkaistu. Seuranta kuitenkin jatkui ja tulokset julkaistiin seuraavassa raportissa.
- Joulutauon 2022-12-29...2023-01-06 (viikot 52 ja 1) aikana raportteja ei julkaistu. Myös näytteenotto oli kaksi viikkoa tauolla.
- Kesätauon 2023-07-14...28 (viikot 28–30) aikana raportteja ei julkaistu. Myös näytteenotto oli kolme viikkoa tauolla, eli tuloksia siltä ajalta ei ole lainkaan.
- 2023-12-08 (viikko 49) raporttia ei julkaistu itsenäisyyspäivän vuoksi. Näytteet kuitenkin kerättiin ja ne analysoitiin ilmeisesti normaalia myöhemmin. Tulokset julkaistiin viikon 50 raportissa.
- Joulutauon 2023-12-29...2024-01-05 (viikot 52 ja 1) aikana näytteitä ei kerätty.


## Muuta

Komento raporttien välisten erojen tarkasteluun ilman ihmeempää lukujen käsittelyä:
```sh
GIT_PAGER='less -S' git diff -U0 --no-index \
    data/Koronaviruksen\ jätevesiseurannan\ viikkoraportti\ 2022-11-{11,18}.csv \
    --word-diff-regex='"[^\"]*"' --diff-algorithm=minimal
```


## Taulukon selitteet

-   **Näytteen päivämäärä**: Kokoomanäytteenoton (24 h) päättymispäivämäärä.
-   **Puhdistamo**: Seurannassa mukana olevan jätevedenpuhdistamon nimi.
-   **Puhdistamon sijainti**: Kunta, jolla jätevedenpuhdistamo sijaitsee.
-   **Puhdistamon asiakasmäärä**: Puhdistamon viemäriverkoston toiminta-alueella asuvien henkilöiden arvioitu lukumäärä.
-   **Koronavirustulos näytteestä**:
    -   Ei havaittu: puhdistamon jätevesinäytteestä ei havaittu viitteitä SARS-CoV-2 koronaviruksesta.
    -   Tulos epävarma: puhdistamon jätevedestä havaittiin alustavasti pieni määrä SARS-CoV-2 koronaviruksen geeniperimää (RNA:ta), mutta tulosta ei saatu varmistettua.
    -   Havaittu, alle määritysrajan: puhdistamon jätevedessä havaittiin pieni määrä SARS-CoV-2 koronaviruksen RNA:ta. RNA-lukumäärä ylitti analyysimenetelmän toteamisrajan, mutta jäi määritysrajan alle.
-   Havaittu, yli määritysrajan: puhdistamon jätevedessä todettu SARS-CoV-2 koronaviruksen RNA-lukumäärä normalisoituna kokoomanäytteen keräysajankohdan tulovirtaamaan 1000 henkilöä kohti.
-   **Epävarmuustekijät**: Taulukkoriville on lisätty kirjainsymboli (a, b tai c), mikäli saatuun SARS-CoV-2 koronaviruksen RNA-tuloksen analysointiin liittyy yksi tai useampi tuloksen luotettavuutta heikentävä epävarmuustekijä.
    -   a = näytteen lämpötila yli 15 astetta näytteen saapuessa laboratorioon.
    -   b = näytteessä on todettu määritystä häiritseviä tekijöitä (inhibitio).
    -   c = yli 14vrk viive näytteen keräämisen ja analyysin aloituksen välillä, kertanäyte tai poikkeava keräysaika.
    -   () = epävarmuustekijää ei ole testattu tai tieto puuttuu.
-   **Virtaama**: Jätevedenpuhdistamolle kokoomanäytteenoton (24h) aikana saapuneen jäteveden määrä kuutioina (m3).
-   **Normalisoitu RNA-lukumäärä DNA-standardilla**: Normalisoitu RNA-lukumäärä (määritysrajan, 803 geenikopiota/100ml, ylittävät tulokset): miljoonaa virus-RNA kopiota/1000 hlö/vrk. Tuloksia ajalta 3.8.2020 - 7.11.2022.
-   **Normalisoitu RNA-lukumäärä RNA-standardilla**: Normalisoitu RNA-lukumäärä (määritysrajan, 12 geenikopiota/100ml, ylittävät tulokset): miljoonaa virus-RNA kopiota/1000 hlö/vrk. Tuloksia 27.6.2022 alkaen. Esikäsittelymenetelmä muuttui 1.1.2023 (uusi määritysraja, 121 geenikopiota/100ml). Sen jälkeen julkaistut tulokset eivät ole täysin vertailukelpoisia aikaisempien tulosten kanssa.

Kopioitu 2023-12-15 (viikko 50) julkaistusta raportista.

