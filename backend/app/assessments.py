"""Versioned triage: provisional routes, never automatic regulatory approvals."""
from .retrieval import retrieve, citation
from .assistant import DISCLAIMERS

RULE_VERSION='2026.09-pilot.2'
def q(id,en,hi,mr,options):
    return {'id':id,'labels':{'en':en,'hi':hi,'mr':mr},'options':[{'value':v,'labels':{'en':a,'hi':b,'mr':c}} for v,a,b,c in options]}
YESNO=[('yes','Yes','हाँ','होय'),('no','No','नहीं','नाही'),('unknown','Not sure','निश्चित नहीं','खात्री नाही')]
FORM={
 'use':q('use','What will the product be used or advertised for?','उत्पाद का उपयोग या विज्ञापन किस लिए होगा?','उत्पादनाचा वापर किंवा जाहिरात कशासाठी असेल?',[
    ('therapeutic','Treating or preventing disease','रोग का उपचार या रोकथाम','रोगावर उपचार किंवा प्रतिबंध'),('nutrition','Food or nutritional support','भोजन या पोषण','अन्न किंवा पोषण'),('cosmetic','Cleansing or appearance','सफाई या सौंदर्य','स्वच्छता किंवा सौंदर्य'),('unknown','Not sure / mixed claims','निश्चित नहीं / मिश्रित दावे','खात्री नाही / मिश्र दावे')]),
 'reference':q('reference','Is the formula described in an authoritative AYUSH or Schedule text (e.g., Ayurvedic Formulary of India, Siddha Formulary, Unani Pharmacopoeia, or texts listed in First Schedule of D&C Act)?','क्या सूत्र किसी प्रामाणिक AYUSH या अनुसूची ग्रंथ (जैसे भारतीय आयुर्वेदिक फार्मूलरी, सिद्ध फार्मूलरी, यूनानी फार्माकोपिया, या D&C अधिनियम की प्रथम अनुसूची में सूचीबद्ध ग्रंथ) में वर्णित है?','सूत्र कोणत्याही अधिकृत AYUSH किंवा अनुसूची ग्रंथामध्ये (जसे भारतीय आयुर्वेदिक फॉर्म्युलरी, सिद्ध फॉर्म्युलरी, युनानी फार्माकोपिया, किंवा D&C कायद्याच्या पहिल्या अनुसूचीत सूचीबद्ध ग्रंथ) वर्णिले आहे का?',YESNO),
 'exact':q('exact','Are the ingredients, proportions, and preparation method (including Shodhana/purification, Marana/calcination, and Bhavana/levigation steps) unchanged from that authoritative text?','क्या सामग्री, अनुपात और तैयारी विधि (शोधन, मारण और भावना सहित) उसी प्रामाणिक ग्रंथ के अनुसार समान हैं?','घटक, प्रमाण आणि तयार करण्याची पद्धत (शोधन, मारण आणि भावना यांसह) त्या अधिकृत ग्रंथाप्रमाणेच आहेत का?',YESNO),
 'ingredients':q('ingredients','Are all medicinal ingredients either named in the authoritative text or disclosed as non-textual, non-classical materials? (Include Rasa-Shastra mineral/metal preparations if applicable)','क्या सभी औषधीय घटक (रस शास्त्र की खनिज/धातु तैयारियों सहित) प्रामाणिक ग्रंथ में वर्णित हैं या गैर-शास्त्रीय सामग्री के रूप में स्पष्ट रूप से वर्णित हैं?','सर्व औषधी घटक (रस शास्त्राच्या खनिज/धातू तयारी सहित) अधिकृत ग्रंथांमध्ये नमूद केलेले आहेत की अशास्त्रीय सामग्री म्हणून स्पष्टपणे नमूद केले आहेत का?',YESNO),
 'phytopharma':q('phytopharma','Is this a standardised plant fraction being developed through a phytopharmaceutical route (purified extract with defined marker compounds) rather than a classical text-based preparation?','क्या यह एक मानकीकृत पौध-भिन्न अंश है जो शास्त्रीय ग्रंथ-आधारित तैयारी के बजाय फाइटोफार्मास्यूटिकल मार्ग (शुद्ध अर्क और परिभाषित मार्कर यौगिकों) पर विकसित किया जा रहा है?','हे प्रमाणित वनस्पती अंश (शुद्ध अर्क आणि परिभाषित मार्कर संयुगे) आहे की शास्त्रीय ग्रंथ-आधारित तयारीऐवजी फायटोफार्मास्युटिकल मार्गाने विकसित केले जात आहे?',YESNO),
 'aahara':q('aahara','Does the food follow an Ayurveda-Aahara recipe (FSSAI notification-based), authorised food-category basis, or a separate FSSAI Health Supplement / Nutraceutical route?','क्या भोजन आयुर्वेद-आहार विधि (FSSAI अधिसूचना आधारित), अधिकृत खाद्य श्रेणी या अलग FSSAI स्वास्थ्य पूरक/न्यूट्रास्यूटिकल मार्ग का अनुसरण करता है?','अन्न आयुर्वेद-आहार पद्धत (FSSAI अधिसूचना आधारित), अधिकृत खाद्य श्रेणी किंवा वेगळा FSSAI आरोग्य पूरक/न्यूट्रास्युटिकल मार्ग अनुसरण करते आहे का?',YESNO),
 'route':q('route','How will it be administered and marketed?','इसे कैसे प्रशासित और विपणन किया जाएगा?','ते कसे प्रशासनित आणि विपणन केले जाईल?',[
    ('oral','Oral','मुख से','तोंडावाटे'),('external','External','बाहरी','बाह्य'),('other','Other / not established','अन्य / अस्पष्ट','इतर / अस्पष्ट')]),
 'origin':q('origin','What biological materials are involved and what is the dominant source?','कौन सी जैविक सामग्री शामिल है और मुख्य स्रोत क्या है?','कोणती जैविक सामग्री समाविष्ट आहे आणि मुख्य स्रोत काय आहे?',[
    ('plant','Plant','पौधे','वनस्पती'),('microbial','Microbial','सूक्ष्मजीव','सूक्ष्मजीव'),('animal','Animal','पशु','प्राणी'),('mixed','Mixed / uncertain','मिश्रित / अनिश्चित','मिश्र / अनिश्चित')]),
 'claims':q('claims','What therapeutic, nutrition, cosmetic, or disease-related claims are intended?','कौन से चिकित्सीय, पोषण, सौंदर्य या रोग-संबंधित दावे प्रस्तावित हैं?','कोणते चिकित्सीय, पोषण, सौंदर्य किंवा रोग-संबंधित दावा प्रस्तावित आहेत?',[
    ('classic','Classical AYUSH / traditional use only','केवल शास्त्रीय AYUSH / पारंपरिक उपयोग','केवळ शास्त्रीय AYUSH / पारंपरिक उपयोग'),('health','Disease-prevention or therapeutic efficacy claims','रोग-रोकथाम या चिकित्सीय प्रभाव के दावे','रोग-प्रतिबंध किंवा चिकित्सीय प्रभावाचे दावा'),('general','General wellness or daily-use promotion','सामान्य स्वास्थ्य या दैनिक उपयोग संवर्धन','सामान्य आरोग्य किंवा दैनंदिन वापर संवर्धन'),('unknown','Not clear or mixed','स्पष्ट नहीं / मिश्रित','स्पष्ट नाही / मिश्र')]),
 # ── New granular questions ─────────────────────────────────────────────────
 'dosage_form':q('dosage_form',
    'What is the specific dosage form of the product? (Select the closest match per CDSCO/AYUSH classification)',
    'उत्पाद का विशिष्ट खुराक रूप क्या है? (CDSCO/AYUSH वर्गीकरण के अनुसार निकटतम विकल्प चुनें)',
    'उत्पादनाचे विशिष्ट डोस स्वरूप काय आहे? (CDSCO/AYUSH वर्गीकरणानुसार जवळचा पर्याय निवडा)',[
    ('classical_oral','Classical oral form (Churna, Vati, Kwatha, Asava/Arishta, Avaleha, Ghrita, Taila for internal use)',
     'शास्त्रीय मौखिक रूप (चूर्ण, वटी, क्वाथ, असव/अरिष्ट, अवलेह, घृत, आंतरिक उपयोग हेतु तैल)',
     'शास्त्रीय तोंडी स्वरूप (चूर्ण, वटी, क्वाथ, असव/अरिष्ट, अवलेह, घृत, अंतर्गत वापरासाठी तैल)'),
    ('modern_oral','Modern oral form (Tablet, Capsule, Syrup, Soft gel, effervescent)',
     'आधुनिक मौखिक रूप (टैबलेट, कैप्सूल, सिरप, सॉफ्ट जेल, इफ़रवेसेंट)',
     'आधुनिक तोंडी स्वरूप (टॅबलेट, कॅप्सूल, सिरप, सॉफ्ट जेल, इफरव्हेसंट)'),
    ('topical','Topical / External (Lepa, Taila for external use, cream, ointment, balm)',
     'बाहरी उपयोग (लेप, बाहरी तैल, क्रीम, मलहम, बाम)',
     'बाह्य वापर (लेप, बाह्य तैल, क्रीम, मलम, बाम)'),
    ('rasa_shastra','Rasa-Shastra / mineral-metallic preparation (Bhasma, Pishti, Mandura, Sindura)',
     'रस शास्त्र / खनिज-धातु तैयारी (भस्म, पिष्टी, मंडूर, सिंदूर)',
     'रस शास्त्र / खनिज-धातू तयारी (भस्म, पिष्टी, मंडूर, सिंदूर)'),
    ('other_form','Other / novel delivery system',
     'अन्य / नवीन वितरण प्रणाली',
     'इतर / नवीन वितरण प्रणाली')]),
 'claims_detail':q('claims_detail',
    'Which specific claim category applies to this product under Indian regulatory definitions?',
    'भारतीय नियामक परिभाषाओं के अनुसार इस उत्पाद पर कौन सी विशिष्ट दावा श्रेणी लागू होती है?',
    'भारतीय नियामक व्याख्यांनुसार या उत्पादनावर कोणती विशिष्ट दावा श्रेणी लागू होते?',[
    ('schedule_k','Schedule K exemption claim — classical ASU drug with approved textual reference, no separate clinical trial required',
     'अनुसूची K छूट का दावा — अनुमोदित ग्रंथ संदर्भ वाली शास्त्रीय ASU औषधि, अलग नैदानिक परीक्षण आवश्यक नहीं',
     'अनुसूची K सूट दावा — मंजूर ग्रंथ संदर्भासह शास्त्रीय ASU औषध, स्वतंत्र नैदानिक चाचणी आवश्यक नाही'),
    ('new_drug_claim','New drug / new indication claim — requires CDSCO new-drug approval pathway with safety and efficacy data',
     'नई औषधि / नए संकेत का दावा — सुरक्षा और प्रभावकारिता डेटा के साथ CDSCO नई-औषधि अनुमोदन मार्ग आवश्यक',
     'नवीन औषध / नवीन संकेत दावा — सुरक्षा आणि परिणामकारकता डेटासह CDSCO नवीन-औषध मंजुरी मार्ग आवश्यक'),
    ('wellness_claim','General wellness / structure-function claim — no disease-specific therapeutic promise',
     'सामान्य स्वास्थ्य / संरचना-कार्य दावा — कोई रोग-विशिष्ट चिकित्सीय वादा नहीं',
     'सामान्य आरोग्य / संरचना-कार्य दावा — रोग-विशिष्ट चिकित्सीय वचन नाही'),
    ('cosmetic_claim','Cosmetic / beauty claim — regulated under Cosmetic Rules, not D&C Act drug provisions',
     'सौंदर्य प्रसाधन दावा — D&C अधिनियम के औषधि प्रावधानों के बजाय सौंदर्य प्रसाधन नियमों के अंतर्गत विनियमित',
     'सौंदर्यप्रसाधन दावा — D&C कायद्याच्या औषध तरतुदींऐवजी सौंदर्यप्रसाधन नियमांनुसार नियमित'),
    ('uncertain_claim','Claim category is unclear or mixed',
     'दावा श्रेणी अस्पष्ट या मिश्रित है',
     'दावा श्रेणी अस्पष्ट किंवा मिश्र आहे')]),
 'cross_border':q('cross_border',
    'Will this product be marketed or registered in any of the following international markets? (Select the primary target)',
    'क्या इस उत्पाद का विपणन या पंजीकरण निम्नलिखित अंतर्राष्ट्रीय बाजारों में से किसी में किया जाएगा? (प्राथमिक लक्ष्य चुनें)',
    'या उत्पादनाचे विपणन किंवा नोंदणी खालीलपैकी कोणत्याही आंतरराष्ट्रीय बाजारात केले जाईल का? (प्राथमिक लक्ष्य निवडा)',[
    ('india_only','India only — no international registration planned',
     'केवल भारत — कोई अंतर्राष्ट्रीय पंजीकरण योजना नहीं',
     'केवळ भारत — कोणतीही आंतरराष्ट्रीय नोंदणी योजना नाही'),
    ('us_fda','US market — FDA Botanical Drug Application (BDA) or Dietary Supplement (DSHEA) route',
     'अमेरिकी बाजार — FDA बॉटैनिकल ड्रग एप्लीकेशन (BDA) या डाइटरी सप्लीमेंट (DSHEA) मार्ग',
     'अमेरिकन बाजार — FDA बॉटॅनिकल ड्रग ॲप्लिकेशन (BDA) किंवा डायटरी सप्लिमेंट (DSHEA) मार्ग'),
    ('eu_ema','EU market — Traditional Herbal Medicinal Product Directive (THMPD) or full EMA marketing authorisation',
     'यूरोपीय बाजार — पारंपरिक हर्बल औषधि उत्पाद निर्देशिका (THMPD) या पूर्ण EMA विपणन प्राधिकरण',
     'युरोपीय बाजार — पारंपरिक हर्बल औषधी उत्पाद निर्देशिका (THMPD) किंवा पूर्ण EMA विपणन प्राधिकरण'),
    ('uk_thr','UK market — Traditional Herbal Registration (THR) under MHRA',
     'ब्रिटिश बाजार — MHRA के अंतर्गत पारंपरिक हर्बल पंजीकरण (THR)',
     'ब्रिटिश बाजार — MHRA अंतर्गत पारंपरिक हर्बल नोंदणी (THR)'),
    ('multiple_markets','Multiple international markets planned',
     'कई अंतर्राष्ट्रीय बाजारों की योजना',
     'अनेक आंतरराष्ट्रीय बाजारांची योजना')]),
 'gmp_compliance':q('gmp_compliance',
    'What is the current GMP (Good Manufacturing Practice) certification status of the manufacturing facility?',
    'विनिर्माण सुविधा की वर्तमान GMP (गुड मैन्युफैक्चरिंग प्रैक्टिस) प्रमाणन स्थिति क्या है?',
    'उत्पादन सुविधेची सध्याची GMP (गुड मॅन्युफॅक्चरिंग प्रॅक्टिस) प्रमाणन स्थिती काय आहे?',[
    ('schedule_t','Schedule T GMP (mandatory for ASU drugs in India)',
     'अनुसूची T GMP (भारत में ASU औषधियों के लिए अनिवार्य)',
     'अनुसूची T GMP (भारतातील ASU औषधांसाठी अनिवार्य)'),
    ('who_gmp','WHO-GMP certified',
     'WHO-GMP प्रमाणित',
     'WHO-GMP प्रमाणित'),
    ('eu_gmp','EU-GMP certified (required for THMPD route)',
     'EU-GMP प्रमाणित (THMPD मार्ग के लिए आवश्यक)',
     'EU-GMP प्रमाणित (THMPD मार्गासाठी आवश्यक)'),
    ('fda_cgmp','US FDA cGMP compliant (21 CFR Part 211 or 111)',
     'US FDA cGMP अनुपालन (21 CFR भाग 211 या 111)',
     'US FDA cGMP अनुपालन (21 CFR भाग 211 किंवा 111)'),
    ('none_gmp','No current GMP certification or status unknown',
     'कोई वर्तमान GMP प्रमाणन नहीं या स्थिति अज्ञात',
     'सध्या GMP प्रमाणन नाही किंवा स्थिती अज्ञात')]),
}
ABS={
 'origin':q('origin','Were biological resources or associated traditional knowledge accessed from India (including cultivated, wild-harvested, or community-held knowledge)?','क्या जैविक संसाधन या संबंधित पारंपरिक ज्ञान भारत से (खेती, जंगली संग्रह, या समुदाय-आधारित ज्ञान सहित) प्राप्त किया गया?','जैविक संसाधने किंवा संबंधित पारंपरिक ज्ञान भारतातून (लागवड, जंगली संग्रह, किंवा समुदाय-आधारित ज्ञान सहित) मिळवले आहे का?',YESNO),
 'entity':q('entity','Which description best fits the applicant?','आवेदक किस श्रेणी में है?','अर्जदार कोणत्या श्रेणीतील आहे?',[
    ('indian','Indian citizen / Indian-controlled entity','भारतीय नागरिक / भारतीय नियंत्रण','भारतीय नागरिक / भारतीय नियंत्रण'),('foreign','Foreign person / foreign-controlled entity','विदेशी व्यक्ति / विदेशी नियंत्रण','परदेशी व्यक्ती / परदेशी नियंत्रण'),('unknown','Control or residency unclear','नियंत्रण या निवास अस्पष्ट','नियंत्रण किंवा निवास अस्पष्ट')]),
 'purpose':q('purpose','What is the purpose of access?','प्राप्ति का उद्देश्य क्या है?','संसाधन मिळवण्याचा उद्देश काय?',[
    ('research','Research','अनुसंधान','संशोधन'),('commercial','Commercial use','व्यावसायिक उपयोग','व्यावसायिक वापर'),('both','Research and commercialisation','अनुसंधान और व्यवसाय','संशोधन आणि व्यवसाय')]),
 'transfer':q('transfer','Will research results or materials be transferred abroad?','क्या शोध परिणाम या सामग्री विदेश भेजी जाएगी?','संशोधन निष्कर्ष किंवा सामग्री परदेशात हस्तांतरित होईल का?',YESNO),
 'ip':q('ip','Is an IP application or commercialisation of IP planned?','क्या बौद्धिक संपदा आवेदन या उसका व्यवसायीकरण होगा?','बौद्धिक संपदा अर्ज किंवा व्यापारीकरण नियोजित आहे का?',YESNO),
 'cultivated':q('cultivated','Are resources cultivated, with documentary proof of origin (invoices, seed certificates, cultivation records)?','क्या संसाधन उगाए गए हैं और उत्पत्ति का प्रमाण (चालान, बीज प्रमाणपत्र, खेती के रिकॉर्ड) है?','संसाधने लागवडीतून मिळाली असून उत्पत्तीचा पुरावा (बीजक, बीज प्रमाणपत्र, लागवड नोंदी) आहे का?',YESNO),
 'tk':q('tk','Is community-associated traditional knowledge involved (codified in texts, oral traditions, or community practices)?','क्या समुदाय से संबंधित पारंपरिक ज्ञान (ग्रंथों, मौखिक परंपराओं, या सामुदायिक प्रथाओं में संहिताबद्ध) शामिल है?','समुदायाशी संबंधित पारंपरिक ज्ञान (ग्रंथ, मौखिक परंपरा, किंवा सामुदायिक प्रथा) वापरले आहे का?',YESNO),
 # ── New granular ABS questions ─────────────────────────────────────────────
 'nagoya_scope':q('nagoya_scope',
    'Has the applicant assessed whether the Nagoya Protocol country-of-origin obligations apply, particularly Articles 5 (benefit-sharing), 6 (access with PIC), and 15 (compliance with domestic ABS legislation)?',
    'क्या आवेदक ने मूल्यांकन किया है कि नागोया प्रोटोकॉल के मूल-देश दायित्व, विशेष रूप से अनुच्छेद 5 (लाभ-साझाकरण), 6 (PIC के साथ पहुँच), और 15 (घरेलू ABS कानून का अनुपालन), लागू होते हैं?',
    'अर्जदाराने नागोया प्रोटोकॉलच्या मूळ-देश जबाबदाऱ्या, विशेषतः अनुच्छेद 5 (लाभ-वाटप), 6 (PIC सह प्रवेश), आणि 15 (देशांतर्गत ABS कायद्याचे अनुपालन), लागू होतात का याचे मूल्यांकन केले आहे का?',YESNO),
 'benefit_sharing':q('benefit_sharing',
    'What is the current status of benefit-sharing arrangements with the provider country / community?',
    'प्रदाता देश / समुदाय के साथ लाभ-साझाकरण व्यवस्था की वर्तमान स्थिति क्या है?',
    'प्रदाता देश / समुदायासोबत लाभ-वाटप व्यवस्थेची सध्याची स्थिती काय आहे?',[
    ('none_bs','No benefit-sharing arrangement initiated',
     'कोई लाभ-साझाकरण व्यवस्था शुरू नहीं की गई',
     'कोणतीही लाभ-वाटप व्यवस्था सुरू केलेली नाही'),
    ('negotiating','Benefit-sharing terms under negotiation / MoU being drafted',
     'लाभ-साझाकरण शर्तों पर बातचीत / MoU तैयार हो रहा है',
     'लाभ-वाटप अटींवर वाटाघाटी / MoU तयार होत आहे'),
    ('signed','Mutually Agreed Terms (MAT) or benefit-sharing agreement signed',
     'पारस्परिक सहमत शर्तें (MAT) या लाभ-साझाकरण समझौता हस्ताक्षरित',
     'परस्पर मान्य अटी (MAT) किंवा लाभ-वाटप करार स्वाक्षरित'),
    ('exempt_bs','Believed exempt from benefit-sharing (provide documentary basis)',
     'लाभ-साझाकरण से छूट प्राप्त (दस्तावेज़ी आधार दें)',
     'लाभ-वाटपातून सूट (दस्तऐवजी आधार द्या)'),
    ('unknown_bs','Status unknown or not assessed',
     'स्थिति अज्ञात या मूल्यांकन नहीं किया गया',
     'स्थिती अज्ञात किंवा मूल्यांकन केले नाही')]),
 'prior_informed_consent':q('prior_informed_consent',
    'Has Prior Informed Consent (PIC) been obtained from the relevant local community, State Biodiversity Board, or National Biodiversity Authority as applicable?',
    'क्या संबंधित स्थानीय समुदाय, राज्य जैव विविधता बोर्ड, या राष्ट्रीय जैव विविधता प्राधिकरण से पूर्व सूचित सहमति (PIC) प्राप्त की गई है?',
    'संबंधित स्थानीय समुदाय, राज्य जैवविविधता मंडळ, किंवा राष्ट्रीय जैवविविधता प्राधिकरणाकडून पूर्व सूचित संमती (PIC) मिळवली आहे का?',[
    ('pic_obtained','Yes — PIC obtained with documentation',
     'हाँ — दस्तावेज़ीकरण के साथ PIC प्राप्त',
     'होय — दस्तऐवजीकरणासह PIC मिळवली'),
    ('pic_pending','PIC application filed, decision pending',
     'PIC आवेदन दायर, निर्णय लंबित',
     'PIC अर्ज दाखल, निर्णय प्रलंबित'),
    ('pic_not_initiated','PIC process not yet initiated',
     'PIC प्रक्रिया अभी शुरू नहीं हुई',
     'PIC प्रक्रिया अद्याप सुरू झालेली नाही'),
    ('pic_not_required','Believed not required (provide regulatory basis)',
     'आवश्यक नहीं माना जाता है (नियामक आधार दें)',
     'आवश्यक नाही असे मानले जाते (नियामक आधार द्या)'),
    ('unknown_pic','Not sure / status unknown',
     'निश्चित नहीं / स्थिति अज्ञात',
     'खात्री नाही / स्थिती अज्ञात')]),
}

