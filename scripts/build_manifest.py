"""Reproducible source registry. Manifest entries are candidates, not implied authority."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sources=[]
def add(id,title,url,category,authority='guidance',jurisdiction='india',market='treaties',publisher='',**extra):
    sources.append(dict(id=id,title=title,url=url,category=category,authority=authority,jurisdiction=jurisdiction,
        market=market,publisher=publisher or ('IP India' if jurisdiction=='india' else 'WIPO'),language='en',access=extra.pop('access','public'),**extra))

local=[
 ('patents-act','patent_act_1970.pdf','Patents Act, 1970','patents','legislation','Supplied compilation; amendment completeness must be checked.'),
 ('patents-manual','manual of patent office.pdf','Manual of Patent Office Practice and Procedure','patents','guidance','Practice guidance; subsequent rules prevail.'),
 ('ayush-guidelines','guidelines_ayush related inventions.pdf','Guidelines for Examination of Ayush Related Inventions, 2025','patents','guidance','2025 guideline verified by visual inspection of supplied cover. Text extraction has spaced glyphs.'),
 ('pharma-guidelines','guidelines-pharma.pdf','Pharmaceutical Patent Examination Guidelines, 2014','patents','guidance','Historical guidance; assess amendments and later guidance.'),
 ('tk-patents','guidelines for processing patent application.pdf','Guidelines: Traditional Knowledge and Biological Material','traditional_knowledge','guidance','Useful TK and biological material context; verify current ABS provisions.'),
 ('patent-examination','guideline-search&examination.pdf','Patent Search and Examination Guidelines, 2015','patents','guidance','Practice reference; not a current consolidated rulebook.'),
 ('gi-act','geog_indiciations 1999.pdf','Geographical Indications Act, 1999','gi','legislation','Supplied Gazette; verify amendments.'),
 ('gi-rules','geo_indication_rules_2002.pdf','Geographical Indications Rules, 2002','gi','legislation','Base rules; read with subsequent amendments.'),
 ('gi-rules-2025','geo_indication_rules_2025.pdf','Geographical Indications Amendment Rules, 2025','gi','legislation','Gazette dated 3 November 2025, G.S.R. 812(E).'),
 ('gi-manual','geo_indi_practice_manual.pdf','GI Practice and Procedure Manual, 2011','gi','guidance','Historical procedural guidance.'),
 ('gi-logo-draft','geo_indi_guidelines.pdf','Draft GI and GI Logo Guidelines, October 2025','gi','draft','DRAFT: excluded from substantive answer context.'),
 ('trademark-act','trades_act_1999.pdf','Trade Marks Act, 1999 (Hindi)','trademarks','legislation','Hindi supplied text; extraction and amendment verification required.'),
 ('trademark-rules','trades_rules_2017.pdf','Trade Marks Rules, 2017','trademarks','legislation','Bilingual Gazette; some glyph extraction is damaged.'),
 ('trademark-notice','draftmanual_trademark.pdf','Public notice inviting comments on draft trade mark manual, 2015','trademarks','notice','One-page scanned consultation notice, not the manual. Excluded.'),
 ('design-rules','design rules_2001.pdf','Designs Rules, 2001','designs','legislation','Mixed scanned/text pages require selective OCR; verify amendments.'),
 ('design-manual','designmanuak.pdf','Manual of Designs Practice and Procedure','designs','guidance','Office guidance; verify against current statute and rules.'),
 ('patent-form1','form1-appl for grant of patent.pdf','Patent Form 1: Application for Grant','forms','form','Form resource only. Verify latest official form before use.'),
 ('patent-form3','undertaking form.pdf','Patent Form 3: Section 8 Statement and Undertaking','forms','form','Potential legacy form; current-rule verification required.'),
]
for id,file,title,cat,authority,notes in local:
    add(id,title,'https://ipindia.gov.in/',cat,authority,local_path='Resources/'+file,notes=notes,
        disposition='excluded' if authority in ('draft','notice') else 'pending')
    if id=='trademark-act': sources[-1]['language']='hi'

add('pct-texts','PCT Legal Texts','https://www.wipo.int/en/web/pct-system/texts/index','pct',jurisdiction='international',notes='Official index includes version-specific texts. Index is navigation; ingest linked instruments separately.')
add('pct-agreements','ISA and IPEA Agreements','https://www.wipo.int/en/web/pct-system/access/isa_ipea_agreements','pct',jurisdiction='international',notes='Authority-specific agreements and access links.')
add('wipo-indicators','World Intellectual Property Indicators 2025','https://www.wipo.int/edocs/pubdocs/en/wipo-pub-941-17-2025-en-world-intellectual-property-indicators-2025.pdf','statistics','statistics',jurisdiction='international',disposition='background',notes='Background statistics only; CC BY 4.0 attribution required. Not governing law.')
add('drugs-rules','Drugs and Cosmetics Act and Rules (through December 2016)','https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Ethics-Committee/Guideline-Document/Drugs_CosmeticsAct1940_Rules1945.pdf','classification','legislation',publisher='CDSCO',notes='Historical compilation through 31 December 2016. Current obligations need later amendments.')
add('aahara-kob','Ayurveda Aahara Kind of Business Order, 1 September 2025','https://www.fssai.gov.in/upload/advisories/2025/09/68b67efa6f47520250902103601289.pdf','aahara','order',publisher='FSSAI',publication_date='2025-09-01',notes='Official alternate URL found after supplied link failed.')
add('aahara-recipes','Ayurveda Aahara Category A Recipes, July 2025','https://fssai.gov.in/docs/food-law/advisory/68835f872eaf4Order%20dated%2025-07-2025%20enclosing%20Ayurveda%20Aahara.pdf','aahara','order',publisher='FSSAI',notes='Supplied URL; fetch must succeed before indexing.')
add('aahara-recipes-2','Ayurveda Aahara Recipes Part 2, June 2026','https://fssai.gov.in/docs/food-law/advisory/6a34f644db631Annexure%20No_part-2%20Compendium%20of%20Ayurveda%20Aahara%20recipes.pdf','aahara','order',publisher='FSSAI',notes='Supplied URL; official advisory listing identifies 19 June 2026 update.')
add('ppvfr-form','New and Extant Plant Variety Application','https://plantauthority.gov.in/sites/default/files/newextantvariety2013.pdf','plant_varieties','form',publisher='PPV&FR Authority',notes='Form, not the governing plant-variety statute.')
add('pharma-grants','Pharmaceutical Patents Granted: Historical List','https://ipindia.gov.in/uploads/dynamic-tables/1778068157_patentGranted_Pharma_2010-11_Jul2013%20(1).pdf','prior_art','registry',notes='Historical grants; individual records and current status require independent verification.')
add('abs-2025','India ABS Regulations 2025: National Record','https://absch.cbd.int/en/database/MSR/ABSCH-MSR-IN-283500/1','abs','guidance',publisher='CBD ABS Clearing-House / India',notes='Government-submitted record and source-document links. Dynamic text may require manual capture.')
add('nba-faq','National Biodiversity Authority FAQs','https://www.nbaindia.nic.in/index.php/about-us/faqs','abs','guidance',publisher='NBA',notes='Official explanatory guidance; governing provisions take precedence.')
add('nba-faq-1','NBA FAQs: IP and access obligations','https://www.nbaindia.nic.in/about-us/faqs?page=1','abs','guidance',publisher='NBA')
add('nba-faq-3','NBA FAQs: ABS regulations and commencement','https://www.nbaindia.nic.in/about-us/faqs?page=3','abs','guidance',publisher='NBA')
add('gratk','WIPO GRATK Treaty Summary','https://www.wipo.int/en/web/treaties/ip/gratk/summary_gratk','gratk',jurisdiction='international',notes='Summary; do not equate adoption with entry into force or applicability to a particular state.')
add('gratk-text','WIPO GRATK Treaty Text','https://www.wipo.int/wipolex/en/text/593055','gratk','treaty',jurisdiction='international')
add('cbd','Convention on Biological Diversity: Text','https://www.cbd.int/convention/text','cbd','treaty',jurisdiction='international',publisher='CBD Secretariat')
add('nagoya','Nagoya Protocol: Text and Annex','https://www.cbd.int/abs/text','nagoya','treaty',jurisdiction='international',publisher='CBD Secretariat')
add('trips','TRIPS Agreement: Legal Text','https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm','trips','treaty',jurisdiction='international',publisher='WTO')
add('madrid','Madrid System','https://www.wipo.int/en/web/madrid-system','madrid',jurisdiction='international',notes='Official navigation and system overview; eligibility is country-specific.')
add('hague','Hague System','https://www.wipo.int/en/web/hague-system','hague',jurisdiction='international',notes='Official navigation; membership must be checked for applicant and designated markets.')
add('budapest','Budapest Treaty System','https://www.wipo.int/en/web/budapest-system','budapest',jurisdiction='international')
add('us-botanical','Botanical Drug Development Guidance for Industry','https://www.fda.gov/files/drugs/published/Botanical-Drug-Development--Guidance-for-Industry.pdf','market_access','guidance',jurisdiction='international',market='us',publisher='US FDA',notes='Guidance document; distinguish enforceable regulations from recommendations.')
add('us-supplements','Dietary Supplements: Information for Industry','https://www.fda.gov/food/dietary-supplements/information-industry-dietary-supplements','market_access',jurisdiction='international',market='us',publisher='US FDA')
add('eu-herbal','Herbal Medicinal Products: EU Framework','https://www.ema.europa.eu/en/human-regulatory-overview/herbal-medicinal-products','market_access',jurisdiction='international',market='eu',publisher='EMA',notes='EU common framework; national competent-authority requirements need country selection.')
add('uk-thr','Apply for a Traditional Herbal Registration','https://www.gov.uk/guidance/apply-for-a-traditional-herbal-registration-thr','market_access',jurisdiction='international',market='uk',publisher='MHRA / GOV.UK')
add('dpdp-rules','Digital Personal Data Protection Rules, 2025','https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf','privacy','legislation',publisher='MeitY',notes='Read with commencement notifications. No blanket compliance certification implied.')
add('tkdl','Traditional Knowledge Digital Library','https://www.tkdl.res.in/','traditional_knowledge',publisher='CSIR TKDL',disposition='pointer',access='restricted',notes='Public information and lawful access pointer. No automated restricted-database access.')
add('pcimh','Pharmacopoeia Commission for Indian Medicine and Homoeopathy','https://pcimh.gov.in/','pharmacopoeia',publisher='PCIM&H',disposition='pointer',notes='Standards source directory. Ingest individual publications only after checking rights and version.')
add('copyright','WIPO Copyright Overview','https://www.wipo.int/en/web/copyright','copyright',jurisdiction='international',notes='International overview; Indian statutory corpus remains a tracked gap until official Act acquired.')
add('trade-secrets','WIPO Trade Secrets','https://www.wipo.int/en/web/trade-secrets','trade_secrets',jurisdiction='international',notes='Overview; India-specific contractual and case-law guidance needs Indian authority.')

add('copyright-act','Copyright Act, 1957','https://www.indiacode.nic.in/indiacode/bitstream/123456789/1367/1/A195714.pdf','copyright','legislation',publisher='India Code',notes='Official compilation; amendment applicability review pending.')
add('designs-act','Designs Act, 2000','https://www.indiacode.nic.in/indiacode/bitstream/123456789/1917/1/A2000-16.pdf','designs','legislation',publisher='India Code')
add('ppvfr-act','Protection of Plant Varieties and Farmers Rights Act, 2001','https://plantauthority.gov.in/sites/default/files/ppvfract2001.pdf','plant_varieties','legislation',publisher='India Code')
add('biodiversity-act','Biological Diversity Act, 2002 (amended compilation)','https://www.indiacode.nic.in/bitstream/123456789/2046/4/a2003-18.pdf','abs','legislation',publisher='India Code',notes='Includes 2023 amendments; applicability and commencement require review.')
add('biodiversity-rules','Biological Diversity Rules, 2024','https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1010_11082025024835.pdf','abs','legislation',publisher='MoEFCC / PARIVESH',notes='Official Gazette copy. Verify later amendments before advice.')
add('abs-regulations','Biological Diversity ABS Regulations, 2025','https://upload.indiacode.nic.in/showfile?actid=AC_CEN_16_18_000010_200318_1517807327125&filename=abs_regulations_2025_%285%29-1.pdf&type=regulation','abs','legislation',publisher='India Code / NBA',notes='Official regulation text, distinct from the dynamic CBD national record.')
add('aahara-regulations','Food Safety and Standards (Ayurveda Aahara) Regulations, 2022','https://www.fssai.gov.in/upload/notifications/2022/05/62789a20b54bdGazette_Notification_Ayurveda_Aahara_09_05_2022.pdf','aahara','legislation',publisher='FSSAI',notes='Base Gazette; subsequent orders are separate source versions.')
add('patent-rules-index','Patent Rules and Amendments: official index','https://ipindia.gov.in/resource/patents-resources-rules','patents','guidance',publisher='IP India',notes='Links to rules consolidated through 15 March 2024 and second amendment 16 March 2024. Draft entries must not support answers.')


add('patent-rules-2024','Patents Amendment Rules, 15 March 2024','https://ipindia.gov.in/storage/uploads/docs-operator/17e7b633-4b6f-4737-9408-8c8fe72c9cfc.pdf','patents','legislation',publisher='IP India',publication_date='2024-03-15',notes='Gazette linked by official rules index, accessed September 2026.')
add('patent-rules-2024-2','Patents Second Amendment Rules, 16 March 2024','https://ipindia.gov.in/storage/uploads/docs-operator/33524c6c-73dd-4fe0-bbd7-43c8f187413e.pdf','patents','legislation',publisher='IP India',publication_date='2024-03-16')
add('pct-treaty','Patent Cooperation Treaty text','https://www.wipo.int/documents/d/pct-system/docs-en-texts-pct.pdf','pct','treaty',jurisdiction='international',notes='Treaty text linked by official PCT legal texts index; separate from implementing regulations.')
add('pct-regulations-2026','PCT Regulations effective January 2026','https://www.wipo.int/documents/d/pct-system/docs-en-texts-pct-regs2026.pdf','pct','treaty',jurisdiction='international',effective_from='2026-01-01',notes='Version-specific official regulations; verify effective-date cover.')

catalog={'schema_version':1,'created':'2026-09-06','review_policy':'Ingestion never approves law. Source references require curator approval for generated answers.','sources':sources,
 'supplied_url_replacements':[{'original':'https://fssai.gov.in/docs/food-law/advisory/68b685259cb03Order%20dated01stSeptember2025-Introduction%20of%20new%20KoB-Ayurveda%20aahara.pdf','replacement_id':'aahara-kob','reason':'Original URL failed during planning; official alternate discovered.'}]}
(ROOT/'corpus').mkdir(exist_ok=True)
(ROOT/'corpus'/'manifest.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Wrote {len(sources)} source entries')
