#!/usr/bin/env python3
"""Extend static-profile-data.json with additional countries.

Each entry gets: displayName, 1 headquarters address (capital),
2-3 contacts (gov site / legal portal / parliament), and 1 generic desk.
"""
import json
from pathlib import Path

EXT = {
    # Tier-2: G20/OECD + regional powers + representative mid-income
    "are": ("Government of the United Arab Emirates", "Abu Dhabi", "AE",
            [("https://u.ae/", "u.ae citizen portal"), ("https://www.mofa.gov.ae/", "MoFA")], None),
    "qat": ("State of Qatar", "Doha", "QA",
            [("https://www.gco.gov.qa/", "Government Comms"), ("https://www.hukoomi.gov.qa/", "Hukoomi citizen portal")], None),
    "kwt": ("Government of Kuwait", "Kuwait City", "KW",
            [("https://www.e.gov.kw/", "e.gov.kw"), ("https://www.da.gov.kw/", "Audit Bureau")], None),
    "omn": ("Sultanate of Oman", "Muscat", "OM",
            [("https://www.oman.om/", "oman.om"), ("https://www.mol.gov.om/", "Ministry of Legal")], None),
    "bhr": ("Kingdom of Bahrain", "Manama", "BH",
            [("https://www.bahrain.bh/", "bahrain.bh"), ("https://www.legalaffairs.gov.bh/", "Legal Affairs")], None),
    "irn": ("Government of the Islamic Republic of Iran", "Tehran", "IR",
            [("https://president.ir/", "President"), ("https://www.mfa.ir/", "MoFA")], None),
    "lbn": ("Republic of Lebanon", "Beirut", "LB",
            [("https://www.presidency.gov.lb/", "Presidency"), ("http://www.pcm.gov.lb/", "Council of Ministers")], None),
    "jor": ("Hashemite Kingdom of Jordan", "Amman", "JO",
            [("https://www.jordan.gov.jo/", "jordan.gov.jo"), ("https://www.pm.gov.jo/", "PM Office")], None),
    "hun": ("Government of Hungary", "Budapest", "HU",
            [("https://kormany.hu/", "kormany.hu"), ("https://njt.hu/", "National Legislation")], None),
    "cze": ("Government of the Czech Republic", "Prague", "CZ",
            [("https://www.vlada.cz/", "vlada.cz"), ("https://www.zakonyprolidi.cz/", "Legal database")], None),
    "svk": ("Government of the Slovak Republic", "Bratislava", "SK",
            [("https://www.vlada.gov.sk/", "vlada.gov.sk"), ("https://www.slov-lex.sk/", "Slov-Lex")], None),
    "ukr": ("Government of Ukraine", "Kyiv", "UA",
            [("https://www.kmu.gov.ua/", "kmu.gov.ua"), ("https://zakon.rada.gov.ua/", "Legal database")], None),
    "rou": ("Government of Romania", "Bucharest", "RO",
            [("https://gov.ro/", "gov.ro"), ("https://www.cdep.ro/", "Chamber of Deputies")], None),
    "hrv": ("Government of the Republic of Croatia", "Zagreb", "HR",
            [("https://vlada.gov.hr/", "vlada.gov.hr"), ("https://narodne-novine.nn.hr/", "Official Gazette")], None),
    "srb": ("Government of the Republic of Serbia", "Belgrade", "RS",
            [("https://www.srbija.gov.rs/", "srbija.gov.rs"), ("http://www.parlament.gov.rs/", "Parliament")], None),
    "blr": ("Government of the Republic of Belarus", "Minsk", "BY",
            [("https://www.government.by/", "government.by"), ("https://pravo.by/", "Legal portal")], None),
    "kaz": ("Government of the Republic of Kazakhstan", "Astana", "KZ",
            [("https://www.gov.kz/", "gov.kz"), ("https://adilet.zan.kz/", "Adilet legal DB")], None),
    "uzb": ("Government of the Republic of Uzbekistan", "Tashkent", "UZ",
            [("https://www.gov.uz/", "gov.uz"), ("https://lex.uz/", "LexUz legal DB")], None),
    "pak": ("Government of Pakistan", "Islamabad", "PK",
            [("https://www.pakistan.gov.pk/", "pakistan.gov.pk"), ("https://na.gov.pk/", "National Assembly")], None),
    "bgd": ("Government of Bangladesh", "Dhaka", "BD",
            [("https://bangladesh.gov.bd/", "bangladesh.gov.bd"), ("http://bdlaws.minlaw.gov.bd/", "Laws of Bangladesh")],
            [("bangladesh.rti", "RTI Application", "RTI Act 2009", "Each public authority")]),
    "lka": ("Government of Sri Lanka", "Colombo", "LK",
            [("https://www.gov.lk/", "gov.lk"), ("https://www.parliament.lk/", "Parliament")],
            [("srilanka.rti", "Right to Information", "RTI Act 2016", "Each public authority")]),
    "npl": ("Government of Nepal", "Kathmandu", "NP",
            [("https://www.nepal.gov.np/", "nepal.gov.np"), ("http://www.lawcommission.gov.np/", "Law Commission")], None),
    "mmr": ("Government of Myanmar", "Naypyidaw", "MM",
            [("https://www.mnpt.gov.mm/", "Government"), ("https://www.president-office.gov.mm/", "President")], None),
    "khm": ("Royal Government of Cambodia", "Phnom Penh", "KH",
            [("https://www.cambodia.gov.kh/", "cambodia.gov.kh"), ("http://pressocm.gov.kh/", "Press OCM")], None),
    "col": ("Gobierno de Colombia", "Bogota", "CO",
            [("https://www.presidencia.gov.co/", "Presidencia")], None),  # updated existing
    "ven": ("Gobierno de Venezuela", "Caracas", "VE",
            [("http://www.gobiernoenlinea.ve/", "Gobierno en Linea"), ("http://www.mppre.gob.ve/", "MPPRE")], None),
    "ecu": ("Gobierno de Ecuador", "Quito", "EC",
            [("https://www.gob.ec/", "gob.ec"), ("https://www.asambleanacional.gob.ec/", "Asamblea Nacional")], None),
    "bol": ("Gobierno de Bolivia", "La Paz", "BO",
            [("https://www.gob.bo/", "gob.bo"), ("https://www.senado.bo/", "Senado")], None),
    "pry": ("Gobierno de Paraguay", "Asuncion", "PY",
            [("https://www.presidencia.gov.py/", "Presidencia"), ("https://www.bacn.gov.py/", "Legislative archive")], None),
    "ury": ("Gobierno del Uruguay", "Montevideo", "UY",
            [("https://www.gub.uy/", "gub.uy"), ("https://www.impo.com.uy/", "IMPO legal DB")], None),
    "cri": ("Gobierno de Costa Rica", "San Jose", "CR",
            [("https://www.presidencia.go.cr/", "Presidencia"), ("http://www.pgrweb.go.cr/", "Legal system")], None),
    "pan": ("Gobierno de Panama", "Panama City", "PA",
            [("https://www.presidencia.gob.pa/", "Presidencia"), ("https://www.organojudicial.gob.pa/", "Judicial")], None),
    "gtm": ("Gobierno de Guatemala", "Guatemala City", "GT",
            [("https://www.guatemala.gob.gt/", "guatemala.gob.gt"), ("https://www.congreso.gob.gt/", "Congreso")], None),
    "cub": ("Gobierno de Cuba", "Havana", "CU",
            [("https://www.gob.cu/", "gob.cu"), ("https://www.presidencia.gob.cu/", "Presidencia")], None),
    "dom": ("Gobierno de Republica Dominicana", "Santo Domingo", "DO",
            [("https://www.presidencia.gob.do/", "Presidencia"), ("https://transparencia.gob.do/", "Transparency portal")], None),
    "jam": ("Government of Jamaica", "Kingston", "JM",
            [("https://opm.gov.jm/", "Office of PM"), ("https://japarliament.gov.jm/", "Parliament")], None),
    "tto": ("Government of Trinidad and Tobago", "Port of Spain", "TT",
            [("https://www.opm.gov.tt/", "Office of PM"), ("https://www.ttparliament.org/", "Parliament")], None),
    "eth": ("Federal Democratic Republic of Ethiopia", "Addis Ababa", "ET",
            [("https://www.pmo.gov.et/", "Office of PM"), ("https://www.fdrelaws.gov.et/", "Legal DB")], None),
    "tza": ("United Republic of Tanzania", "Dodoma", "TZ",
            [("https://www.tanzania.go.tz/", "tanzania.go.tz"), ("https://www.parliament.go.tz/", "Parliament")], None),
    "uga": ("Government of Uganda", "Kampala", "UG",
            [("https://www.gou.go.ug/", "gou.go.ug"), ("https://www.parliament.go.ug/", "Parliament")], None),
    "rwa": ("Government of the Republic of Rwanda", "Kigali", "RW",
            [("https://www.gov.rw/", "gov.rw"), ("https://www.minijust.gov.rw/", "Ministry of Justice")], None),
    "sen": ("Gouvernement du Senegal", "Dakar", "SN",
            [("https://www.sec.gouv.sn/", "Secretariat"), ("https://www.gouv.sn/", "gouv.sn")], None),
    "civ": ("Gouvernement de Cote d'Ivoire", "Yamoussoukro", "CI",
            [("https://www.gouv.ci/", "gouv.ci"), ("https://www.presidence.ci/", "Presidence")], None),
    "gha": ("Government of Ghana", "Accra", "GH",
            [("https://www.ghana.gov.gh/", "ghana.gov.gh"), ("https://www.parliament.gh/", "Parliament")], None),
    "cmr": ("Gouvernement du Cameroun", "Yaounde", "CM",
            [("https://www.spm.gov.cm/", "Services du PM"), ("https://www.prc.cm/", "Presidence")], None),
    "cod": ("Gouvernement de la RDC", "Kinshasa", "CD",
            [("https://www.primature.cd/", "Primature"), ("https://www.presidence.cd/", "Presidence")], None),
    "ago": ("Governo de Angola", "Luanda", "AO",
            [("https://www.governo.gov.ao/", "governo.gov.ao"), ("https://www.parlamento.ao/", "Parliament")], None),
    "moz": ("Governo de Mocambique", "Maputo", "MZ",
            [("https://www.portaldogoverno.gov.mz/", "Governo portal"), ("https://www.parlamento.mz/", "Parliament")], None),
    "zmb": ("Government of Zambia", "Lusaka", "ZM",
            [("https://www.zambia.gov.zm/", "zambia.gov.zm"), ("https://www.parliament.gov.zm/", "Parliament")], None),
    "zwe": ("Government of Zimbabwe", "Harare", "ZW",
            [("http://www.zim.gov.zw/", "zim.gov.zw"), ("http://www.parlzim.gov.zw/", "Parliament")], None),
    "mdg": ("Gouvernement de Madagascar", "Antananarivo", "MG",
            [("https://www.presidence.gov.mg/", "Presidence"), ("https://www.primature.gov.mg/", "Primature")], None),
    "tun": ("Gouvernement de Tunisie", "Tunis", "TN",
            [("https://www.finances.gov.tn/", "Ministry of Finance"), ("https://www.legislation.tn/", "Legal DB")], None),
    "dza": ("Gouvernement d'Algerie", "Algiers", "DZ",
            [("https://www.premier-ministre.gov.dz/", "Premier Ministre"), ("https://www.joradp.dz/", "Official Journal")], None),
}

def build(entry):
    name, capital, country, contacts, extra_desks = entry
    addresses = [{"kind": "headquarters", "label": f"Capital: {capital}", "addressLocality": capital, "country": country}]
    contacts_list = [{"kind": "website" if i == 0 else "portal", "uri": uri, "label": label} for i, (uri, label) in enumerate(contacts)]
    desks = []
    if extra_desks:
        for dk in extra_desks:
            desks.append({"kind": dk[0], "label": dk[1], "basis": dk[2], "authority": dk[3] if len(dk) > 3 else ""})
    return {"displayName": name, "addresses": addresses, "contacts": contacts_list, "desks": desks}

def main():
    root = Path(__file__).parent
    data = json.loads((root / "static-profile-data.json").read_text())
    before = len(data)
    added = []
    for iso3, entry in EXT.items():
        if iso3 in data:
            continue  # don't overwrite existing
        data[iso3] = build(entry)
        added.append(iso3)
    (root / "static-profile-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"added {len(added)} countries: {added}")
    print(f"total: {before} -> {len(data)}")

if __name__ == "__main__":
    main()