RESULTS={
 'classical':('Classical ASU medicine route','शास्त्रीय आयुर्वेदिक औषधि मार्ग','शास्त्रीय आयुर्वेदिक औषध मार्ग','Ayurvedic drug authoritative books formula First Schedule'),
 'proprietary':('Patent-or-proprietary ASU medicine route','पेटेंट या प्रोप्राइटरी आयुर्वेदिक औषधि मार्ग','पेटंट किंवा प्रोप्रायटरी आयुर्वेदिक औषध मार्ग','patent proprietary medicine ingredients authoritative books'),
 'new_drug':('Potential non-classical / new-drug assessment','संभावित गैर-शास्त्रीय / नई औषधि मूल्यांकन','संभाव्य अशास्त्रीय / नवीन औषध मूल्यांकन','new drug safety effectiveness phytopharmaceutical'),
 'phytopharmaceutical':('Phytopharmaceutical route to investigate','फाइटोफार्मास्यूटिकल मार्ग की जाँच','फायटोफार्मास्युटिकल मार्गाचा विचार','phytopharmaceutical purified standardized fraction'),
 'aahara':('Ayurveda-Aahara route to investigate','आयुर्वेद आहार मार्ग की जाँच','आयुर्वेद आहार मार्गाचा विचार','Ayurveda Aahara food category'),
 'food':('Food / nutraceutical route to investigate','खाद्य / न्यूट्रास्यूटिकल मार्ग की जाँच','अन्न / न्यूट्रास्युटिकल मार्गाचा विचार','food nutritional supplement Ayurveda Aahara'),
 'cosmetic':('Cosmetic route to investigate','कॉस्मेटिक मार्ग की जाँच','सौंदर्यप्रसाधन मार्गाचा विचार','cosmetic cleansing beautifying appearance'),
 'uncertain':('Classification needs clarification','वर्गीकरण के लिए स्पष्टीकरण आवश्यक','वर्गीकरणासाठी स्पष्टीकरण आवश्यक','Ayurvedic medicine classification authoritative text'),
}

