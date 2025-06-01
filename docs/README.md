# CAMsync

**CAMsync** ist ein Hilfstool zur Verwaltung und Pflege einer Werkzeugdatenbank. Es unterstützt verschiedene Wartungs-, Bereinigungs- und Synchronisationsfunktionen für Werkzeugdaten.

---

## 1. Tool Rework (Einzelfunktionen)

### Funktion: Löschen von Komplettwerkzeugen mit bestimmten Statuswerten

Alle Komplettwerkzeuge mit einem der folgenden Status werden gelöscht:

- **Gelöscht**  
- **Auslaufwerkzeug**  
- **Gesperrt**  
- **Nicht für Werk 'ROD' freigegeben**

---

### Funktion: Status-Kennung als Präfix im Werkzeugnamen

Werkzeuge erhalten abhängig vom Status ein Präfix:

- `+` = Favorit  
- `F` = Freigegeben  
  - z. B. "ROD Frei", "WÜM Sonder"  
- `K` = Auftrags-Komplettwerkzeug  
- `S` = Sonderstatus, z. B.:  
  - ROD Sonder / WÜM Frei  
  - Sonderbeschaffung  
  - Form- oder Sonderwerkzeug  
  - Beigestelltes Werkzeug  
  - Inaktiv (nicht in Verwendung in beiden Datenbanken)  
  - Versuchswerkzeug  

---

### Funktion: Materialien automatisch in neue Kategorien überführen

| **Altbezeichnung**                              | **Neue Bezeichnung**                                        |
|-------------------------------------------------|-------------------------------------------------------------|
| Aluminiumlegierungen (normal)                   | Aluminium-Knetlegierungen Si < 6 %                         |
| Kupferlegierungen (normal)                      | Kupfer-Knetlegierungen Bronze                              |
| Hartbearbeitung Stähle > 45 HRC                 | Gehärteter Werkzeugstahl > 60 HRC                          |
| Titan und Titanlegierungen                      | Titan-Legierungen > 300 HB (z. B. Ti6Al4V)                 |
| Inconel und Sonderlegierungen                   | Nickelbasislegierungen, präzisionsgehärtet (Inconel 718)   |
| Edelstähle / rostfreier Stahl (normal)          | Rostfreier Stahl (z. B. Cr-Ni-Mo, Werkstoff 1.4571)        |
| Stahlwerkstoffe (normal zerspanbar)             | Stahl 500–850 N/mm² (bis 24 HRC)                           |
| Stahlwerkstoffe (schwer zerspanbar)             | Stahl 850–1100 N/mm² (24–34 HRC)                           |
| Kunststoffe allgemein (kein CFK, GFK usw.)      | Thermoplaste                                               |

---

### Funktion: Löschen ungültiger Werkzeuge aus der Datenbank

Wenn ein Werkzeug beim Import als ungültig erkannt wird:

- werden **NC-Tool**, **Tool**, **Halter** und **Verlängerung** aus der SQL-Datenbank gelöscht
- das Werkzeug wird zurück in den Sync-Ordner verschoben und der Import erneut versucht

**Achtung:** Werkzeuge, die dauerhaft ungültig sind, laufen so in einer Endlosschleife. Daher regelmäßig prüfen und ggf. bereinigen.

---

### Funktion: Werkzeuge in Toolklassen einsortieren

- Die entsprechenden **Schnittklassen** müssen bereits in der Datenbank vorhanden sein.
- Die Werte müssen in der **hyperMILL-Datenbank** gepflegt werden.
- Beispielklasse: `Kennametal_Universal`

---

## 2. Depot-Synchronisation

- Depots werden automatisch in der Datenbank angelegt.
- Der Depotname entspricht dem Namen der Excel-Datei im konfigurierten Verzeichnis.
- In **Spalte A** der Excel-Datei müssen Komplettwerkzeugnummern eingetragen sein.
- Alle dort gelisteten Werkzeuge werden dem Depot hinzugefügt bzw. bei Vorhandensein überschrieben.
- **Empfehlung:** Vor dem Import das bestehende Depot manuell löschen, da nicht mehr gelistete Werkzeuge sonst erhalten bleiben.

---

## 3. Clean_Projekt

- Diese Funktion löscht `.stl`- und `.vis`-Dateien, die älter sind als die in der Konfiguration festgelegte Anzahl an Tagen.
- **Tipp:** Vor dem endgültigen Löschen sollte der **Dry Run** aktiviert werden, um die zu löschenden Dateien zunächst nur anzuzeigen.







## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).  
Die Nutzung ist kostenlos für private und nichtkommerzielle Zwecke.  
Kommerzielle Nutzung ist nur nach Rücksprache mit dem Autor gestattet.