def validate_answers(answers,questions):
    for key,value in answers.items():
        if key not in questions or value not in {o['value'] for o in questions[key]['options']}:
            raise ValueError(f'Invalid answer for {key}')

def question_result(question,language,answers):
    return {'complete':False,'question':{'id':question['id'],'text':question['labels'][language],
        'options':[{'value':o['value'],'label':o['labels'][language]} for o in question['options']]},
        'answered':len(answers),'rule_version':RULE_VERSION}

def classify(db,answers,language='en'):
    validate_answers(answers,FORM)
    needed=['use']
    use=answers.get('use')
    if use=='therapeutic':
        needed+=['reference']
        if answers.get('reference')=='yes': needed+=['exact']
        if answers.get('reference')=='no' or answers.get('exact')=='no':
            needed+=['ingredients']
            if answers.get('ingredients')=='no': needed+=['phytopharma']
    elif use=='nutrition': needed+=['aahara']
    if use and use!='unknown': needed+=['route','origin']
    # ── New granular questions are asked after base classification ──────────
    if use in ('therapeutic','nutrition'):
        needed+=['dosage_form']
    if use=='therapeutic':
        needed+=['claims_detail']
    if use and use!='unknown':
        needed+=['cross_border']
    # GMP is asked when cross_border is answered and not india_only
    cross_border = answers.get('cross_border')
    if cross_border and cross_border != 'india_only':
        needed+=['gmp_compliance']
    # Also ask GMP for therapeutic products even if India-only
    if use=='therapeutic' and cross_border=='india_only':
        needed+=['gmp_compliance']
    for key in needed:
        if key not in answers: return question_result(FORM[key],language,answers)
    result='uncertain'
    if use=='cosmetic': result='cosmetic'
    elif use=='nutrition': result='aahara' if answers.get('aahara')=='yes' else 'food' if answers.get('aahara')=='no' else 'uncertain'
    elif use=='therapeutic':
        if answers.get('reference')=='yes' and answers.get('exact')=='yes': result='classical'
        elif answers.get('ingredients')=='yes': result='proprietary'
        elif answers.get('ingredients')=='no': result='phytopharmaceutical' if answers.get('phytopharma')=='yes' else 'new_drug' if answers.get('phytopharma')=='no' else 'uncertain'
    if answers.get('route')=='other': result='uncertain'
    info=RESULTS[result]
    rows,_=retrieve(db,info[3],'india',limit=3)
    labels={'en':0,'hi':1,'mr':2}

    # ── Build enriched posture with cross-border and GMP guidance ───────────
    posture = {
        'regulatory':'Confirm the route, intended claims, evidence requirements and licence with the competent authority.',
        'ip':'Regulatory classification does not establish patentability. Patent-or-proprietary is a regulatory term.',
        'traditional_knowledge':'Check authoritative texts and prior art. A search pointer is not a patentability opinion.',
        'abs':'Assess biological-resource access separately using the ABS helper.',
    }
    # Dosage form guidance
    dosage = answers.get('dosage_form','')
    if dosage == 'rasa_shastra':
        posture['dosage_form'] = (
            'Rasa-Shastra preparations (Bhasma, Pishti, etc.) require additional heavy-metal safety testing '
            'per CDSCO guidelines. Ensure compliance with permissible limits for lead, mercury, arsenic, and cadmium '
            'as specified in the Ayurvedic Pharmacopoeia of India (API).'
        )
    elif dosage == 'modern_oral':
        posture['dosage_form'] = (
            'Modern oral dosage forms (tablet, capsule, syrup) of ASU ingredients may trigger additional '
            'CDSCO scrutiny if the final form differs from classical texts. Verify whether the dosage form '
            'requires separate stability testing per Schedule T requirements.'
        )
    # Claims detail guidance
    claims_d = answers.get('claims_detail','')
    if claims_d == 'schedule_k':
        posture['claims_guidance'] = (
            'Schedule K exemption applies only if the drug is prepared exactly as described in authoritative texts '
            'listed in the First Schedule of the Drugs & Cosmetics Act. Any modification to ingredients, proportions, '
            'or manufacturing process may void this exemption and require a fresh licence application.'
        )
    elif claims_d == 'new_drug_claim':
        posture['claims_guidance'] = (
            'New drug claims require submission of safety and efficacy data to CDSCO. For ASU-origin new drugs, '
            'Rule 158B of D&C Rules applies. Phase I–III clinical trial data, or a well-documented history of '
            'traditional use with pharmacovigilance data, may be required depending on the claim specificity.'
        )
    elif claims_d == 'wellness_claim':
        posture['claims_guidance'] = (
            'General wellness claims must avoid any disease-specific therapeutic language per Drugs & Magic Remedies '
            '(Objectionable Advertisements) Act, 1954 and the ASCI code. Structure-function claims are permissible '
            'but must not imply treatment, cure, or prevention of any specific disease.'
        )
    # Cross-border guidance
    cb = answers.get('cross_border','india_only')
    if cb == 'us_fda':
        posture['cross_border'] = (
            'US FDA route: For therapeutic claims, pursue Botanical Drug Application (BDA) under 21 CFR Part 312/314. '
            'For wellness/supplement claims, the DSHEA (Dietary Supplement Health and Education Act) route applies. '
            'Requires NDI (New Dietary Ingredient) notification if the ingredient was not marketed before 15 Oct 1994. '
            'FDA cGMP compliance (21 CFR Part 111 for supplements, Part 211 for drugs) is mandatory.'
        )
    elif cb == 'eu_ema':
        posture['cross_border'] = (
            'EU route: For traditional herbal medicines, apply under Directive 2004/24/EC (THMPD) requiring 30 years '
            'of traditional use (15 years within EU). For novel formulations, full EMA marketing authorisation '
            'under Directive 2001/83/EC is required. EU-GMP certification and a Qualified Person (QP) are mandatory. '
            'Active substance master file (ASMF) documentation may be needed.'
        )
    elif cb == 'uk_thr':
        posture['cross_border'] = (
            'UK route: Post-Brexit, apply for Traditional Herbal Registration (THR) under MHRA. Requires evidence '
            'of 30 years of traditional use (15 years in UK/EU). Bibliographic evidence and expert report on safety '
            'and traditional use required. UK-specific GMP and qualified person requirements apply.'
        )
    elif cb == 'multiple_markets':
        posture['cross_border'] = (
            'Multi-market strategy requires separate regulatory dossiers for each jurisdiction. Consider ICH CTD '
            'format for harmonised submissions. GMP must meet the highest standard required across target markets. '
            'ABS/Nagoya compliance must be verified for each country-of-destination implementing legislation.'
        )
    # GMP guidance
    gmp = answers.get('gmp_compliance','')
    if gmp == 'none_gmp':
        posture['gmp_compliance'] = (
            'GMP certification is a mandatory prerequisite for obtaining a manufacturing licence. For ASU drugs in India, '
            'Schedule T GMP compliance is minimum. For export or international registration, upgrade to WHO-GMP, '
            'EU-GMP, or FDA cGMP as required by the target market.'
        )
    elif gmp == 'schedule_t' and cb in ('us_fda','eu_ema','uk_thr','multiple_markets'):
        posture['gmp_compliance'] = (
            'Schedule T GMP is sufficient for Indian market only. International markets require WHO-GMP (minimum), '
            'EU-GMP (for EU/UK markets), or FDA cGMP (for US market). Facility upgrade and re-certification '
            'will be needed before international regulatory submissions.'
        )

    limitations = [
        'Triage is based on user-supplied facts. It is not a licence determination.',
        'Review original formula, text reference, ingredients and current rules with a qualified reviewer.',
    ]
    if dosage == 'rasa_shastra':
        limitations.append(
            'Rasa-Shastra preparations may face additional import restrictions in some jurisdictions '
            'due to heavy-metal content concerns. Verify country-specific limits.'
        )
    if cb in ('us_fda','eu_ema','uk_thr','multiple_markets'):
        limitations.append(
            'Cross-border regulatory pathways have independent timelines, evidence requirements, and fee structures. '
            'This triage does not substitute for market-specific regulatory counsel.'
        )
    if gmp == 'none_gmp':
        limitations.append(
            'Manufacturing without GMP certification is a regulatory non-compliance risk. '
            'Obtain certification before applying for any product licence.'
        )

    return {'complete':True,'code':result,'title':info[labels[language]],'provisional':True,'rule_version':RULE_VERSION,
        'citations':[citation(r).model_dump() for r in rows],
        'missing_facts':[key for key,value in answers.items() if value=='unknown'],
        'posture':posture,
        'authority_to_consult':_classification_authority(result, cb),
        'limitations':limitations,
        'disclaimer':DISCLAIMERS[language]}


def _classification_authority(result, cross_border):
    """Return granular authority-to-consult based on classification and market."""
    base = 'State AYUSH licensing authority; CDSCO for potentially applicable new-drug/phytopharmaceutical routes; FSSAI for food routes, as relevant.'
    if result in ('classical', 'proprietary'):
        base = 'State AYUSH licensing authority for manufacturing licence. CDSCO AYUSH Division for any new indication claims.'
    elif result == 'phytopharmaceutical':
        base = 'CDSCO (Phytopharmaceutical Division) for clinical trial and marketing authorisation. AYUSH Ministry for traditional-use evidence.'
    elif result == 'new_drug':
        base = 'CDSCO New Drug Division. Rule 158B pathway for ASU-origin new drugs. Clinical trial registry (CTRI) for trial registration.'
    elif result in ('aahara', 'food'):
        base = 'FSSAI for product approval and licensing. AYUSH Ministry for Ayurveda-Aahara classification confirmation.'
    elif result == 'cosmetic':
        base = 'CDSCO Cosmetics Division. Bureau of Indian Standards (BIS) for quality standards.'

    if cross_border == 'us_fda':
        base += ' For US: FDA CDER (drugs) or FDA CFSAN (supplements). US agent and registered establishment required.'
    elif cross_border == 'eu_ema':
        base += ' For EU: EMA or national competent authority of the member state of entry. HMPC for herbal monograph review.'
    elif cross_border == 'uk_thr':
        base += ' For UK: MHRA Traditional Herbal Registration scheme.'
    elif cross_border == 'multiple_markets':
        base += ' Engage market-specific regulatory consultants for each target jurisdiction.'
    return base


def assess_abs(db,answers,language='en'):
    validate_answers(answers,ABS)
    needed=['origin','entity','purpose','transfer','ip','cultivated','tk',
            'nagoya_scope','benefit_sharing','prior_informed_consent']
    for key in needed:
        if key not in answers:return question_result(ABS[key],language,answers)
    unclear=any(v=='unknown' or v=='unknown_bs' or v=='unknown_pic' for v in answers.values())
    route='review' if unclear else 'nba' if answers['entity']=='foreign' or answers['transfer']=='yes' else 'nba_sbb' if answers['ip']=='yes' else 'sbb' if answers['purpose']!='research' else 'research_review'
    if answers['origin']=='no':route='origin_review'
    # Nagoya non-assessment escalates to full NBA review
    if answers.get('nagoya_scope')=='no' and route not in ('nba','origin_review'):
        route='nba'
    # No benefit-sharing and commercial purpose escalates
    if answers.get('benefit_sharing')=='none_bs' and answers.get('purpose') in ('commercial','both'):
        route='nba' if route!='origin_review' else route
    # PIC not initiated with TK involvement is a compliance gap
    if answers.get('prior_informed_consent')=='pic_not_initiated' and answers.get('tk')=='yes':
        route='nba' if route!='origin_review' else route

    rows,_=retrieve(db,'biological resources access research commercial utilisation patent approval benefit sharing Nagoya Protocol PIC','india',limit=4,category='abs')
    # Only reference the actual retrieved ABS documents.
    rows=[r for r in rows if r[2].category=='abs']
    titles={'en':'ABS assessment: authority and evidence checklist','hi':'ABS मूल्यांकन: प्राधिकरण और साक्ष्य सूची','mr':'ABS मूल्यांकन: प्राधिकरण आणि पुरावा सूची'}

    # ── Build enriched checklist with Nagoya/PIC/benefit-sharing items ──────
    checklist = [
        'Document applicant nationality, residency and ownership/control.',
        'Record biological-resource origin, access dates and procurement evidence.',
        'Identify the relevant state, purpose of access, research transfers and IP stage.',
        'Document associated TK and community involvement.',
        'Check each claimed exemption against current provisions and documentary conditions.',
    ]
    # Nagoya-specific items
    if answers.get('nagoya_scope') == 'no':
        checklist.append(
            'URGENT: Assess Nagoya Protocol obligations — Articles 5 (benefit-sharing), 6 (PIC), '
            'and 15 (compliance). Non-assessment creates legal risk for downstream IP and commercial activities.'
        )
    elif answers.get('nagoya_scope') == 'yes':
        checklist.append(
            'Document the Nagoya Protocol assessment results, including the country-of-origin determination '
            'and any applicable checkpoints under Article 17 (Internationally Recognised Certificate of Compliance).'
        )
    # Benefit-sharing items
    bs = answers.get('benefit_sharing','')
    if bs == 'none_bs':
        checklist.append(
            'Initiate benefit-sharing negotiations with the provider community / State Biodiversity Board. '
            'Section 21 of Biological Diversity Act, 2002 requires equitable benefit-sharing for commercial use.'
        )
    elif bs == 'negotiating':
        checklist.append(
            'Document ongoing benefit-sharing negotiations. Ensure Mutually Agreed Terms (MAT) cover: '
            'monetary/non-monetary benefits, access conditions, third-party transfer restrictions, and dispute resolution.'
        )
    elif bs == 'exempt_bs':
        checklist.append(
            'Provide documentary basis for benefit-sharing exemption. Cultivation exemption under Section 7 '
            'requires proof that resources are from cultivated sources with proper procurement documentation.'
        )
    # PIC items
    pic = answers.get('prior_informed_consent','')
    if pic == 'pic_not_initiated':
        checklist.append(
            'URGENT: Initiate PIC process immediately. For foreign entities, NBA approval under Section 3 '
            'of BD Act is mandatory before access. For Indian entities, SBB intimation under Section 7 is required.'
        )
    elif pic == 'pic_pending':
        checklist.append(
            'Track PIC application status. Typical NBA processing time is 3-6 months. '
            'Do not proceed with commercial activities until PIC is formally granted.'
        )
    elif pic == 'pic_not_required':
        checklist.append(
            'Document the regulatory basis for PIC exemption. Common grounds include: normally traded commodity '
            '(Section 40 notification), cultivated variety with documented origin, or pre-existing access agreement.'
        )

    authority = {
        'nba': 'National Biodiversity Authority (NBA), Chennai. File Form I for access and benefit-sharing.',
        'nba_sbb': 'NBA (for IP/commercial) and relevant State Biodiversity Board (for access intimation). Dual filing may be required.',
        'sbb': 'Relevant State Biodiversity Board. File intimation under Section 7 via SBB portal.',
        'research_review': 'NBA / State Biodiversity Board for route clarification. Academic research may qualify for simplified procedure.',
        'origin_review': 'Origin-country ABS focal point (check CBD ABS Clearing-House) and NBA where relevant for cross-border access.',
        'review': 'NBA / State Biodiversity Board — insufficient clarity on facts requires formal pre-application consultation.',
    }.get(route, 'NBA / State Biodiversity Board')

    limitations = [
        'No automatic exemption, fee calculation, approval or compliance certificate is issued.',
        'Cultivation or traditional use alone does not establish that every ABS obligation is excluded.',
    ]
    if answers.get('nagoya_scope') == 'no':
        limitations.append(
            'Failure to assess Nagoya Protocol obligations may result in patent opposition, '
            'import restrictions, or non-compliance penalties in signatory countries.'
        )
    if answers.get('benefit_sharing') == 'none_bs' and answers.get('purpose') in ('commercial','both'):
        limitations.append(
            'Commercial utilisation without benefit-sharing arrangement is a violation of Section 21 '
            'of the Biological Diversity Act, 2002 and may attract penalties under Section 55.'
        )
    if answers.get('prior_informed_consent') == 'pic_not_initiated' and answers.get('tk') == 'yes':
        limitations.append(
            'Access to TK-associated biological resources without PIC from the community '
            'is a violation of Sections 3/4 of the BD Act and may invalidate downstream IP rights.'
        )

    return {'complete':True,'code':route,'title':titles[language],'provisional':True,'rule_version':RULE_VERSION,
        'citations':[citation(r).model_dump() for r in rows],'missing_facts':[k for k,v in answers.items() if v in ('unknown','unknown_bs','unknown_pic')],
        'authority_to_consult':authority,
        'checklist':checklist,
        'limitations':limitations,
        'disclaimer':DISCLAIMERS[language]}
